# -*- coding: utf-8 -*-
"""
큐에이플러스(QA+) 텔레그램 전송 모듈
- 생성된 1080x1920 세로형 쇼츠 MP4 영상을 텔레그램 톡방으로 직접 전송
- 환경변수 TELEGRAM_BOT_TOKEN 및 TELEGRAM_CHAT_ID 활용
"""

import os
import sys
import requests

def send_video_to_telegram(video_path, caption=None):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("[!] TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID 환경변수가 설정되지 않아 텔레그램 전송을 건너뜁니다.")
        return False

    if not os.path.exists(video_path):
        print(f"[!] 전송할 영상 파일을 찾을 수 없습니다: {video_path}")
        return False

    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    print(f"\n[텔레그램] 영상 전송 시작 ({file_size_mb:.2f} MB): {os.path.basename(video_path)}...")

    if not caption:
        caption = f"🎬 <b>[큐에이플러스] 오늘의 일일 숏츠 영상이 완성되었습니다!</b>\n\n📌 <b>파일명:</b> {os.path.basename(video_path)}\n💡 스마트폰에 바로 저장하여 유튜브 쇼츠나 오픈채팅방에 업로드하세요."

    # 1. Send Video via Telegram Bot API
    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    
    with open(video_path, "rb") as f:
        files = {"video": f}
        data = {
            "chat_id": chat_id,
            "caption": caption,
            "parse_mode": "HTML",
            "supports_streaming": True
        }
        try:
            res = requests.post(url, files=files, data=data, timeout=120)
            if res.status_code == 200:
                print("  🎉 [성공] 텔레그램으로 영상 파일이 성공적으로 전송되었습니다!")
                return True
            else:
                print(f"  [오류] 텔레그램 API 응답 에러: {res.status_code} - {res.text}")
                # Fallback to sendDocument if sendVideo fails
                f.seek(0)
                doc_url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
                doc_res = requests.post(doc_url, files={"document": f}, data={"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"}, timeout=120)
                if doc_res.status_code == 200:
                    print("  🎉 [성공] 텔레그램 문서 형식으로 전송 완료!")
                    return True
                return False
        except Exception as e:
            print(f"  [오류] 텔레그램 전송 중 예외 발생: {e}")
            return False

def send_message_to_telegram(message):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not bot_token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)
    except Exception:
        pass

if __name__ == "__main__":
    if len(sys.argv) > 1:
        v_path = sys.argv[1]
        cap = sys.argv[2] if len(sys.argv) > 2 else None
        send_video_to_telegram(v_path, cap)
    else:
        print("사용법: python telegram_sender.py [비디오파일경로] [캡션]")
