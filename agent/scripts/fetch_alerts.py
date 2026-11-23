"""Print unread emails from the scout mailbox for the scout run, then file them.

Installed into Hermes' scripts folder by install.sh and attached to the scout job
(cron --script), so its output is injected into the agent's prompt each run.

Reads SCOUT_IMAP_* from Hermes' .env, prints each unread email as plain text, then
labels it "HJA/processed" and archives it, so the inbox only ever holds mail that
has not been looked at. It never sends mail, and the agent never sees the password.
"""
from __future__ import annotations

import email
import re
import sys
from email.header import decode_header, make_header
from email.message import Message
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # hja_mail.py sits next to this script
from hja_mail import archive_processed, connect, load_env, mailbox_settings

MAX_EMAILS = 30
MAX_CHARS = 5000


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
    settings = mailbox_settings(load_env())
    if not settings:
        print("NO_MAILBOX_CONFIGURED")
        return

    box = connect(*settings)
    try:
        box.select("INBOX")
        uids = box.uid("SEARCH", None, "UNSEEN")[1][0].split()[:MAX_EMAILS]
        if not uids:
            print("NO_NEW_ALERTS")
        for uid in uids:
            raw = box.uid("FETCH", uid, "(RFC822)")[1][0][1]  # fetching marks the email read
            msg = email.message_from_bytes(raw)
            subject = str(make_header(decode_header(msg.get("Subject", ""))))
            print(f"=== EMAIL | From: {msg.get('From')} | Subject: {subject}")
            print(body_text(msg)[:MAX_CHARS], "\n")
        archive_processed(box, uids)
    finally:
        box.logout()


if __name__ == "__main__":
    main()
