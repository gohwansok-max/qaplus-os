# -*- coding: utf-8 -*-
"""
큐에이플러스(QA+) 텔레그램 봇 리스너 서비스
- 스마트폰 텔레그램에서 메시지를 수신하여 즉시 쇼츠 비디오 렌더링 및 발송
- 명령어:
  /make [주제]
  /daily (오늘치 대기 주제 즉시 실행)
"""

import os
import sys
import time
import requests
import threading

# Fix UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, "scripts"))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = str(os.environ.get("TELEGRAM_CHAT_ID", ""))
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "gohwansok-max/qaplus-os")

def trigger_github_action(topic=None):
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return False

    url = f"https://api.github.com/repos/{GITHUB_REPO}/dispatches"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {
        "event_type": "generate_video",
        "client_payload": {"topic": topic} if topic else {}
    }
    
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=10)
        return res.status_code == 204
    except Exception as e:
        print(f"[!] GitHub API 호출 에러: {e}")
        return False

def render_locally_and_send(chat_id, topic=None):
    try:
        from daily_qa_autopilot import run_daily_autopilot
        send_telegram_reply(chat_id, "🎬 <b>[렌더링 진행 중]</b>\n20년 선배 TTS 음성과 1080x1920 세로형 카드를 합성하고 있습니다. 잠시만 기다려주세요...")
        run_daily_autopilot(topic)
    except Exception as e:
        print(f"[!] 로컬 렌더링 에러: {e}")
        send_telegram_reply(chat_id, f"⚠️ 영상 생성 중 오류가 발생했습니다: {e}")

def send_telegram_reply(chat_id, text):
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
    except Exception:
        pass

def process_command(chat_id, text):
    cleaned = text.strip()
    
    # 1. /make or 만들어줘
    if cleaned.startswith("/make") or cleaned.startswith("만들어줘"):
        topic = cleaned.replace("/make", "").replace("만들어줘:", "").replace("만들어줘", "").strip()
        topic = topic.strip("[]'\"").strip()
        
        if not topic:
            send_telegram_reply(chat_id, "💡 <b>사용법:</b> <code>/make [주제]</code>\n예: <code>/make 스마트HACCP 온도 센서 연동 방법</code>")
            return
            
        send_telegram_reply(chat_id, f"🚀 <b>[접수 완료]</b>\n\n📌 <b>주제:</b> <code>{topic}</code>\n\n쇼츠 영상 제작을 시작했습니다. 1~2분 뒤 완성된 MP4 영상이 도착합니다!")
        
        # Try GitHub Actions first if token exists, otherwise render locally
        if GITHUB_TOKEN:
            success = trigger_github_action(topic)
            if success:
                return
                
        # Run local rendering in background thread
        threading.Thread(target=render_locally_and_send, args=(chat_id, topic), daemon=True).start()

    # 2. /daily or 오늘영상
    elif cleaned in ["/daily", "오늘영상", "오늘"]:
        send_telegram_reply(chat_id, "📅 <b>[일일 토픽 렌더링 시작]</b>\n\n30일 토픽 큐에서 오늘의 주제를 가져와 렌더링합니다!")
        if GITHUB_TOKEN:
            success = trigger_github_action(None)
            if success:
                return
        threading.Thread(target=render_locally_and_send, args=(chat_id, None), daemon=True).start()

    # 3. Help
    elif cleaned in ["/start", "/help", "도움말"]:
        help_msg = (
            "👋 <b>큐에이플러스 AI 영상 제작 봇</b>\n\n"
            "• <code>/make [주제]</code> : 원하는 주제로 즉시 숏츠 영상 제작\n"
            "• <code>/daily</code> : 30일 큐에서 오늘자 주제 즉시 제작\n\n"
            "💡 <b>예시:</b>\n"
            "<code>/make 스마트HACCP 온도 센서 연동 방법</code>\n"
            "<code>/make 레토르트 살균 F0값 계산</code>\n"
            "<code>/make CCP 금속검출기 테스트피스 주기</code>"
        )
        send_telegram_reply(chat_id, help_msg)

def run_bot():
    if not TELEGRAM_BOT_TOKEN:
        print("[!] TELEGRAM_BOT_TOKEN 환경변수가 필요합니다.")
        return

    print("==================================================================")
    print("  🤖 [큐에이플러스] 텔레그램 봇 서비스 가동 시작")
    print("==================================================================")
    print(f"  • Bot Token: {TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"  • Chat ID: {TELEGRAM_CHAT_ID}")
    print("  • 대기 중... 텔레그램에서 명령어를 보내보세요.")

    # Send online alert to Telegram
    if TELEGRAM_CHAT_ID:
        send_telegram_reply(TELEGRAM_CHAT_ID, "🟢 <b>[큐에이플러스 봇 온라인]</b>\n텔레그램 리스너가 가동되었습니다. <code>/make [주제]</code>를 입력해보세요!")

    last_update_id = 0
    # First get latest update_id to avoid executing old buffered commands
    try:
        init_res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?limit=100", timeout=10)
        if init_res.status_code == 200:
            updates = init_res.json().get("result", [])
            if updates:
                last_update_id = updates[-1]["update_id"]
                print(f"  • 기존 {len(updates)}개 메시지 확인 완료. 최신 ID: {last_update_id}")
    except Exception:
        pass

    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=20"
            res = requests.get(url, timeout=30)
            if res.status_code == 200:
                data = res.json()
                for update in data.get("result", []):
                    last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    chat_id = str(msg.get("chat", {}).get("id", ""))
                    text = msg.get("text", "").strip()

                    if not text:
                        continue

                    if TELEGRAM_CHAT_ID and chat_id != TELEGRAM_CHAT_ID:
                        continue

                    print(f"  [수신] Chat: {chat_id} | Text: {text}")
                    process_command(chat_id, text)

        except Exception as e:
            print(f"[!] 봇 루프 에러: {e}")
            time.sleep(3)

if __name__ == "__main__":
    run_bot()

