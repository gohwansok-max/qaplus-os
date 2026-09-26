import copy
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from jarvis_ai import OpenAIClient, UNTRUSTED_EMAIL_NOTICE, UNTRUSTED_MEMORY_NOTICE
from jarvis_dispatch import run_action
from jarvis_memory import (
    MAX_ITEMS_PER_SECTION,
    MemoryClient,
    add_items,
    empty_memory,
    memory_token,
    match_standards,
    merge_learning,
    normalize_memory,
    persona_system_prompt,
)

SECRET = "test_secret"


class FakeResponse:
    def __init__(self, status, data=None):
        self.status_code = status
        self.data = data or {}

    def json(self):
        return self.data


class FakeWorker:
    """Worker /memory API를 흉내 낸다. 인증 헤더와 rev 충돌을 실제처럼 검사한다."""

    def __init__(self, doc=None, pending=None, conflicts=0, fail_load=False, standards=None):
        self.doc = doc or empty_memory()
        self.standards = standards if standards is not None else []
        self.pending = dict(pending or {})
        self.conflicts = conflicts
        self.fail_load = fail_load
        self.saves = 0

    def request(self, method, url, headers=None, json=None, timeout=None):
        if headers.get("Authorization") != f"Bearer {memory_token(SECRET)}":
            return FakeResponse(403)
        path = url.split("workers.dev", 1)[1]
        if path == "/memory" and method == "GET":
            if self.fail_load:
                return FakeResponse(503)
            return FakeResponse(200, {"doc": copy.deepcopy(self.doc)})
        if path == "/memory" and method == "PUT":
            if self.conflicts > 0:
                self.conflicts -= 1
                self.doc["rev"] += 1  # 다른 실행이 먼저 저장한 상황
                return FakeResponse(409)
            if json["expected_rev"] != self.doc["rev"]:
                return FakeResponse(409)
            self.doc = copy.deepcopy(json["doc"])
            self.doc["rev"] = json["expected_rev"] + 1
            self.saves += 1
            return FakeResponse(200, {"rev": self.doc["rev"]})
        if path == "/memory/standards" and method == "GET":
            if self.fail_load:
                return FakeResponse(503)
            return FakeResponse(200, {"standards": copy.deepcopy(self.standards)})
        if path == "/memory/pending/take":
            text = self.pending.pop(json["update_id"], None)
            return FakeResponse(200, {"text": text}) if text else FakeResponse(404)
        return FakeResponse(404)


def client(worker):
    return MemoryClient("https://jarvis.example.workers.dev", SECRET, session=worker)


class FakeTelegram:
    def __init__(self):
        self.messages = []

    def send_message(self, text, reply_markup=None):
        self.messages.append(text)


class FakeAI:
    def __init__(self, learning=None, fail_learning=False):
        self.learning = learning if learning is not None else {}
        self.fail_learning = fail_learning
        self.system_prompts = []
        self.turns = []

    def answer_general_query(self, query, system_prompt, turns):
        self.system_prompts.append(system_prompt)
        self.turns.append(turns)
        return f"답변: {query}"

    def extract_learning(self, query, answer, known_profile):
        if self.fail_learning:
            raise RuntimeError("boom")
        return self.learning


class MemoryModelTests(unittest.TestCase):
    def test_same_fact_increments_count_instead_of_duplicating(self):
        doc = empty_memory()
        self.assertEqual(add_items(doc, "preferences", ["결론부터 말해주기"]), 1)
        self.assertEqual(add_items(doc, "preferences", ["결론부터  말해주기."]), 0)
        self.assertEqual(len(doc["profile"]["preferences"]), 1)
        self.assertEqual(doc["profile"]["preferences"][0]["count"], 2)

    def test_unknown_sections_and_junk_are_ignored(self):
        doc = empty_memory()
        added = merge_learning(doc, {"updates": {"hacker": ["x"], "skills": ["블로그 초안 작성", 3, ""]}})
        self.assertEqual(added, 1)
        self.assertNotIn("hacker", doc["profile"])
        self.assertEqual(normalize_memory({"profile": {"facts": ["plain", {"text": ""}]}})["profile"]["facts"], [])

    def test_section_is_capped_but_pinned_notes_survive(self):
        doc = empty_memory()
        add_items(doc, "facts", ["직접 기억시킨 중요 사실"], pinned=True)
        add_items(doc, "facts", [f"학습 항목 {i}" for i in range(MAX_ITEMS_PER_SECTION + 10)])
        texts = [item["text"] for item in doc["profile"]["facts"]]
        self.assertIn("직접 기억시킨 중요 사실", texts)
        self.assertEqual(len(texts), MAX_ITEMS_PER_SECTION + 1)

    def test_persona_prompt_reflects_learned_profile_and_limits(self):
        doc = empty_memory()
        add_items(doc, "qa_expertise", ["식품 품질관리 20년차, HACCP·FSSC 22000 실무"])
        add_items(doc, "tone_manner", ["짧은 지시형 문장을 씀"])
        prompt = persona_system_prompt(doc)
        self.assertIn("식품 품질관리 20년차", prompt)
        self.assertIn("짧은 지시형 문장", prompt)
        self.assertIn("한 것처럼 말하지 않는다", prompt)


class GeneralQueryLearningTests(unittest.TestCase):
    def run_query(self, worker, ai, update_id=7):
        telegram = FakeTelegram()
        run_action("jarvis_general_query", {"telegram_update_id": update_id}, None, ai, telegram, "secret", client(worker))
        return telegram

    def test_answers_with_persona_learns_and_reports_new_memory(self):
        doc = empty_memory()
        add_items(doc, "identity", ["식품 품질관리 팀장"])
        worker = FakeWorker(doc=doc, pending={7: "HACCP 내부심사 체크리스트 만들어줘. 표로 줘"})
        ai = FakeAI(learning={"updates": {"preferences": ["체크리스트는 표 형식 선호"], "skills": ["HACCP 내부심사 준비"]}})

        telegram = self.run_query(worker, ai)

        self.assertIn("식품 품질관리 팀장", ai.system_prompts[0])
        self.assertEqual(telegram.messages[0], "답변: HACCP 내부심사 체크리스트 만들어줘. 표로 줘")
        self.assertIn("체크리스트는 표 형식 선호", telegram.messages[1])
        saved = worker.doc
        self.assertEqual(saved["stats"]["conversations"], 1)
        self.assertEqual(saved["turns"][-1]["q"], "HACCP 내부심사 체크리스트 만들어줘. 표로 줘")
        self.assertEqual(saved["profile"]["skills"][0]["text"], "HACCP 내부심사 준비")
        self.assertEqual(worker.pending, {})

    def test_next_conversation_receives_previous_turns(self):
        worker = FakeWorker(pending={1: "첫 질문", 2: "두 번째 질문"})
        ai = FakeAI()
        self.run_query(worker, ai, update_id=1)
        self.run_query(worker, ai, update_id=2)
        self.assertEqual(ai.turns[1][-1]["q"], "첫 질문")

    def test_save_conflict_is_retried_without_losing_learning(self):
        worker = FakeWorker(pending={7: "질문"}, conflicts=1)
        ai = FakeAI(learning={"updates": {"direction": ["AI 네이티브 품질관리 체계 구축"]}})
        self.run_query(worker, ai)
        self.assertEqual(worker.saves, 1)
        self.assertEqual(worker.doc["profile"]["direction"][0]["text"], "AI 네이티브 품질관리 체계 구축")

    def test_memory_outage_still_answers(self):
        worker = FakeWorker(pending={7: "질문"}, fail_load=True)
        telegram = self.run_query(worker, FakeAI(fail_learning=True))
        self.assertEqual(telegram.messages, ["답변: 질문"])

    def test_nothing_new_learned_sends_only_answer(self):
        worker = FakeWorker(pending={7: "안녕"})
        telegram = self.run_query(worker, FakeAI(learning={"updates": {}}))
        self.assertEqual(telegram.messages, ["답변: 안녕"])
        self.assertEqual(worker.doc["stats"]["conversations"], 1)

    def test_voice_question_goes_through_same_learning_loop(self):
        worker = FakeWorker()
        ai = FakeAI(learning={"updates": {"skills": ["음성으로 업무 지시"]}})
        ai.transcribe = lambda audio, filename: "내일 감사 준비물 알려줘"
        telegram = FakeTelegram()
        telegram.download_voice = lambda file_id: (b"ogg", "voice.ogg")
        run_action("jarvis_voice_command", {"voice_file_id": "voice-1"}, None, ai, telegram, "secret", client(worker))
        self.assertEqual(telegram.messages[0], "인식한 내용: 내일 감사 준비물 알려줘")
        self.assertEqual(telegram.messages[1], "답변: 내일 감사 준비물 알려줘")
        self.assertEqual(worker.doc["profile"]["skills"][0]["text"], "음성으로 업무 지시")

    def test_wrong_secret_cannot_read_memory(self):
        worker = FakeWorker()
        bad = MemoryClient("https://jarvis.example.workers.dev", "other_secret", session=worker)
        with self.assertRaises(RuntimeError):
            bad.load()

    def test_worker_url_must_be_https(self):
        with self.assertRaises(RuntimeError):
            MemoryClient("http://jarvis.example.workers.dev", SECRET)


SPONSOR = {"name": "협찬 거절", "body": "감사 인사 → 어려운 이유 → 다음 기회. 세 문장.", "updated": "2026-09-26"}
REPORT = {"name": "보고서", "body": "결론 → 근거 3개 → 액션", "updated": "2026-09-26"}


class StandardsTests(unittest.TestCase):
    def test_matches_name_ignoring_spaces_or_hash_and_caps_at_two(self):
        extra = {"name": "협찬", "body": "짧게", "updated": ""}
        self.assertEqual(match_standards([SPONSOR, REPORT], "A사 협찬제안 왔어. 협찬거절로 답장 써줘")[0]["name"], "협찬 거절")
        self.assertEqual(match_standards([SPONSOR], "#협찬거절 B사 건")[0]["name"], "협찬 거절")
        self.assertEqual(match_standards([SPONSOR, REPORT], "오늘 날씨 어때"), [])
        names = [s["name"] for s in match_standards([extra, SPONSOR, REPORT], "협찬 거절 보고서 같이")]
        self.assertEqual(names, ["협찬 거절", "보고서"])
        self.assertEqual(match_standards(["junk", {"name": 1}, None], "협찬"), [])

    def test_prompt_includes_only_matched_standard_body(self):
        prompt = persona_system_prompt(empty_memory(), [SPONSOR])
        self.assertIn("반드시 적용", prompt)
        self.assertIn("감사 인사 → 어려운 이유 → 다음 기회", prompt)
        self.assertNotIn("반드시 적용", persona_system_prompt(empty_memory()))

    def test_general_query_applies_matched_standard_and_notes_it(self):
        worker = FakeWorker(pending={7: "C사 협찬 거절 답장 써줘"}, standards=[SPONSOR, REPORT])
        ai = FakeAI()
        telegram = FakeTelegram()
        run_action("jarvis_general_query", {"telegram_update_id": 7}, None, ai, telegram, "secret", client(worker))
        self.assertIn("세 문장", ai.system_prompts[0])
        self.assertNotIn("근거 3개", ai.system_prompts[0])
        self.assertEqual(telegram.messages[0], "답변: C사 협찬 거절 답장 써줘\n\n— 기준: 협찬 거절")


class OpenAIPersonaTests(unittest.TestCase):
    def make(self, content):
        calls = []

        class Session:
            def post(self, url, **kwargs):
                calls.append((url, kwargs))

                class R:
                    def raise_for_status(self):
                        return None

                    def json(self):
                        return {"choices": [{"message": {"content": content}}]}
                return R()

        os.environ.setdefault("OPENAI_API_KEY", "test-key")
        return OpenAIClient(session=Session()), calls

    def test_answer_uses_persona_history_and_hides_secrets(self):
        ai, calls = self.make("결론: 가능합니다.")
        answer = ai.answer_general_query(
            "이 키 sk-abcdefghijklmnop123 로 연결 방법 알려줘", "PERSONA", [{"q": "이전 질문", "a": "이전 답"}],
        )
        self.assertEqual(answer, "결론: 가능합니다.")
        messages = calls[0][1]["json"]["messages"]
        self.assertEqual(messages[0], {"role": "system", "content": "PERSONA"})
        self.assertEqual(messages[1]["content"], "이전 질문")
        self.assertNotIn("sk-abcdefghijklmnop123", json.dumps(messages, ensure_ascii=False))

    def test_answer_markdown_is_cleaned_for_telegram(self):
        ai, _ = self.make("## 결론\n**핵심** 항목\n* 둘째")
        self.assertEqual(ai.answer_general_query("q", "S"), "결론\n핵심 항목\n- 둘째")

    def test_learning_extraction_uses_memory_notice_not_email_notice(self):
        ai, calls = self.make('{"updates": {"tone_manner": ["짧은 지시형"]}}')
        result = ai.extract_learning("표로 줘", "네", "")
        self.assertEqual(result["updates"]["tone_manner"], ["짧은 지시형"])
        system = calls[0][1]["json"]["messages"][0]["content"]
        self.assertIn(UNTRUSTED_MEMORY_NOTICE, system)
        self.assertNotIn(UNTRUSTED_EMAIL_NOTICE, system)


if __name__ == "__main__":
    unittest.main()
