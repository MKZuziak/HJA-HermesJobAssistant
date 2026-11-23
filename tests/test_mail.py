"""Offline tests for the drafts-only mailbox helpers (no network, no IMAP server)."""
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "agent" / "scripts"
TMP = tempfile.TemporaryDirectory()
os.environ["HERMES_HOME"] = TMP.name  # module-level paths resolve against this
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hja_mail = load("hja_mail")
mail_sync = load("mail_sync")

HOME = Path(TMP.name)
(HOME / "materials" / "cv").mkdir(parents=True)
(HOME / "materials" / "cv" / "CV.pdf").write_bytes(b"%PDF-1.4 test")
(HOME / "scout" / "drafts" / "ucl-postdoc").mkdir(parents=True)
(HOME / "scout" / "drafts" / "ucl-postdoc" / "cover_letter.md").write_text("Dear committee")
(HOME / ".env").write_text("SECRET=1\n")

VALID = """To: Hiring Committee <jobs@example.org>
Subject: Application: Postdoc in privacy
Attach: cv/CV.pdf, drafts/ucl-postdoc/cover_letter.md
---
Dear committee,

Please find my application attached.
"""


class ParseTests(unittest.TestCase):
    def test_valid(self):
        headers, body = mail_sync.parse_outbox(VALID)
        self.assertEqual(headers["subject"], "Application: Postdoc in privacy")
        self.assertTrue(body.startswith("Dear committee"))

    def test_requires_separator_and_fields(self):
        with self.assertRaises(mail_sync.DraftError):
            mail_sync.parse_outbox("To: a@b.org\nSubject: x\nno separator")
        with self.assertRaises(mail_sync.DraftError):
            mail_sync.parse_outbox("Subject: x\n---\nbody")

    def test_rejects_unknown_headers_and_bad_addresses(self):
        with self.assertRaises(mail_sync.DraftError):
            mail_sync.parse_outbox("To: a@b.org\nSubject: x\nBcc: c@d.org\n---\nbody")
        with self.assertRaises(mail_sync.DraftError):
            mail_sync.parse_outbox("To: not-an-address\nSubject: x\n---\nbody")


class AttachmentTests(unittest.TestCase):
    def test_allowed_roots(self):
        self.assertTrue(mail_sync.resolve_attachment("cv/CV.pdf").is_file())
        self.assertTrue(mail_sync.resolve_attachment("drafts/ucl-postdoc/cover_letter.md").is_file())

    def test_traversal_refused(self):
        for spec in ("../.env", "drafts/../../.env", "/opt/data/.env", "materials/../.env"):
            with self.assertRaises(mail_sync.DraftError, msg=spec):
                mail_sync.resolve_attachment(spec)

    def test_build_message_has_attachments_and_no_bcc(self):
        headers, body = mail_sync.parse_outbox(VALID)
        msg = mail_sync.build_message(headers, body, "scout@example.com")
        names = [p.get_filename() for p in msg.iter_attachments()]
        self.assertEqual(names, ["CV.pdf", "cover_letter.md"])
        self.assertIsNone(msg["Bcc"])
        self.assertEqual(msg["From"], "scout@example.com")


class ImapHelperTests(unittest.TestCase):
    def test_parse_list_line_localised_drafts(self):
        flags, name = hja_mail.parse_list_line(b'(\\HasNoChildren \\Drafts) "/" "[Gmail]/Bozze"')
        self.assertIn("\\Drafts", flags)
        self.assertEqual(name, "[Gmail]/Bozze")

    def test_mailbox_settings_requires_all(self):
        self.assertIsNone(hja_mail.mailbox_settings({"SCOUT_IMAP_HOST": "imap.gmail.com"}))
        self.assertEqual(
            hja_mail.mailbox_settings({"SCOUT_IMAP_HOST": "h", "SCOUT_IMAP_USER": "u", "SCOUT_IMAP_PASSWORD": "p"}),
            ("h", "u", "p"))

    def test_no_smtp_anywhere(self):
        for script in SCRIPTS.glob("*.py"):
            self.assertNotIn("smtplib", script.read_text(), msg=script.name)


if __name__ == "__main__":
    unittest.main()
