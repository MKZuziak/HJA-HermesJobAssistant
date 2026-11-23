"""Turn outbox files written by the agent into drafts in the scout mailbox.

Runs as a script-only (no-agent) cron job every few minutes. For each
/opt/data/scout/outbox/*.md it builds an email and appends it to the mailbox's
Drafts folder over IMAP, then moves the file to outbox/done/. Nothing is ever
sent: the user reviews and sends drafts from their mail client.

Outbox file format (headers, a line with ---, then the plain-text body):

    To: someone@example.org
    Cc: other@example.org            (optional)
    Subject: Application: Postdoc in ...
    Attach: cv/My_CV.pdf, drafts/slug/cover_letter.pdf   (optional)
    ---
    Dear ...

Attachments may only come from the read-only materials folder or the drafts
folder; anything else is refused. Prints a summary only when drafts were created
(empty output = silent run).
"""
from __future__ import annotations

import mimetypes
import re
import sys
from email.message import EmailMessage
from email.utils import formataddr, getaddresses, make_msgid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # hja_mail.py sits next to this script
from hja_mail import HOME, append_draft, connect, load_env, mailbox_settings

OUTBOX = HOME / "scout" / "outbox"
DONE = OUTBOX / "done"
ATTACH_ROOTS = {"materials": HOME / "materials", "drafts": HOME / "scout" / "drafts"}
MAX_ATTACHMENT_BYTES = 15 * 1024 * 1024
ALLOWED_HEADERS = {"to", "cc", "subject", "attach", "in-reply-to"}
EMAIL_RE = re.compile(r"^[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+$")


class DraftError(ValueError):
    """An outbox file that can't be turned into a draft."""


def parse_outbox(text: str) -> tuple[dict[str, str], str]:
    head, sep, body = text.partition("\n---\n")
    if not sep:
        raise DraftError("missing the '---' line between headers and body")
    headers: dict[str, str] = {}
    for line in head.strip().splitlines():
        if ":" not in line:
            raise DraftError(f"bad header line: {line!r}")
        key, value = (part.strip() for part in line.split(":", 1))
        if key.lower() not in ALLOWED_HEADERS:
            raise DraftError(f"unsupported header: {key}")
        headers[key.lower()] = value
    if not headers.get("to") or not headers.get("subject"):
        raise DraftError("To and Subject are required")
    for field in ("to", "cc"):
        for _, addr in getaddresses([headers.get(field, "")]):
            if addr and not EMAIL_RE.match(addr):
                raise DraftError(f"invalid address in {field}: {addr}")
    return headers, body.strip() + "\n"


def resolve_attachment(spec: str) -> Path:
    """Map 'cv/x.pdf' (materials) or 'drafts/slug/x.pdf' to a real file inside an allowed root."""
    spec = spec.strip().lstrip("/")
    first, _, rest = spec.partition("/")
    if first in ATTACH_ROOTS:
        root, relative = ATTACH_ROOTS[first], rest
    else:  # a bare path like cv/My_CV.pdf is relative to materials
        root, relative = ATTACH_ROOTS["materials"], spec
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise DraftError(f"attachment not found or not allowed: {spec}")
    if path.stat().st_size > MAX_ATTACHMENT_BYTES:
        raise DraftError(f"attachment too large: {spec}")
    return path


def build_message(headers: dict[str, str], body: str, sender: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = formataddr(("", sender))
    msg["To"] = headers["to"]
    if headers.get("cc"):
        msg["Cc"] = headers["cc"]
    msg["Subject"] = headers["subject"]
    if headers.get("in-reply-to"):
        msg["In-Reply-To"] = headers["in-reply-to"]
        msg["References"] = headers["in-reply-to"]
    msg["Message-ID"] = make_msgid(domain=sender.split("@")[-1])
    msg.set_content(body)
    for spec in filter(None, (s.strip() for s in headers.get("attach", "").split(","))):
        path = resolve_attachment(spec)
        ctype, _ = mimetypes.guess_type(path.name)
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        msg.add_attachment(path.read_bytes(), maintype=maintype, subtype=subtype, filename=path.name)
    return msg


def main() -> int:
    files = sorted(OUTBOX.glob("*.md")) if OUTBOX.exists() else []
    if not files:
        return 0  # silent tick
    settings = mailbox_settings(load_env())
    if not settings:
        print("Outbox has drafts, but no mailbox is configured (SCOUT_IMAP_* in secrets.env).")
        return 0

    created, failed = [], []
    box = connect(*settings)
    try:
        DONE.mkdir(parents=True, exist_ok=True)
        for path in files:
            try:
                headers, body = parse_outbox(path.read_text(encoding="utf-8"))
                msg = build_message(headers, body, settings[1])
                folder = append_draft(box, msg.as_bytes())
                path.rename(DONE / path.name)
                created.append(f"- {headers['subject']} → {headers['to']}")
            except DraftError as err:
                failed.append(f"- {path.name}: {err}")
    finally:
        box.logout()

    if created:
        print(f"📝 {len(created)} new draft(s) in {folder}, ready for your review:")
        print("\n".join(created))
    if failed:
        print("⚠️ Not turned into drafts (fix the file in the outbox):")
        print("\n".join(failed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
