# -*- coding: utf-8 -*-
"""
큐에이플러스(QA+) 텔레그램 명령 수신기 — GitHub Actions 전용 (상주 프로세스 불필요)

기존 telegram_bot_service.py 는 무한 while 루프로 도는 상주형이라
PC가 꺼져 있으면 /make 명령을 아무도 듣지 못했습니다.
이 스크립트는 Actions에서 5분마다 1회만 실행되어 밀린 명령을 모아 처리합니다.

동작:
  1. getUpdates 로 밀린 메시지를 한 번에 읽는다
  2. /make [주제] · /daily · /help 를 파싱한다
  3. offset 을 확정(confirm)해 같은 명령이 다음 실행에서 또 처리되지 않게 한다
  4. repository_dispatch(generate_video) 로 렌더링 워크플로를 깨운다

필요 환경변수:
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
  QA_DISPATCH_TOKEN  — repository_dispatch 용 PAT (Contents: write)
                       기본 GITHUB_TOKEN 으로 보낸 이벤트는 다른 워크플로를
                       트리거하지 않는 것이 GitHub 정책이므로 PAT가 반드시 필요합니다.
  GITHUB_REPOSITORY  — Actions가 자동 주입 (owner/repo)
"""

import os
import sys
import json
import requests

MAX_JOBS_PER_RUN = 3  # 한 번에 트리거할 최대 건수 (폭주 방지)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = str(os.environ.get("TELEGRAM_CHAT_ID", "")).strip()
DISPATCH_TOKEN = os.environ.get("QA_DISPATCH_TOKEN", "").strip()
REPO = os.environ.get("GITHUB_REPOSITORY", "").strip()

API = f"https://api.telegram.org/bot{BOT_TOKEN}"

HELP_TEXT = (
    "👋 <b>큐에이플러스 AI 영상 제작 봇</b>\n\n"
    "• <code>/make [주제]</code> : 원하는 주제로 쇼츠 영상 제작\n"
    "• <code>/daily</code> : 30일 큐에서 다음 주제로 제작\n\n"
    "💡 <b>예시</b>\n"
    "<code>/make 선행요건기준 8가지에 대한 목차 간략 설명</code>\n"
    "<code>/make CCP 금속검출기 테스트피스 주기</code>\n\n"
    "⏱ 명령은 5분 주기로 수거됩니다. 접수 메시지가 오면 정상입니다."
)


def reply(text):
    if not BOT_TOKEN or not CHAT_ID:
        return
    try:
        requests.post(
            f"{API}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=15,
        )
    except Exception as exc:
        print(f"[!] 텔레그램 회신 실패: {exc}")


def fetch_updates():
    """밀린 메시지를 읽어 (명령목록, 마지막 update_id) 를 돌려준다."""
    url = f"{API}/getUpdates"
    res = requests.get(
        url,
        params={"timeout": 0, "limit": 100, "allowed_updates": json.dumps(["message"])},
        timeout=30,
    )
    if res.status_code == 409:
        # 웹훅이 걸려 있으면 getUpdates 를 쓸 수 없다.
        print("[!] 409 Conflict — 이 봇에 웹훅이 설정되어 있어 폴링이 불가능합니다.")
        print("    해제: https://api.telegram.org/bot<TOKEN>/deleteWebhook")
        sys.exit(1)
    res.raise_for_status()

    updates = res.json().get("result", [])
    if not updates:
        return [], None

    last_id = updates[-1]["update_id"]
    commands = []
    for upd in updates:
        msg = upd.get("message") or {}
        text = (msg.get("text") or "").strip()
        chat = str((msg.get("chat") or {}).get("id", ""))
        if not text:
            continue
        if CHAT_ID and chat != CHAT_ID:
            print(f"  [무시] 허용되지 않은 chat_id: {chat}")
            continue
        commands.append(text)
    return commands, last_id


def confirm_offset(last_id):
    """offset 을 확정하면 텔레그램 서버가 처리 완료된 메시지를 폐기한다."""
    try:
        requests.get(
            f"{API}/getUpdates",
            params={"offset": last_id + 1, "limit": 1, "timeout": 0},
            timeout=20,
        )
        print(f"  ✓ offset 확정 완료 (update_id {last_id} 까지 소비)")
    except Exception as exc:
        print(f"[!] offset 확정 실패 — 다음 실행에서 중복 처리될 수 있습니다: {exc}")


def dispatch(topic):
    """렌더링 워크플로를 repository_dispatch 로 깨운다."""
    payload = {"event_type": "generate_video", "client_payload": {}}
    if topic:
        payload["client_payload"]["topic"] = topic

    res = requests.post(
        f"https://api.github.com/repos/{REPO}/dispatches",
        headers={
            "Authorization": f"Bearer {DISPATCH_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json=payload,
        timeout=20,
    )
    if res.status_code == 204:
        return True, ""
    return False, f"{res.status_code} {res.text[:200]}"


def parse(text):
    """텍스트 한 줄을 (종류, 주제) 로 해석한다."""
    low = text.lower()
    if low in ("/start", "/help", "도움말"):
        return "help", None
    if low in ("/daily", "오늘영상", "오늘"):
        return "queue", None
    if text.startswith("/make") or text.startswith("만들어줘"):
        topic = text
        for prefix in ("/make@", "/make", "만들어줘:", "만들어줘"):
            if topic.startswith(prefix):
                topic = topic[len(prefix):]
                break
        topic = topic.strip().strip("[]'\"").strip()
        return ("make", topic) if topic else ("make_empty", None)
    return None, None


def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("[!] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID Secret 이 비어 있습니다.")
        sys.exit(1)

    commands, last_id = fetch_updates()
    if not commands:
        print("새 명령 없음.")
        if last_id is not None:
            confirm_offset(last_id)
        return

    print(f"수신한 메시지 {len(commands)}건")

    jobs = []       # (주제 or None) 목록
    send_help = False
    for text in commands:
        kind, topic = parse(text)
        print(f"  [해석] {text[:40]!r} -> {kind}")
        if kind == "help" or kind == "make_empty":
            send_help = True
        elif kind == "make":
            jobs.append(topic)
        elif kind == "queue":
            jobs.append(None)

    # 명령을 해석한 뒤 곧바로 확정한다. (중복 렌더링이 유실보다 더 아프다)
    confirm_offset(last_id)

    if send_help:
        reply(HELP_TEXT)

    if not jobs:
        return

    if not DISPATCH_TOKEN or not REPO:
        reply(
            "⚠️ <b>[설정 필요]</b>\n명령은 받았지만 렌더링을 시작할 수 없습니다.\n"
            "레포 Secret 에 <code>QA_DISPATCH_TOKEN</code>(PAT, Contents 쓰기 권한)을 등록해 주세요."
        )
        print("[!] QA_DISPATCH_TOKEN 또는 GITHUB_REPOSITORY 미설정")
        sys.exit(1)

    dropped = jobs[MAX_JOBS_PER_RUN:]
    for topic in jobs[:MAX_JOBS_PER_RUN]:
        label = topic if topic else "큐의 다음 주제"
        ok, err = dispatch(topic)
        if ok:
            reply(
                f"🚀 <b>[접수 완료]</b>\n\n📌 <b>주제:</b> <code>{label}</code>\n\n"
                "렌더링을 시작했습니다. 완성되면 MP4 영상이 이 방으로 도착합니다."
            )
            print(f"  ✓ 트리거 성공: {label}")
        else:
            reply(f"⚠️ <b>[트리거 실패]</b>\n주제: <code>{label}</code>\n사유: {err}")
            print(f"[!] 트리거 실패: {label} / {err}")
            sys.exit(1)

    if dropped:
        reply(f"ℹ️ 한 번에 {MAX_JOBS_PER_RUN}건까지만 처리합니다. {len(dropped)}건은 다시 보내주세요.")


if __name__ == "__main__":
    main()
