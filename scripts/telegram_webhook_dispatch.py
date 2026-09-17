"""Webhook 발행 요청 처리.

Telegram webhook 수신과 Blogger OAuth 실행을 분리한다.
Blogger 발행 성공 후 원본 Telegram 메시지의 발행/보류 버튼을 제거한다.
"""

import json
import os
import re
import sys

import requests

from blogger_publisher import publish_draft


def telegram_api(method, payload):
    """Telegram Bot API를 호출한다."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/{method}",
            json=payload,
            timeout=20,
        )

        try:
            data = response.json()
        except ValueError:
            raise RuntimeError(
                f"Telegram API 응답 형식 오류: {method}"
            ) from None

        if not response.ok or not data.get("ok"):
            raise RuntimeError(
                f"Telegram API 실패: {method}"
            )

        return data

    except requests.RequestException:
        raise RuntimeError(
            "Telegram 연결 실패"
        ) from None


def send(text):
    """Telegram으로 결과 메시지를 보낸다."""
    return telegram_api(
        "sendMessage",
        {
            "chat_id": os.environ["TELEGRAM_CHAT_ID"],
            "text": text,
        },
    )


def remove_inline_keyboard(message_id):
    """기존 Telegram 메시지의 Inline Keyboard를 제거한다."""
    return telegram_api(
        "editMessageReplyMarkup",
        {
            "chat_id": os.environ["TELEGRAM_CHAT_ID"],
            "message_id": message_id,
            "reply_markup": {
                "inline_keyboard": []
            },
        },
    )


def main():
    """GitHub repository_dispatch 이벤트를 처리한다."""
    with open(
        os.environ["GITHUB_EVENT_PATH"],
        encoding="utf-8",
    ) as stream:
        event = json.load(stream)

    if event.get("action") != "telegram_blog_publish":
        raise ValueError(
            "지원하지 않는 이벤트"
        )

    payload = event.get(
        "client_payload",
        {},
    )

    post_id = str(
        payload.get(
            "post_id",
            "",
        )
    )

    if not re.fullmatch(
        r"[0-9]{1,30}",
        post_id,
    ):
        raise ValueError(
            "잘못된 Blogger 글 번호"
        )

    # Cloudflare Worker에서 전달한 Telegram 원본 메시지 번호
    message_id_raw = payload.get(
        "message_id"
    )

    message_id = None

    if message_id_raw is not None:
        try:
            parsed_message_id = int(
                message_id_raw
            )

            if parsed_message_id > 0:
                message_id = parsed_message_id

        except (TypeError, ValueError):
            message_id = None

    # Blogger 공개 발행
    result = publish_draft(
        post_id
    )

    if not result.get("ok"):
        send(
            "🚨 [QA+] 발행 실패\n\n"
            f"글 번호: {post_id}\n"
            "GitHub 실행 로그를 확인해 주세요."
        )

        raise RuntimeError(
            "Blogger 공개 발행 실패"
        )

    title = (
        result.get("title")
        or "블로그 글"
    )

    url = (
        result.get("url")
        or ""
    )

    already_live = bool(
        result.get(
            "already_live",
            False,
        )
    )

    # 발행에 성공했거나 이미 공개된 글인 경우
    # 원본 Telegram 메시지의 발행/보류 버튼을 제거한다.
    #
    # 버튼 제거 실패는 Blogger 발행 성공 자체를
    # 실패 처리하지 않는다.
    keyboard_removed = False

    if message_id is not None:
        try:
            remove_inline_keyboard(
                message_id
            )

            keyboard_removed = True

        except Exception:
            print(
                "::warning::"
                "Blogger 발행은 성공했지만 "
                "Telegram 버튼 제거에는 실패했습니다."
            )

    # 이미 공개된 글
    if already_live:
        send(
            "ℹ️ [QA+] 이미 공개된 글입니다.\n\n"
            f"📌 {title}\n"
            f"🔗 {url}"
        )

    # 이번 실행에서 새로 공개된 글
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
                "message_id": message_id,
                "keyboard_removed": keyboard_removed,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    try:
        main()

    except Exception:
        print(
            "::error::"
            "Webhook 발행 처리 실패. "
            "비밀값 보호를 위해 "
            "예외 원문을 출력하지 않습니다."
        )

        sys.exit(1)
