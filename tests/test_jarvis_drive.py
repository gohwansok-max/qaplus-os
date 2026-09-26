import json
import os
import sys
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.insert(0, os.path.dirname(__file__))

from jarvis_dispatch import run_action
from jarvis_drive import FILES_URL, UPLOAD_URL, DriveClient, build_markdown, safe_filename
from test_jarvis_memory import FakeAI, FakeTelegram, FakeWorker, client

NOW = datetime(2026, 9, 26, 12, 5, tzinfo=timezone.utc)


class FakeResponse:
    def __init__(self, status, data):
        self.status_code = status
        self._data = data

    def json(self):
        return self._data


class FakeDriveSession:
    def __init__(self, folders=None):
        self.folders = list(folders or [])
        self.calls = []

    def post(self, url, data=None, timeout=None):
        assert data["grant_type"] == "refresh_token"
        return FakeResponse(200, {"access_token": "at", "expires_in": 3600})

    def request(self, method, url, headers=None, timeout=None, params=None, json=None, data=None):
        assert headers["Authorization"] == "Bearer at"
        self.calls.append((method, url, params, json, data, headers))
        if method == "GET" and url == FILES_URL:
            return FakeResponse(200, {"files": [{"id": f} for f in self.folders]})
        if method == "POST" and url == FILES_URL:
            self.folders.append("new-folder")
            return FakeResponse(200, {"id": "new-folder"})
        if method == "POST" and url == UPLOAD_URL:
            return FakeResponse(200, {"id": "file-1", "name": "saved.md", "webViewLink": "https://drive.google.com/file/d/file-1/view"})
        return FakeResponse(404, {})


def drive(session):
    return DriveClient("cid", "secret", "refresh", session=session)


class MarkdownTests(unittest.TestCase):
    def test_filename_is_kst_dated_and_sanitized(self):
        self.assertEqual(safe_filename('협찬/거절: "A사"', NOW), "2026-09-26_2105_협찬 거절 A사.md")
        self.assertEqual(safe_filename("   ", NOW), "2026-09-26_2105_Jarvis 답변.md")

    def test_markdown_uses_title_or_question_and_keeps_full_answer(self):
        long_answer = "가" * 5000
        name, body = build_markdown({"q": "C사 협찬 거절 답장 써줘", "a": long_answer, "at": "2026-09-26T11:50:00+00:00", "title": ""}, NOW)
        self.assertTrue(name.endswith("_C사 협찬 거절 답장 써줘.md"))
        self.assertIn("# C사 협찬 거절 답장 써줘", body)
        self.assertIn("- 답변 시각: 2026-09-26 20:50 KST", body)
        self.assertIn(long_answer, body)
        name, body = build_markdown({"q": "q", "a": "a", "title": "주간 보고"}, NOW)
        self.assertIn("# 주간 보고", body)
        self.assertIn("답변 시각: 기록 없음", body)


class DriveClientTests(unittest.TestCase):
    def test_reuses_app_folder_and_uploads_markdown(self):
        session = FakeDriveSession(folders=["folder-1"])
        created = drive(session).upload_markdown("a.md", "# 제목\n본문")
        self.assertEqual(created["link"], "https://drive.google.com/file/d/file-1/view")
        upload = session.calls[-1]
        self.assertEqual(upload[2]["uploadType"], "multipart")
        body = upload[4].decode("utf-8")
        self.assertIn('"parents": ["folder-1"]', body)
        self.assertIn("# 제목\n본문", body)
        self.assertFalse(any(call[0] == "POST" and call[1] == FILES_URL for call in session.calls))

    def test_creates_folder_when_missing(self):
        session = FakeDriveSession()
        drive(session).upload_markdown("a.md", "x")
        folder_create = [c for c in session.calls if c[0] == "POST" and c[1] == FILES_URL][0]
        self.assertEqual(folder_create[3], {"name": "Jarvis 저장함", "mimeType": "application/vnd.google-apps.folder"})

    def test_only_allowlisted_drive_calls_and_required_token(self):
        with self.assertRaises(ValueError):
            drive(FakeDriveSession())._request("DELETE", FILES_URL)
        with self.assertRaises(RuntimeError):
            DriveClient("cid", "secret", "")


class SaveOutputFlowTests(unittest.TestCase):
    def test_general_query_keeps_full_answer_for_saving(self):
        worker = FakeWorker(pending={7: "질문"})
        run_action("jarvis_general_query", {"telegram_update_id": 7}, None, FakeAI(), FakeTelegram(), "secret", client(worker))
        self.assertEqual(worker.last, {"q": "질문", "a": "답변: 질문", "source": "actions"})

    def test_save_uploads_snapshot_and_replies_with_link(self):
        worker = FakeWorker()
        worker.saves_pending[31] = {"q": "보고서 써줘", "a": "결론 먼저", "at": "2026-09-26T11:50:00+00:00", "title": "주간 보고"}
        session = FakeDriveSession(folders=["folder-1"])
        telegram = FakeTelegram()
        run_action("jarvis_save_output", {"telegram_update_id": 31}, None, FakeAI(), telegram, "secret", client(worker), drive(session))
        self.assertIn("'Jarvis 저장함'에 저장했습니다", telegram.messages[0])
        self.assertIn("https://drive.google.com/file/d/file-1/view", telegram.messages[0])
        self.assertIn("# 주간 보고", session.calls[-1][4].decode("utf-8"))
        self.assertEqual(worker.saves_pending, {})

    def test_missing_snapshot_or_drive_setup_is_reported(self):
        telegram = FakeTelegram()
        run_action("jarvis_save_output", {"telegram_update_id": 99}, None, FakeAI(), telegram, "secret", client(FakeWorker()), drive(FakeDriveSession()))
        self.assertIn("저장할 답변을 찾지 못했습니다", telegram.messages[0])

        worker = FakeWorker()
        worker.saves_pending[32] = {"q": "q", "a": "a"}
        os.environ.pop("JARVIS_DRIVE_REFRESH_TOKEN", None)
        telegram = FakeTelegram()
        run_action("jarvis_save_output", {"telegram_update_id": 32}, None, FakeAI(), telegram, "secret", client(worker))
        self.assertIn("Google Drive 저장이 아직 설정되지 않았습니다", telegram.messages[0])


if __name__ == "__main__":
    unittest.main()
