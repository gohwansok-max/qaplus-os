"""Jarvis 결과물 저장용 최소 Google Drive REST 클라이언트.

OAuth 범위는 drive.file 하나다. 이 앱이 만든 폴더·파일만 보고 쓸 수 있으며,
사용자의 다른 Drive 파일은 읽거나 수정할 수 없다. 삭제·공유 API는 제공하지 않는다.
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

DRIVE_FILE_SCOPE = "https://www.googleapis.com/auth/drive.file"
TOKEN_URL = "https://oauth2.googleapis.com/token"
FILES_URL = "https://www.googleapis.com/drive/v3/files"
UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files"
FOLDER_MIME = "application/vnd.google-apps.folder"
DEFAULT_FOLDER_NAME = "Jarvis 저장함"
KST = timezone(timedelta(hours=9), name="KST")


def safe_filename(title: str, now: datetime) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|#\r\n\t]+", " ", title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()[:40].strip() or "Jarvis 답변"
    return f"{now.astimezone(KST):%Y-%m-%d_%H%M}_{cleaned}.md"


def build_markdown(save: dict[str, Any], now: datetime) -> tuple[str, str]:
    """저장 스냅숏을 (파일명, 본문)으로 만든다. 제목이 없으면 질문 앞부분을 쓴다."""
    question = str(save.get("q", "")).strip()
    answer = str(save.get("a", "")).strip()
    title = str(save.get("title", "")).strip() or re.sub(r"\s+", " ", question)[:30] or "Jarvis 답변"
    answered_at = str(save.get("at", ""))
    try:
        answered = datetime.fromisoformat(answered_at.replace("Z", "+00:00")).astimezone(KST).strftime("%Y-%m-%d %H:%M KST")
    except ValueError:
        answered = "기록 없음"
    body = "\n".join([
        f"# {title}",
        "",
        f"- 저장: {now.astimezone(KST):%Y-%m-%d %H:%M} KST",
        f"- 답변 시각: {answered}",
        f"- 질문: {question}" if question else "- 질문: (기록 없음)",
        "",
        "---",
        "",
        answer,
        "",
    ])
    return safe_filename(title, now), body


class DriveClient:
    """drive.file 범위 refresh token으로 Jarvis 전용 폴더에 파일을 만든다."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
        folder_name: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        # Gmail과 같은 OAuth 클라이언트를 쓰되 토큰은 분리한다(Gmail 토큰 범위를 넓히지 않는다).
        self.client_id = client_id or os.environ.get("JARVIS_DRIVE_CLIENT_ID") or os.environ.get("GMAIL_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("JARVIS_DRIVE_CLIENT_SECRET") or os.environ.get("GMAIL_CLIENT_SECRET", "")
        self.refresh_token = refresh_token or os.environ.get("JARVIS_DRIVE_REFRESH_TOKEN", "")
        if not all((self.client_id, self.client_secret, self.refresh_token)):
            raise RuntimeError("Google Drive 저장 설정(JARVIS_DRIVE_REFRESH_TOKEN)이 없습니다.")
        self.folder_name = folder_name or os.environ.get("JARVIS_DRIVE_FOLDER_NAME") or DEFAULT_FOLDER_NAME
        self.session = session or requests.Session()
        self._access_token = ""
        self._expires_at = 0.0

    def _token(self) -> str:
        if self._access_token and time.time() < self._expires_at - 60:
            return self._access_token
        response = self.session.post(TOKEN_URL, data={
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }, timeout=20)
        if response.status_code != 200:
            raise RuntimeError(f"Drive 토큰 갱신 실패 ({response.status_code})")
        data = response.json()
        token = str(data.get("access_token", ""))
        if not token:
            raise RuntimeError("Drive 토큰 응답이 비어 있습니다.")
        self._access_token = token
        self._expires_at = time.time() + int(data.get("expires_in", 3600))
        return token

    def _request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        # 허용 API: 폴더 검색·생성(files.list/create), 파일 업로드(upload files.create)만.
        if (method, url) not in {("GET", FILES_URL), ("POST", FILES_URL), ("POST", UPLOAD_URL)}:
            raise ValueError("허용되지 않은 Drive API 호출입니다.")
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._token()}"
        response = self.session.request(method, url, headers=headers, timeout=30, **kwargs)
        if response.status_code not in (200, 201):
            raise RuntimeError(f"Drive API 실패 ({response.status_code})")
        return response.json()

    def ensure_folder(self) -> str:
        """drive.file 범위에서는 이 앱이 만든 폴더만 검색된다. 없으면 새로 만든다."""
        name = self.folder_name.replace("\\", "\\\\").replace("'", "\\'")
        found = self._request("GET", FILES_URL, params={
            "q": f"name = '{name}' and mimeType = '{FOLDER_MIME}' and trashed = false",
            "fields": "files(id)",
            "spaces": "drive",
            "pageSize": 1,
        })
        files = found.get("files") or []
        if files:
            return str(files[0]["id"])
        created = self._request("POST", FILES_URL, params={"fields": "id"}, json={"name": self.folder_name, "mimeType": FOLDER_MIME})
        return str(created["id"])

    def upload_markdown(self, filename: str, content: str) -> dict[str, str]:
        folder_id = self.ensure_folder()
        boundary = f"jarvis-{uuid.uuid4().hex}"
        metadata = json.dumps({"name": filename, "parents": [folder_id], "mimeType": "text/markdown"}, ensure_ascii=False)
        body = (
            f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{metadata}\r\n"
            f"--{boundary}\r\nContent-Type: text/markdown; charset=UTF-8\r\n\r\n{content}\r\n"
            f"--{boundary}--\r\n"
        ).encode("utf-8")
        created = self._request(
            "POST", UPLOAD_URL,
            params={"uploadType": "multipart", "fields": "id,name,webViewLink"},
            headers={"Content-Type": f"multipart/related; boundary={boundary}"},
            data=body,
        )
        return {"id": str(created.get("id", "")), "name": str(created.get("name", filename)), "link": str(created.get("webViewLink", ""))}
