import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from jarvis_dispatch import classify_command_text, redact_sensitive, run_action
from jarvis_gmail import MailMessage
from jarvis_telegram import approval_id, make_draft_callback


class FakeGmail:
    def __init__(self):
        self.draft_calls = 0
        self.message = MailMessage(
            message_id="18abc123def45678",
            thread_id="thread-1",
            sender="홍길동 <person@example.com>",
            subject="검토 요청",
            received_at=datetime.now(timezone.utc),
            body="본문",
        )

    def list_recent(self, **kwargs):
        return [self.message]

    def get_message(self, message_id):
        self.requested_id = message_id
        return self.message

    def create_reply_draft(self, original, reply_text, verified_approval_id):
        self.draft_calls += 1
        self.reply_text = reply_text
        self.approval_id = verified_approval_id
        return "draft-1", True


class FakeAI:
    def summarize_messages(self, messages):
        return [{"index": 0, "important": True, "key_request": "검토", "deadline": "금요일", "reply_needed": True}]

    def today_tasks(self, messages, today):
        return [{"task": "자료 검토", "deadline": today, "reason": "메일 요청"}]

    def create_reply_text(self, original):
        return "검토 후 회신드리겠습니다."

    def transcribe(self, audio, filename):
        return "최근 중요 메일 브리핑해줘"


class FakeTelegram:
    def __init__(self):
        self.messages = []

    def send_message(self, text, reply_markup=None):
        self.messages.append((text, reply_markup))

    def download_voice(self, file_id):
        return b"voice", "voice.ogg"


class JarvisDispatchTests(unittest.TestCase):
    def test_text_and_transcribed_voice_use_same_command_classifier(self):
        self.assertEqual(classify_command_text("최근 중요 메일 브리핑해줘"), "briefing")
        self.assertEqual(classify_command_text("오늘 할 일 보여줘!"), "today_tasks")
        self.assertIsNone(classify_command_text("메일을 삭제해줘"))

    def test_briefing_never_creates_draft_without_button_event(self):
        gmail, ai, telegram = FakeGmail(), FakeAI(), FakeTelegram()
        run_action("jarvis_command", {"command": "briefing"}, gmail, ai, telegram, "secret")
        self.assertEqual(gmail.draft_calls, 0)
        self.assertTrue(telegram.messages[0][1]["inline_keyboard"])

    def test_only_signed_button_approval_creates_gmail_draft(self):
        gmail, ai, telegram = FakeGmail(), FakeAI(), FakeTelegram()
        callback = make_draft_callback("18abc123def45678", "secret")
        run_action(
            "jarvis_create_draft",
            {"approval": callback, "approval_id": approval_id(callback)},
            gmail,
            ai,
            telegram,
            "secret",
        )
        self.assertEqual(gmail.draft_calls, 1)
        self.assertEqual(gmail.approval_id, approval_id(callback))
        self.assertIn("임시보관함", telegram.messages[0][0])
        self.assertNotIn("발송했습니다", telegram.messages[0][0])

    def test_direct_dispatch_without_signed_approval_cannot_create_draft(self):
        gmail, ai, telegram = FakeGmail(), FakeAI(), FakeTelegram()
        with self.assertRaises(ValueError):
            run_action(
                "jarvis_create_draft",
                {"message_id": "18abc123def45678"},
                gmail,
                ai,
                telegram,
                "secret",
            )
        self.assertEqual(gmail.draft_calls, 0)

    def test_voice_command_runs_briefing_but_not_draft_creation(self):
        gmail, ai, telegram = FakeGmail(), FakeAI(), FakeTelegram()
        run_action("jarvis_voice_command", {"voice_file_id": "voice-file"}, gmail, ai, telegram, "secret")
        self.assertEqual(gmail.draft_calls, 0)
        self.assertTrue(telegram.messages)

    def test_sensitive_values_are_redacted_before_telegram(self):
        redacted = redact_sensitive("person@example.com / 010-1234-5678 / 900101-1234567")
        self.assertNotIn("person@example.com", redacted)
        self.assertNotIn("010-1234-5678", redacted)
        self.assertNotIn("900101-1234567", redacted)


if __name__ == "__main__":
    unittest.main()
