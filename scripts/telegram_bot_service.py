# -*- coding: utf-8 -*-
"""
큐에이플러스(QA+) 텔레그램 봇 리스너 서비스
- 스마트폰 텔레그램에서 메시지를 보내면 GitHub 클라우드(Actions)를 즉시 트리거하여 영상을 렌더링
- 명령어 예시:
  /make 레토르트 살균 F0값 계산
  /make 알레르기 교차오염 세척 검증
  /daily (오늘치 대기 주제 즉시 실행)
"""

import os
import sys
import time
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")      # GitHub Personal Access Token (repo 권한)
GITHUB_REPO = os.environ.get("GITHUB_REPO")        # 예: "myusername/ai-ceo-os"

def trigger_github_action(topic=None):
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print("[!] GITHUB_TOKEN 또는 GITHUB_REPO가 설정되지 않았습니다.")
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

def send_telegram_reply(chat_id, text):
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
    except Exception:
        pass

def run_bot():
    if not TELEGRAM_BOT_TOKEN:
        print("[!] TELEGRAM_BOT_TOKEN 환경변수가 필요합니다.")
        return

    print("==================================================================")
    print("  🤖 [큐에이플러스] 텔레그램 봇 서비스 가동 중...")
    print("==================================================================")
    print("스마트폰 텔레그램에서 명령어를 보내면 클라우드에서 영상을 렌더링합니다.")
    print("명령어: /make [주제] 또는 /daily")

    last_update_id = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
            res = requests.get(url, timeout=40)
            if res.status_code == 200:
                data = res.json()
                for update in data.get("result", []):
                    last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    chat_id = str(msg.get("chat", {}).get("id", ""))
                    text = msg.get("text", "").strip()

                    # Only respond to authorized chat_id if set
                    if TELEGRAM_CHAT_ID and chat_id != TELEGRAM_CHAT_ID:
                        continue

                    if text.startswith("/make ") or text.startswith("만들어줘:"):
                        topic = text.replace("/make ", "").replace("만들어줘:", "").strip()
                        if topic:
                            send_telegram_reply(chat_id, f"🚀 <b>[접수 완료]</b>\n\n주제: <code>{topic}</code>\n\n클라우드에서 1080x1920 세로형 쇼츠 MP4 렌더링을 시작했습니다!\n약 1~2분 뒤 완성된 영상이 톡으로 도착합니다.")
                            success = trigger_github_action(topic)
                            if not success:
                                send_telegram_reply(chat_id, "⚠️ GitHub Actions 트리거 실패. 토큰 및 저장소 설정을 확인해주세요.")
                    
                    elif text == "/daily" or text == "오늘영상":
                        send_telegram_reply(chat_id, "📅 <b>[일일 토픽 렌더링 시작]</b>\n\n토픽 큐에서 오늘의 주제를 가져와 렌더링합니다. 잠시만 기다려주세요!")
                        trigger_github_action(None)

                    elif text == "/start" or text == "/help":
                        help_msg = "👋 <b>큐에이플러스 AI 영상 제작 봇</b>\n\n• <code>/make [주제]</code> : 원하는 주제로 즉시 쇼츠 영상 렌더링\n• <code>/daily</code> : 큐에 등록된 오늘자 주제 즉시 렌더링\n\nPC가 꺼져 있어도 클라우드가 1분 만에 MP4 영상을 만들어 보내드립니다!"
                        send_telegram_reply(chat_id, help_msg)

        except Exception as e:
            print(f"[!] 봇 에러 (5초 후 재시도): {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
