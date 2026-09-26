import base64
import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from jarvis_gmail import GMAIL_SCOPES, GmailClient, MailMessage


class FakeResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("request failed")

    def json(self):
        return self._data


class FakeSession:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return FakeResponse({"access_token": "token", "expires_in": 3600})


def encoded(value):
    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")


def gmail_message(message_id="18abc123def45678", sender="담당자 <person@example.com>", subject="검토 요청", body="금요일까지 검토 부탁드립니다.", timestamp=None, extra_headers=None):
    timestamp = timestamp or int(datetime.now(timezone.utc).timestamp() * 1000)
    headers = [
        {"name": "From", "value": sender},
        {"name": "Subject", "value": subject},
        {"name": "Message-ID", "value": "<message@example.com>"},
    ] + list(extra_headers or [])
    return {
        "id": message_id,
        "threadId": "thread-1",
        "internalDate": str(timestamp),
        "payload": {"mimeType": "text/plain", "headers": headers, "body": {"data": encoded(body)}},
    }


class JarvisGmailTests(unittest.TestCase):
    def client(self, session):
        client = GmailClient("client", "secret", "refresh", session=session)
        client._access_token = "token"
        client._access_token_expires_at = 10**12
        return client

    def test_minimum_scopes_are_readonly_and_compose_only(self):
        self.assertEqual(
            GMAIL_SCOPES,
            (
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.compose",
            ),
        )

    def test_recent_mail_excludes_newsletters_and_automated_messages(self):
        session = FakeSession([
            FakeResponse({"messages": [{"id": "18abc123def45678"}, {"id": "18abc123def45679"}]}),
            FakeResponse(gmail_message()),
            FakeResponse(gmail_message(
                message_id="18abc123def45679",
                sender="news@example.com",
                subject="주간 뉴스레터",
                extra_headers=[{"name": "List-Unsubscribe", "value": "<https://example.com/out>"}],
            )),
        ])
        messages = self.client(session).list_recent(hours=24)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].subject, "검토 요청")
        self.assertEqual(messages[0].body, "금요일까지 검토 부탁드립니다.")

    def test_reply_creation_calls_drafts_create_and_never_send_endpoint(self):
        session = FakeSession([FakeResponse({"drafts": []}), FakeResponse({"id": "draft-1"})])
        client = self.client(session)
        original = MailMessage(
            message_id="18abc123def45678",
            thread_id="thread-1",
            sender="담당자 <person@example.com>",
            subject="검토 요청",
            received_at=datetime.now(timezone.utc),
            body="본문",
            message_id_header="<message@example.com>",
        )
        self.assertEqual(
            client.create_reply_draft(original, "검토 후 회신드리겠습니다.", "0123456789abcdef01234567"),
            ("draft-1", True),
        )
        self.assertTrue(session.calls[0][1].endswith("/drafts"))
        method, url, kwargs = session.calls[1]
        self.assertEqual(method, "POST")
        self.assertTrue(url.endswith("/drafts"))
        self.assertNotIn("/send", url)
        raw = kwargs["json"]["message"]["raw"]
        decoded = base64.urlsafe_b64decode(raw + "=" * ((4 - len(raw) % 4) % 4)).decode("utf-8")
        self.assertIn("X-Jarvis-Approval-ID: 0123456789abcdef01234567", decoded)

    def test_existing_approval_draft_is_reused(self):
        existing = {
            "id": "draft-existing",
            "message": {"payload": {"headers": [{"name": "X-Jarvis-Approval-ID", "value": "0123456789abcdef01234567"}]}},
        }
        session = FakeSession([
            FakeResponse({"drafts": [{"id": "draft-existing"}]}),
            FakeResponse(existing),
        ])
        client = self.client(session)
        original = MailMessage(
            message_id="18abc123def45678",
            thread_id="thread-1",
            sender="person@example.com",
            subject="검토 요청",
            received_at=datetime.now(timezone.utc),
            body="본문",
        )
        self.assertEqual(
            client.create_reply_draft(original, "초안", "0123456789abcdef01234567"),
            ("draft-existing", False),
        )
        self.assertEqual(len(session.calls), 2)
        self.assertTrue(all(call[0] == "GET" for call in session.calls))

    def test_existing_approval_is_found_on_later_draft_page(self):
        existing = {
            "id": "draft-later",
            "message": {"payload": {"headers": [{"name": "X-Jarvis-Approval-ID", "value": "0123456789abcdef01234567"}]}},
        }
        session = FakeSession([
            FakeResponse({"drafts": [], "nextPageToken": "page-2"}),
            FakeResponse({"drafts": [{"id": "draft-later"}]}),
            FakeResponse(existing),
        ])
        client = self.client(session)
        original = MailMessage(
            message_id="18abc123def45678",
            thread_id="thread-1",
            sender="person@example.com",
            subject="검토 요청",
            received_at=datetime.now(timezone.utc),
            body="본문",
        )
        self.assertEqual(
            client.create_reply_draft(original, "초안", "0123456789abcdef01234567"),
            ("draft-later", False),
        )
        self.assertEqual(session.calls[1][2]["params"]["pageToken"], "page-2")

    def test_non_allowlisted_gmail_operation_is_blocked(self):
        client = self.client(FakeSession())
        self.assertFalse(any(name.startswith("send") for name in dir(client)))
        with self.assertRaises(RuntimeError):
            client._request("POST", "/messages/send", json={})


if __name__ == "__main__":
    unittest.main()
