"""Shared IMAP helpers for the scout mailbox. Standard library only.

There is deliberately no SMTP anywhere in this project: these helpers can read,
label, archive and *append drafts*, but nothing can send mail. Drafts appear in
the mailbox's Drafts folder for the user to review and send themselves.
"""
from __future__ import annotations

import imaplib
import os
import re
import time
from pathlib import Path

HOME = Path(os.environ.get("HERMES_HOME", "/opt/data"))
ENV_PATH = HOME / ".env"
PROCESSED_LABEL = "HJA/processed"

_LIST_RE = re.compile(rb'\((?P<flags>[^)]*)\) (?P<delim>"[^"]*"|NIL) (?P<name>.+)$')


def load_env(path: Path = ENV_PATH) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def mailbox_settings(env: dict[str, str]) -> tuple[str, str, str] | None:
    host, user, password = (env.get(k, "") for k in
                            ("SCOUT_IMAP_HOST", "SCOUT_IMAP_USER", "SCOUT_IMAP_PASSWORD"))
    return (host, user, password) if host and user and password else None


def connect(host: str, user: str, password: str) -> imaplib.IMAP4_SSL:
    box = imaplib.IMAP4_SSL(host)
    box.login(user, password)
    return box


def parse_list_line(line: bytes) -> tuple[list[str], str] | None:
    """Parse one IMAP LIST response line into (flags, mailbox name)."""
    match = _LIST_RE.match(line.strip())
    if not match:
        return None
    flags = match.group("flags").decode(errors="replace").split()
    name = match.group("name").decode(errors="replace").strip()
    if name.startswith('"') and name.endswith('"'):
        name = name[1:-1]
    return flags, name


def special_folder(box: imaplib.IMAP4, flag: str, fallback: str) -> str:
    """Find a special-use folder (RFC 6154), e.g. \\Drafts, whatever its localised name."""
    status, lines = box.list()
    if status == "OK":
        for raw in lines or []:
            parsed = parse_list_line(raw) if isinstance(raw, bytes) else None
            if parsed and flag in parsed[0]:
                return parsed[1]
    return fallback


def quote(name: str) -> str:
    return '"' + name.replace("\\", "\\\\").replace('"', '\\"') + '"'


def is_gmail(box: imaplib.IMAP4) -> bool:
    return "X-GM-EXT-1" in box.capabilities


def archive_processed(box: imaplib.IMAP4, uids: list[bytes]) -> None:
    """Label processed messages and remove them from the inbox (the selected folder)."""
    if not uids:
        return
    uid_set = b",".join(uids).decode()
    if is_gmail(box):
        box.uid("STORE", uid_set, "+X-GM-LABELS", f"({quote(PROCESSED_LABEL)})")
    else:
        box.create(quote(PROCESSED_LABEL))  # fails harmlessly if it already exists
        box.uid("COPY", uid_set, quote(PROCESSED_LABEL))
    # On Gmail, expunging from INBOX archives the message (it stays in All Mail).
    box.uid("STORE", uid_set, "+FLAGS", "(\\Deleted)")
    box.expunge()


def append_draft(box: imaplib.IMAP4, message: bytes) -> str:
    folder = special_folder(box, "\\Drafts", "Drafts")
    status, detail = box.append(quote(folder), "(\\Draft \\Seen)",
                                imaplib.Time2Internaldate(time.time()), message)
    if status != "OK":
        raise imaplib.IMAP4.error(f"APPEND to {folder} failed: {detail}")
    return folder
