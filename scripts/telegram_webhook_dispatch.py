"""Webhook 발행 요청 처리. Telegram 수신과 Blogger OAuth 실행을 분리한다."""

import json
import os
import re
import sys

import requests

from blogger_publisher import publish_draft


def send(text):
    """Telegram으로 처리 결과를 전송한다."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
            },
            timeout=20,
        )

        if not response.ok:
            raise RuntimeError("Telegram 회신 실패")

        data = response.json()

        if not data.get("ok"):
            raise RuntimeError("Telegram 회신 실패")

    except requests.RequestException:
        raise RuntimeError("Telegram 연결 실패") from None


def main():
    """GitHub repository_dispatch 이벤트를 받아 Blogger 글을 발행한다."""

    # GitHub Actions 이벤트 데이터 읽기
    with open(
        os.environ["GITHUB_EVENT_PATH"],
        encoding="utf-8",
    ) as stream:
        event = json.load(stream)

    # 허용된 이벤트인지 확인
    if event.get("action") != "telegram_blog_publish":
        raise ValueError("지원하지 않는 이벤트")

    # Blogger 글 번호 확인
    post_id = str(
        event.get("client_payload", {}).get("post_id", "")
    )

    if not re.fullmatch(r"[0-9]{1,30}", post_id):
        raise ValueError("잘못된 Blogger 글 번호")

    # Blogger 발행 처리
    result = publish_draft(post_id)

    # 발행 실패
    if not result.get("ok"):
        send(
            "🚨 [QA+] 발행 실패\n\n"
            f"글 번호: {post_id}\n"
            "GitHub 실행 로그를 확인해 주세요."
        )
        raise RuntimeError("Blogger 공개 발행 실패")

    title = result.get("title") or "블로그 글"
    url = result.get("url") or ""
    already_live = result.get("already_live", False)

    # 이미 공개된 글인 경우
    if already_live:
        send(
            "ℹ️ [QA+] 이미 공개된 글입니다.\n\n"
            f"📌 {title}\n"
            f"🔗 {url}"
        )

    # 이번 요청에서 새로 공개된 경우
    else:
        send(
            "✅ [QA+] 공개 발행 완료\n\n"
            f"📌 {title}\n"
            f"🔗 {url}"
        )

    # GitHub Actions 로그용 결과
    print(
        json.dumps(
            {
                "ok": True,
                "post_id": post_id,
                "url": url,
                "already_live": already_live,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    try:
        main()

    except Exception:
        print(
            "::error::Webhook 발행 처리 실패. "
            "비밀값 보호를 위해 예외 원문을 출력하지 않습니다."
        )
        sys.exit(1)
