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
from jarvis_gmail import GmailClient, MailMessage, MESSAGE_ID_RE
from jarvis_telegram import TelegramClient, draft_keyboard, masked_sender, verify_draft_callback

KST = timezone(timedelta(hours=9), name="KST")
SUPPORTED_ACTIONS = {"briefing", "today_tasks", "jarvis_command", "jarvis_voice_command", "jarvis_create_draft"}


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


def run_voice(payload: dict[str, Any], gmail: GmailClient, ai: OpenAIClient, telegram: TelegramClient, callback_secret: str) -> None:
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
    else:
        telegram.send_message("음성에서 지원 명령을 확인하지 못했습니다. '최근 중요 메일 브리핑해줘' 또는 '오늘 할 일 보여줘'라고 말해주세요.")


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
        run_voice(payload, gmail, ai, telegram, callback_secret)
    elif action == "jarvis_create_draft":
        run_create_draft(payload, gmail, ai, telegram, callback_secret)


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
        run_action(action, payload, gmail, ai, telegram, callback_secret)
        print(json.dumps({"ok": True, "action": action}, ensure_ascii=False))
        return 0
    except Exception as err:
        import traceback
        traceback.print_exc()
        print(f"::error::Jarvis 작업 처리에 실패했습니다: {err}")
        if telegram is not None:
            try:
                telegram.send_message("Jarvis 작업 처리에 실패했습니다. GitHub Actions 실행 상태를 확인해주세요.")
            except Exception:
                pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
