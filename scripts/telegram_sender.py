# -*- coding: utf-8 -*-
"""
큐에이플러스(QA+) 텔레그램 전송 모듈
- 생성된 1080x1920 세로형 쇼츠 MP4 영상을 텔레그램 톡방으로 직접 전송
- 환경변수 TELEGRAM_BOT_TOKEN 및 TELEGRAM_CHAT_ID 활용
"""

import os
import sys
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    from dotenv import load_dotenv
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    load_dotenv(os.path.join(base_dir, ".env"))
except ImportError:
    pass

TELEGRAM_UPLOAD_LIMIT_MB = 50  # Bot API 업로드 한도. sendVideo·sendDocument 모두 동일합니다.


def send_video_to_telegram(video_path, caption=None):
    """전송에 실패하면 조용히 넘어가지 않고 예외를 던집니다.

    이전에는 실패해도 False 만 돌려주고 호출부가 그것을 버렸기 때문에,
    영상이 도착하지 않아도 GitHub Actions 잡은 초록색 success 로 끝났습니다.
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID 환경변수가 비어 있습니다.")

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"전송할 영상 파일을 찾을 수 없습니다: {video_path}")

    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    print(f"\n[텔레그램] 영상 전송 시작 ({file_size_mb:.2f} MB): {os.path.basename(video_path)}...")

    if not caption:
        caption = f"🎬 <b>[큐에이플러스] 오늘의 일일 숏츠 영상이 완성되었습니다!</b>\n\n📌 <b>파일명:</b> {os.path.basename(video_path)}\n💡 스마트폰에 바로 저장하여 유튜브 쇼츠나 오픈채팅방에 업로드하세요."

    if file_size_mb > TELEGRAM_UPLOAD_LIMIT_MB:
        send_message_to_telegram(
            f"⚠️ <b>[용량 초과]</b>\n{os.path.basename(video_path)} 가 {file_size_mb:.1f}MB 라 "
            f"텔레그램 봇 한도({TELEGRAM_UPLOAD_LIMIT_MB}MB)를 넘습니다.\n"
            "GitHub Actions 실행 화면의 아티팩트에서 내려받아 주세요."
        )
        raise RuntimeError(
            f"영상 용량 {file_size_mb:.1f}MB 가 텔레그램 봇 한도 {TELEGRAM_UPLOAD_LIMIT_MB}MB 를 초과합니다."
        )

    last_error = ""
    for attempt in range(1, 3):
        try:
            with open(video_path, "rb") as f:
                res = requests.post(
                    f"https://api.telegram.org/bot{bot_token}/sendVideo",
                    files={"video": f},
                    data={
                        "chat_id": chat_id,
                        "caption": caption,
                        "parse_mode": "HTML",
                        "supports_streaming": True,
                    },
                    timeout=180,
                )
            if res.status_code == 200:
                print("  [SUCCESS] 텔레그램으로 영상 파일이 성공적으로 전송되었습니다!")
                return True

            last_error = f"sendVideo {res.status_code} - {res.text[:300]}"
            print(f"  [ERROR] {last_error}")

            # 동영상 인코딩 문제로 sendVideo 가 거부될 때를 대비한 문서 전송 대체 경로
            with open(video_path, "rb") as f:
                doc_res = requests.post(
                    f"https://api.telegram.org/bot{bot_token}/sendDocument",
                    files={"document": f},
                    data={"chat_id": chat_id, "caption": caption, "parse_mode": "HTML"},
                    timeout=180,
                )
            if doc_res.status_code == 200:
                print("  [SUCCESS] 텔레그램 문서 형식으로 전송 완료!")
                return True
            last_error = f"sendDocument {doc_res.status_code} - {doc_res.text[:300]}"
            print(f"  [ERROR] {last_error}")

        except Exception as exc:
            last_error = str(exc)
            print(f"  [ERROR] 텔레그램 전송 중 예외 발생(시도 {attempt}/2): {exc}")

    raise RuntimeError(f"텔레그램 영상 전송에 실패했습니다: {last_error}")


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
