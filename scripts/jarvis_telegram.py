"""Jarvis 전용 Telegram API 유틸리티."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import time
from email.utils import parseaddr
from typing import Any

import requests

MAX_TELEGRAM_DOWNLOAD = 20 * 1024 * 1024
MAX_CALLBACK_TTL_SECONDS = 48 * 60 * 60
DRAFT_CALLBACK_RE = re.compile(r"^d:([A-Za-z0-9_-]{5,32}):([0-9a-z]{1,10}):([A-Za-z0-9_-]{16})$")


def _base36(value: int) -> str:
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    if value == 0:
        return "0"
    output = ""
    while value:
        value, remainder = divmod(value, 36)
        output = alphabet[remainder] + output
    return output


def make_draft_callback(message_id: str, secret: str, ttl_seconds: int = 48 * 60 * 60, now: float | None = None) -> str:
    expires_minutes = int(((now if now is not None else time.time()) + ttl_seconds) // 60)
    payload = f"d:{message_id}:{_base36(expires_minutes)}"
    signature = base64.urlsafe_b64encode(hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()[:12]).decode("ascii").rstrip("=")
    callback = f"{payload}:{signature}"
    if len(callback.encode("utf-8")) > 64:
        raise ValueError("Telegram callback_data가 64바이트를 초과합니다.")
    return callback


def approval_id(callback: str) -> str:
    return hashlib.sha256(callback.encode("utf-8")).hexdigest()[:24]


def verify_draft_callback(callback: str, secret: str, now: float | None = None) -> tuple[str, str]:
    match = DRAFT_CALLBACK_RE.fullmatch(callback)
    if not match or len(callback.encode("utf-8")) > 64 or not secret:
        raise ValueError("유효하지 않은 답장 승인값입니다.")
    message_id, expires_base36, provided_signature = match.groups()
    expires_seconds = int(expires_base36, 36) * 60
    current = int(now if now is not None else time.time())
    if expires_seconds < current or expires_seconds > current + MAX_CALLBACK_TTL_SECONDS + 120:
        raise ValueError("만료되었거나 유효기간이 잘못된 답장 승인값입니다.")
    payload = f"d:{message_id}:{expires_base36}"
    expected = base64.urlsafe_b64encode(hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()[:12]).decode("ascii").rstrip("=")
    if not hmac.compare_digest(provided_signature, expected):
        raise ValueError("답장 승인 서명이 올바르지 않습니다.")
    return message_id, approval_id(callback)


def masked_sender(sender: str) -> str:
    name, address = parseaddr(sender)
    if name:
        compact = name.strip()
        if re.fullmatch(r"[가-힣]{2,4}", compact):
            return compact[0] + "*" * max(1, len(compact) - 2) + compact[-1]
        words = compact.split()
        return " ".join(word[:1] + "***" for word in words)[:80]
    if "@" not in address:
        return "발신자 확인 필요"
    local, domain = address.split("@", 1)
    visible = local[:2] if len(local) > 2 else local[:1]
    return f"{visible}***@{domain}"


class TelegramClient:
    def __init__(self, token: str | None = None, chat_id: str | None = None, session: requests.Session | None = None) -> None:
        self.token = token or os.environ.get("JARVIS_TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.environ.get("JARVIS_TELEGRAM_CHAT_ID", "")
        if not self.token or not self.chat_id:
            raise RuntimeError("Jarvis Telegram 환경변수가 비어 있습니다.")
        self.session = session or requests.Session()

    def _api(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self.session.post(
                f"https://api.telegram.org/bot{self.token}/{method}",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            if not data.get("ok"):
                raise ValueError("telegram not ok")
            return data
        except (requests.RequestException, ValueError, TypeError):
            raise RuntimeError("Telegram API 요청에 실패했습니다.") from None

    def send_message(self, text: str, reply_markup: dict[str, Any] | None = None) -> None:
        chunks = [text[index:index + 3900] for index in range(0, max(len(text), 1), 3900)]
        for index, chunk in enumerate(chunks):
            payload: dict[str, Any] = {"chat_id": self.chat_id, "text": chunk}
            if reply_markup and index == len(chunks) - 1:
                payload["reply_markup"] = reply_markup
            self._api("sendMessage", payload)

    def download_voice(self, file_id: str) -> tuple[bytes, str]:
        data = self._api("getFile", {"file_id": file_id})
        result = data.get("result", {})
        file_size = int(result.get("file_size") or 0)
        file_path = str(result.get("file_path", ""))
        if not file_path or file_size > MAX_TELEGRAM_DOWNLOAD:
            raise RuntimeError("Telegram 음성 파일을 내려받을 수 없습니다.")
        try:
            response = self.session.get(
                f"https://api.telegram.org/file/bot{self.token}/{file_path}",
                timeout=60,
            )
            response.raise_for_status()
            audio = response.content
        except requests.RequestException:
            raise RuntimeError("Telegram 음성 파일 다운로드에 실패했습니다.") from None
        if not audio or len(audio) > MAX_TELEGRAM_DOWNLOAD:
            raise RuntimeError("Telegram 음성 파일 크기가 허용 범위를 벗어났습니다.")
        return audio, os.path.basename(file_path) or "voice.ogg"


def draft_keyboard(message_id: str, secret: str) -> dict[str, Any]:
    return {
        "inline_keyboard": [[
            {"text": "답장 초안 만들기", "callback_data": make_draft_callback(message_id, secret)}
        ]]
    }
