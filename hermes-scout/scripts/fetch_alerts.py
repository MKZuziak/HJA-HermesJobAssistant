"""Collect unread job-alert emails over IMAP and print them for the scout run.

Runs inside the container before each scout run (cron --script). Reads the
SCOUT_IMAP_* values from /opt/data/.env, prints each unread email as plain
text, and marks it as read. It never sends mail. The agent itself never gets
the mailbox password.
"""
import email
import imaplib
import re
from email.header import decode_header, make_header

ENV_FILE = "/opt/data/.env"
MAX_EMAILS = 30
MAX_CHARS = 5000


def load_env(path):
    env = {}
    for line in open(path, encoding="utf-8"):
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.strip().split("=", 1)
            env[key] = value.strip().strip('"').strip("'")
    return env


def body_text(msg):
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
    html = re.sub(r'(?i)<a[^>]+href="([^"]+)"[^>]*>', r" [\1] ", html)  # keep links
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def main():
    env = load_env(ENV_FILE)
    if not env.get("SCOUT_IMAP_HOST"):
        print("NO_MAILBOX_CONFIGURED")
        return
    box = imaplib.IMAP4_SSL(env["SCOUT_IMAP_HOST"])
    box.login(env["SCOUT_IMAP_USER"], env["SCOUT_IMAP_PASSWORD"])
    box.select("INBOX")
    ids = box.search(None, "UNSEEN")[1][0].split()[:MAX_EMAILS]
    if not ids:
        print("NO_NEW_ALERTS")
    for i in ids:
        msg = email.message_from_bytes(box.fetch(i, "(RFC822)")[1][0][1])  # marks as read
        subject = str(make_header(decode_header(msg.get("Subject", ""))))
        print(f"=== ALERT EMAIL | From: {msg.get('From')} | Subject: {subject}")
        print(body_text(msg)[:MAX_CHARS], "\n")
    box.logout()


if __name__ == "__main__":
    main()
