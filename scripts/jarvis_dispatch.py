"""GitHub Actions에서 실행되는 Jarvis 명령 처리기.

예약/수동 브리핑, 음성 명령, 승인된 Gmail Draft 생성만 처리한다.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from jarvis_ai import OpenAIClient, redact_external_text
from jarvis_drive import DriveClient, build_markdown
from jarvis_gmail import GmailClient, MailMessage, MESSAGE_ID_RE
from jarvis_memory import MemoryClient, apply_update, empty_memory, match_standards, persona_system_prompt, profile_summary
from jarvis_telegram import TelegramClient, draft_keyboard, masked_sender, verify_draft_callback

KST = timezone(timedelta(hours=9), name="KST")
SUPPORTED_ACTIONS = {
    "briefing", "today_tasks", "jarvis_command", "jarvis_voice_command", "jarvis_create_draft", "jarvis_general_query",
    "jarvis_save_output",
}


def classify_command_text(text: str) -> str | None:
    normalized = re.sub(r"[\s.!?。！？]+", "", text.lower())
    if "최근중요메일브리핑" in normalized or normalized in {"중요메일브리핑", "메일브리핑"}:
        return "briefing"
    if "오늘할일" in normalized:
        return "today_tasks"
    return None


def redact_sensitive(value: Any) -> str:
    return redact_external_text(value, max_length=1200)


def _mail_summary_text(message: MailMessage, summary: dict[str, Any]) -> str:
    received = message.received_at.astimezone(KST).strftime("%m/%d %H:%M")
    reply_needed = "필요" if bool(summary.get("reply_needed")) else "불필요/확인 필요"
    return "\n".join([
        f"발신자: {masked_sender(message.sender)}",
        f"제목: {redact_sensitive(message.subject)}",
        f"수신 시각: {received} KST",
        f"핵심 요청: {redact_sensitive(summary.get('key_request', '확인 필요'))}",
        f"마감일: {redact_sensitive(summary.get('deadline', '없음'))}",
        f"답장 필요: {reply_needed}",
    ])


def run_briefing(gmail: GmailClient, ai: OpenAIClient, telegram: TelegramClient, callback_secret: str) -> None:
    messages = gmail.list_recent(hours=24, max_results=50)
    summaries = ai.summarize_messages(messages)
    sent = 0
    for summary in summaries:
        index = summary.get("index")
        if not isinstance(index, int) or not 0 <= index < len(messages) or not bool(summary.get("important")):
            continue
        message = messages[index]
        markup = draft_keyboard(message.message_id, callback_secret) if bool(summary.get("reply_needed")) else None
        telegram.send_message(_mail_summary_text(message, summary), reply_markup=markup)
        sent += 1
        if sent >= 10:
            break
    if sent == 0:
        telegram.send_message("최근 24시간 내 브리핑할 중요 메일이 없습니다.")


def run_today_tasks(gmail: GmailClient, ai: OpenAIClient, telegram: TelegramClient) -> None:
    messages = gmail.list_recent(hours=24 * 7, max_results=75)
    today = datetime.now(KST).date().isoformat()
    tasks = ai.today_tasks(messages, today)
    if not tasks:
        telegram.send_message("메일에서 확인된 오늘 할 일이 없습니다.")
        return
    lines = [f"오늘 할 일 ({today})"]
    for index, task in enumerate(tasks[:15], start=1):
        lines.append(
            f"{index}. {redact_sensitive(task.get('task', '확인 필요'))}\n"
            f"   마감: {redact_sensitive(task.get('deadline', '확인 필요'))}\n"
            f"   근거: {redact_sensitive(task.get('reason', '메일 요청'))}"
        )
    telegram.send_message("\n\n".join(lines))


def run_voice(
    payload: dict[str, Any],
    gmail: GmailClient,
    ai: OpenAIClient,
    telegram: TelegramClient,
    callback_secret: str,
    memory: MemoryClient | None = None,
) -> None:
    file_id = str(payload.get("voice_file_id", ""))
    if not file_id or len(file_id) > 512:
        raise ValueError("잘못된 Telegram 음성 파일 ID입니다.")
    audio, filename = telegram.download_voice(file_id)
    transcript = ai.transcribe(audio, filename)
    command = classify_command_text(transcript)
    if command == "briefing":
        run_briefing(gmail, ai, telegram, callback_secret)
    elif command == "today_tasks":
        run_today_tasks(gmail, ai, telegram)
    elif transcript.strip():
        telegram.send_message(f"인식한 내용: {transcript.strip()[:300]}")
        run_general_query({"query": transcript}, ai, telegram, memory)
    else:
        telegram.send_message("음성을 인식하지 못했습니다. 다시 말씀해주세요.")


def run_general_query(payload: dict[str, Any], ai: OpenAIClient, telegram: TelegramClient, memory: MemoryClient | None) -> None:
    """자유 질문: 기억 로드 -> 페르소나 답변 -> 학습 추출 -> 기억 저장."""
    query = str(payload.get("query", ""))
    if not query and memory is not None:
        query = memory.take_pending(int(payload.get("telegram_update_id", 0)))
    query = query.strip()[:2000]
    if not query:
        if memory is None:
            telegram.send_message("기억 저장소(JARVIS_WORKER_URL)가 설정되지 않아 질문을 처리하지 못했습니다.")
            return
        raise ValueError("처리할 질문을 찾지 못했습니다.")

    doc = empty_memory()
    if memory is not None:
        try:
            doc = memory.load()
        except Exception:
            print("::warning::Jarvis 기억을 불러오지 못해 기본 페르소나로 답합니다.")

    standards: list[dict[str, Any]] = []
    if memory is not None:
        try:
            standards = match_standards(memory.load_standards(), query)
        except Exception:
            print("::warning::Jarvis 작업 기준을 불러오지 못해 기준 없이 답합니다.")

    answer = ai.answer_general_query(query, persona_system_prompt(doc, standards), doc["turns"])
    if standards:
        answer = f"{answer}\n\n— 기준: {', '.join(s['name'] for s in standards)}"
    telegram.send_message(answer)

    if memory is None:
        return
    try:
        memory.save_last(query, answer)
    except Exception:
        print("::warning::직전 답변 보관에 실패했습니다(저장해줘 기능만 영향).")
    try:
        learning = ai.extract_learning(query, answer, profile_summary(doc))
    except Exception:
        learning = {}
    new_items: list[str] = []

    def mutate(current: dict[str, Any]) -> None:
        before = {k: {i["text"] for i in v} for k, v in current["profile"].items()}
        apply_update(current, query, answer, learning)
        new_items.clear()
        for key, items in current["profile"].items():
            new_items.extend(i["text"] for i in items if i["text"] not in before.get(key, set()))

    try:
        memory.update(mutate)
    except Exception:
        print("::warning::Jarvis 기억 저장에 실패했습니다.")
        return
    if new_items:
        lines = "\n".join(f"- {text}" for text in new_items[:5])
        telegram.send_message(f"새로 기억한 내용:\n{lines}\n\n/memory 로 전체 확인, 틀린 내용은 '기억 수정: ...'으로 알려주세요.")


def run_save_output(payload: dict[str, Any], telegram: TelegramClient, memory: MemoryClient | None, drive: Any = None) -> None:
    """저장해줘: Worker가 고정한 직전 답변을 Google Drive 'Jarvis 저장함'에 md 파일로 만든다."""
    if memory is None:
        telegram.send_message("기억 저장소(JARVIS_WORKER_URL)가 설정되지 않아 저장할 답변을 찾지 못했습니다.")
        return
    save = memory.take_save(int(payload.get("telegram_update_id", 0)))
    if not save or not str(save.get("a", "")).strip():
        telegram.send_message("저장할 답변을 찾지 못했습니다(이미 저장했거나 24시간이 지났습니다). 다시 \"저장해줘\"를 보내주세요.")
        return
    if drive is None:
        try:
            drive = DriveClient()
        except Exception:
            telegram.send_message("Google Drive 저장이 아직 설정되지 않았습니다. README의 'JARVIS_DRIVE_REFRESH_TOKEN' 설정을 확인해주세요.")
            return
    filename, content = build_markdown(save, datetime.now(timezone.utc))
    created = drive.upload_markdown(filename, content)
    link = f"\n{created['link']}" if created.get("link") else ""
    telegram.send_message(f"Google Drive '{drive.folder_name}'에 저장했습니다.\n{created['name']}{link}")


def run_create_draft(
    payload: dict[str, Any],
    gmail: GmailClient,
    ai: OpenAIClient,
    telegram: TelegramClient,
    callback_secret: str,
) -> None:
    approval = str(payload.get("approval", ""))
    message_id, computed_approval_id = verify_draft_callback(approval, callback_secret)
    if str(payload.get("approval_id", "")) != computed_approval_id:
        raise ValueError("답장 승인 식별자가 올바르지 않습니다.")
    if not MESSAGE_ID_RE.fullmatch(message_id):
        raise ValueError("잘못된 Gmail 메시지 ID입니다.")
    original = gmail.get_message(message_id)
    reply_text = ai.create_reply_text(original)
    _, created = gmail.create_reply_draft(original, reply_text, computed_approval_id)
    if created:
        telegram.send_message("Gmail 임시보관함에 답장 초안을 만들었습니다. 내용을 직접 검토한 뒤 Gmail에서 발송해주세요.")
    else:
        telegram.send_message("같은 승인으로 만든 Gmail 답장 초안이 이미 있어 새 초안을 중복 생성하지 않았습니다.")


def run_action(
    action: str,
    payload: dict[str, Any],
    gmail: GmailClient,
    ai: OpenAIClient,
    telegram: TelegramClient,
    callback_secret: str,
    memory: MemoryClient | None = None,
    drive: Any = None,
) -> None:
    if action not in SUPPORTED_ACTIONS:
        raise ValueError("지원하지 않는 Jarvis 작업입니다.")
    if action == "briefing":
        run_briefing(gmail, ai, telegram, callback_secret)
    elif action == "today_tasks":
        run_today_tasks(gmail, ai, telegram)
    elif action == "jarvis_command":
        command = str(payload.get("command", ""))
        if command == "briefing":
            run_briefing(gmail, ai, telegram, callback_secret)
        elif command == "today_tasks":
            run_today_tasks(gmail, ai, telegram)
        else:
            raise ValueError("지원하지 않는 Jarvis 명령입니다.")
    elif action == "jarvis_voice_command":
        run_voice(payload, gmail, ai, telegram, callback_secret, memory)
    elif action == "jarvis_create_draft":
        run_create_draft(payload, gmail, ai, telegram, callback_secret)
    elif action == "jarvis_general_query":
        run_general_query(payload, ai, telegram, memory)
    elif action == "jarvis_save_output":
        run_save_output(payload, telegram, memory, drive)


def _event_from_environment() -> tuple[str, dict[str, Any]]:
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH가 비어 있습니다.")
    with Path(event_path).open(encoding="utf-8") as stream:
        event = json.load(stream)
    return str(event.get("action", "")), event.get("client_payload", {}) or {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("event", "briefing", "today_tasks"), default="event")
    args = parser.parse_args(argv)
    telegram: TelegramClient | None = None
    try:
        callback_secret = os.environ.get("JARVIS_WEBHOOK_SECRET", "")
        if not callback_secret:
            raise RuntimeError("JARVIS_WEBHOOK_SECRET가 비어 있습니다.")
        gmail = GmailClient()
        ai = OpenAIClient()
        telegram = TelegramClient()
        if args.mode == "event":
            action, payload = _event_from_environment()
        else:
            action, payload = args.mode, {}
        memory: MemoryClient | None = None
        if os.environ.get("JARVIS_WORKER_URL"):
            try:
                memory = MemoryClient()
            except Exception:
                print("::warning::JARVIS_WORKER_URL 설정이 올바르지 않아 기억 기능을 끕니다.")
        run_action(action, payload, gmail, ai, telegram, callback_secret, memory)
        print(json.dumps({"ok": True, "action": action}, ensure_ascii=False))
        return 0
    except Exception as err:
        # 공개 저장소라 Actions 로그가 공개된다. 예외 메시지·traceback은 출력하지 않는다.
        print(f"::error::Jarvis 작업 처리에 실패했습니다 ({type(err).__name__}).")
        if telegram is not None:
            try:
                telegram.send_message("Jarvis 작업 처리에 실패했습니다. GitHub Actions 실행 상태를 확인해주세요.")
            except Exception:
                pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
