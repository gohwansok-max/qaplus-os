"""Jarvis용 최소 Gmail REST 클라이언트.

읽기와 Gmail Draft 생성만 구현한다. 메시지 전송, 삭제, 수정 API는 제공하지 않는다.
"""

from __future__ import annotations

import base64
import html
import hmac
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import parseaddr
from typing import Any

import requests

GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
GMAIL_COMPOSE_SCOPE = "https://www.googleapis.com/auth/gmail.compose"
GMAIL_SCOPES = (GMAIL_READONLY_SCOPE, GMAIL_COMPOSE_SCOPE)
GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"
TOKEN_URL = "https://oauth2.googleapis.com/token"
MESSAGE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{5,32}$")
DRAFT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{5,64}$")
APPROVAL_ID_RE = re.compile(r"^[0-9a-f]{24}$")


@dataclass(frozen=True)
class MailMessage:
    message_id: str
    thread_id: str
    sender: str
    subject: str
    received_at: datetime
    body: str
    message_id_header: str = ""
    references: str = ""


def _decode_websafe(value: str) -> bytes:
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _headers(payload: dict[str, Any]) -> dict[str, str]:
    return {
        str(item.get("name", "")).lower(): str(item.get("value", ""))
        for item in payload.get("headers", [])
        if item.get("name")
    }


def _plain_text_from_html(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _extract_body(payload: dict[str, Any]) -> str:
    plain_parts: list[str] = []
    html_parts: list[str] = []

    def walk(part: dict[str, Any]) -> None:
        mime_type = str(part.get("mimeType", "")).lower()
        data = part.get("body", {}).get("data")
        if data and mime_type in {"text/plain", "text/html"}:
            try:
                decoded = _decode_websafe(str(data)).decode("utf-8", errors="replace")
            except (ValueError, TypeError):
                return
            if mime_type == "text/plain":
                plain_parts.append(decoded)
            else:
                html_parts.append(_plain_text_from_html(decoded))
        for child in part.get("parts", []) or []:
            walk(child)

    walk(payload)
    text = "\n".join(part.strip() for part in plain_parts if part.strip())
    if not text:
        text = "\n".join(part for part in html_parts if part)
    text = text.replace("\x00", "")
    return text[:12_000]


def _looks_automated(headers: dict[str, str], sender: str, subject: str) -> bool:
    if headers.get("list-unsubscribe"):
        return True
    if headers.get("precedence", "").lower() in {"bulk", "list", "junk"}:
        return True
    auto_submitted = headers.get("auto-submitted", "").lower()
    if auto_submitted and auto_submitted != "no":
        return True
    sender_address = parseaddr(sender)[1].lower()
    local_part = sender_address.split("@", 1)[0]
    if any(token in local_part for token in ("no-reply", "noreply", "do-not-reply", "mailer-daemon", "notifications")):
        return True
    lowered_subject = subject.lower()
    return any(token in lowered_subject for token in ("newsletter", "뉴스레터", "광고", "프로모션", "unsubscribe"))


class GmailClient:
    """OAuth refresh token 기반 Gmail 클라이언트.

    허용 API는 messages.list/get, drafts.list/get/create뿐이다.
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.client_id = client_id or os.environ.get("GMAIL_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("GMAIL_CLIENT_SECRET", "")
        self.refresh_token = refresh_token or os.environ.get("GMAIL_REFRESH_TOKEN", "")
        if not all((self.client_id, self.client_secret, self.refresh_token)):
            raise RuntimeError("Gmail OAuth 환경변수가 비어 있습니다.")
        self.session = session or requests.Session()
        self._access_token = ""
        self._access_token_expires_at = 0.0

    def _token(self) -> str:
        if self._access_token and time.time() < self._access_token_expires_at - 60:
            return self._access_token
        try:
            response = self.session.post(
                TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                },
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            token = str(data.get("access_token", ""))
            if not token:
                raise ValueError("missing access token")
            self._access_token = token
            self._access_token_expires_at = time.time() + int(data.get("expires_in", 3600))
            return token
        except (requests.RequestException, ValueError, TypeError, KeyError):
            raise RuntimeError("Gmail OAuth 토큰 갱신에 실패했습니다.") from None

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        method = method.upper()
        allowed = (
            method == "GET" and (
                path == "/messages" or path.startswith("/messages/")
                or path == "/drafts" or path.startswith("/drafts/")
            )
        ) or (method == "POST" and path == "/drafts")
        if not allowed:
            raise RuntimeError("허용되지 않은 Gmail API 작업입니다.")
        try:
            response = self.session.request(
                method,
                f"{GMAIL_API_BASE}{path}",
                headers={"Authorization": f"Bearer {self._token()}"},
                timeout=30,
                **kwargs,
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError, TypeError):
            raise RuntimeError("Gmail API 요청에 실패했습니다.") from None

    def list_recent(self, hours: int = 24, max_results: int = 50) -> list[MailMessage]:
        if not 1 <= hours <= 24 * 14:
            raise ValueError("조회 시간 범위가 잘못되었습니다.")
        cutoff = datetime.now(timezone.utc).timestamp() - hours * 3600
        data = self._request(
            "GET",
            "/messages",
            params={
                "q": "newer_than:14d -in:spam -in:trash -category:promotions -category:social",
                "maxResults": min(max_results, 100),
                "includeSpamTrash": "false",
            },
        )
        results: list[MailMessage] = []
        for item in data.get("messages", []) or []:
            message_id = str(item.get("id", ""))
            if not MESSAGE_ID_RE.fullmatch(message_id):
                continue
            raw = self._request("GET", f"/messages/{message_id}", params={"format": "full"})
            received_at = datetime.fromtimestamp(int(raw.get("internalDate", "0")) / 1000, tz=timezone.utc)
            if received_at.timestamp() < cutoff:
                continue
            message = self._to_message(raw)
            headers = _headers(raw.get("payload", {}))
            if _looks_automated(headers, message.sender, message.subject):
                continue
            results.append(message)
        results.sort(key=lambda message: message.received_at, reverse=True)
        return results

    def get_message(self, message_id: str) -> MailMessage:
        if not MESSAGE_ID_RE.fullmatch(message_id):
            raise ValueError("잘못된 Gmail 메시지 ID입니다.")
        raw = self._request("GET", f"/messages/{message_id}", params={"format": "full"})
        return self._to_message(raw)

    @staticmethod
    def _to_message(raw: dict[str, Any]) -> MailMessage:
        payload = raw.get("payload", {})
        headers = _headers(payload)
        received_at = datetime.fromtimestamp(int(raw.get("internalDate", "0")) / 1000, tz=timezone.utc)
        return MailMessage(
            message_id=str(raw.get("id", "")),
            thread_id=str(raw.get("threadId", "")),
            sender=headers.get("from", "(발신자 없음)"),
            subject=headers.get("subject", "(제목 없음)"),
            received_at=received_at,
            body=_extract_body(payload),
            message_id_header=headers.get("message-id", ""),
            references=headers.get("references", ""),
        )

    def _existing_draft_for_approval(self, approval_id: str) -> str | None:
        page_token = ""
        while True:
            params: dict[str, Any] = {"maxResults": 500, "includeSpamTrash": "false"}
            if page_token:
                params["pageToken"] = page_token
            data = self._request("GET", "/drafts", params=params)
            for item in data.get("drafts", []) or []:
                draft_id = str(item.get("id", ""))
                if not DRAFT_ID_RE.fullmatch(draft_id):
                    continue
                draft = self._request("GET", f"/drafts/{draft_id}", params={"format": "full"})
                headers = _headers(draft.get("message", {}).get("payload", {}))
                if hmac.compare_digest(headers.get("x-jarvis-approval-id", ""), approval_id):
                    return draft_id
            page_token = str(data.get("nextPageToken", ""))
            if not page_token:
                return None

    def create_reply_draft(self, original: MailMessage, reply_body: str, approval_id: str) -> tuple[str, bool]:
        """동일 승인당 답장 Draft 하나만 만들며 어떤 전송 API도 호출하지 않는다."""
        if not APPROVAL_ID_RE.fullmatch(approval_id):
            raise ValueError("잘못된 답장 승인 식별자입니다.")
        existing = self._existing_draft_for_approval(approval_id)
        if existing:
            return existing, False
        recipient = parseaddr(original.sender)[1]
        if not recipient or "@" not in recipient:
            raise ValueError("답장 수신자를 확인할 수 없습니다.")
        body = reply_body.strip()
        if not body:
            raise ValueError("답장 초안이 비어 있습니다.")

        message = EmailMessage()
        message["To"] = recipient
        message["Subject"] = original.subject if original.subject.lower().startswith("re:") else f"Re: {original.subject}"
        message["X-Jarvis-Approval-ID"] = approval_id
        if original.message_id_header:
            message["In-Reply-To"] = original.message_id_header
            references = f"{original.references} {original.message_id_header}".strip()
            message["References"] = references
        message.set_content(body)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii").rstrip("=")
        payload: dict[str, Any] = {"message": {"raw": raw}}
        if original.thread_id:
            payload["message"]["threadId"] = original.thread_id
        result = self._request("POST", "/drafts", json=payload)
        draft_id = str(result.get("id", ""))
        if not draft_id:
            raise RuntimeError("Gmail Draft 생성 결과를 확인할 수 없습니다.")
        return draft_id, True
