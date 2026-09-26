import base64
import hashlib
import hmac
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from jarvis_telegram import approval_id, make_draft_callback, masked_sender, verify_draft_callback


class JarvisTelegramTests(unittest.TestCase):
    def test_callback_is_short_and_hmac_signed(self):
        callback = make_draft_callback("18abc123def45678", "secret", now=1_700_000_000)
        self.assertLessEqual(len(callback.encode("utf-8")), 64)
        payload, signature = callback.rsplit(":", 1)
        expected = base64.urlsafe_b64encode(hmac.new(b"secret", payload.encode(), hashlib.sha256).digest()[:12]).decode().rstrip("=")
        self.assertEqual(signature, expected)
        message_id, verified_id = verify_draft_callback(callback, "secret", now=1_700_000_000)
        self.assertEqual(message_id, "18abc123def45678")
        self.assertEqual(verified_id, approval_id(callback))

    def test_invalid_or_expired_callback_is_rejected(self):
        callback = make_draft_callback("18abc123def45678", "secret", ttl_seconds=60, now=1_700_000_000)
        with self.assertRaises(ValueError):
            verify_draft_callback(callback, "wrong", now=1_700_000_000)
        with self.assertRaises(ValueError):
            verify_draft_callback(callback, "secret", now=1_700_000_120)

    def test_sender_email_is_masked(self):
        self.assertEqual(masked_sender("person@example.com"), "pe***@example.com")
        self.assertEqual(masked_sender("홍길동 <person@example.com>"), "홍*동")


if __name__ == "__main__":
    unittest.main()
