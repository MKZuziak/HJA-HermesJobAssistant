"""Print unread job-alert emails for the scout run.

Installed into Hermes' scripts folder by install.sh and attached to the scout job
(cron --script), so its output is injected into the agent's prompt each run.

Reads SCOUT_IMAP_* from Hermes' .env, prints each unread email as plain text and
marks it read. It never sends mail, and the agent never sees the mailbox password.
"""
from __future__ import annotations

import email
import imaplib
import os
import re
from email.header import decode_header, make_header
from email.message import Message

ENV_FILE = os.path.join(os.environ.get("HERMES_HOME", "/opt/data"), ".env")
MAX_EMAILS = 30
MAX_CHARS = 5000


def load_env(path: str) -> dict[str, str]:
    env: dict[str, str] = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.strip().split("=", 1)
                env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def body_text(msg: Message) -> str:
    plain, html = "", ""
    for part in msg.walk():
        if part.get_content_maintype() == "multipart" or part.get_filename():
            continue
        payload = part.get_payload(decode=True) or b""
        text = payload.decode(part.get_content_charset() or "utf-8", "replace")
        if part.get_content_type() == "text/plain":
            plain += text
        elif part.get_content_type() == "text/html":
            html += text
    if plain.strip():
        return plain
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    html = re.sub(r'(?i)<a[^>]+href="([^"]+)"[^>]*>', r" [\1] ", html)  # keep link targets
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def main() -> None:
    env = load_env(ENV_FILE)
    host, user, password = (env.get(k, "") for k in
                            ("SCOUT_IMAP_HOST", "SCOUT_IMAP_USER", "SCOUT_IMAP_PASSWORD"))
    if not (host and user and password):
        print("NO_MAILBOX_CONFIGURED")
        return

    box = imaplib.IMAP4_SSL(host)
    try:
        box.login(user, password)
        box.select("INBOX")
        ids = box.search(None, "UNSEEN")[1][0].split()[:MAX_EMAILS]
        if not ids:
            print("NO_NEW_ALERTS")
        for msg_id in ids:
            raw = box.fetch(msg_id, "(RFC822)")[1][0][1]  # fetching marks the email read
            msg = email.message_from_bytes(raw)
            subject = str(make_header(decode_header(msg.get("Subject", ""))))
            print(f"=== ALERT EMAIL | From: {msg.get('From')} | Subject: {subject}")
            print(body_text(msg)[:MAX_CHARS], "\n")
    finally:
        box.logout()


if __name__ == "__main__":
    main()
