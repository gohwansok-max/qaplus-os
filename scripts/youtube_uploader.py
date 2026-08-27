#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
큐에이플러스(QA+) 유튜브 쇼츠 자동 업로드 모듈
- OAuth 리프레시 토큰으로 액세스 토큰을 발급받아 YouTube Data API v3(videos.insert, resumable upload)를 호출한다.
- Blogger와 동일한 Google Cloud 프로젝트/OAuth 클라이언트를 재사용하되, 스코프가 다르므로
  리프레시 토큰은 scripts/get_youtube_refresh_token.py로 별도 발급받아야 한다.
"""

import os
import json
import requests

YOUTUBE_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


def get_access_token():
    """ YouTube 전용 리프레시 토큰으로 액세스 토큰 발급. 클라이언트 ID/보안 비밀은 Blogger와 재사용. """
    client_id = os.environ.get("YOUTUBE_CLIENT_ID") or os.environ.get("BLOGGER_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET") or os.environ.get("BLOGGER_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        return None

    resp = requests.post(GOOGLE_TOKEN_URL, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }, timeout=30)

    if resp.status_code != 200:
        print(f"[!] YouTube 액세스 토큰 발급 실패: {resp.status_code} {resp.text}")
        return None

    return resp.json().get("access_token")


def is_configured():
    """ YouTube 자동 업로드에 필요한 환경변수가 전부 있는지 확인 (클라이언트 ID/보안 비밀은 Blogger 것도 인정) """
    has_client = (os.environ.get("YOUTUBE_CLIENT_ID") or os.environ.get("BLOGGER_CLIENT_ID")) and \
                 (os.environ.get("YOUTUBE_CLIENT_SECRET") or os.environ.get("BLOGGER_CLIENT_SECRET"))
    return bool(has_client and os.environ.get("YOUTUBE_REFRESH_TOKEN"))


def upload_short(video_path, title, description, tags=None, privacy_status="public"):
    """
    쇼츠(세로형 짧은 영상)를 유튜브에 업로드한다.
    privacy_status: "public"(즉시 공개) | "unlisted"(링크 공개) | "private"(비공개, 검수 후 수동 공개)
    제목/설명에 자동으로 #Shorts 태그를 붙여 쇼츠 피드에 노출되도록 한다.
    """
    if not os.path.exists(video_path):
        return {"ok": False, "error": f"영상 파일을 찾을 수 없습니다: {video_path}"}

    access_token = get_access_token()
    if not access_token:
        return {"ok": False, "error": "액세스 토큰 발급 실패 (환경변수 미설정 또는 리프레시 토큰 만료)"}

    if "#shorts" not in title.lower() and "#shorts" not in description.lower():
        description = f"{description}\n\n#Shorts #HACCP #식품안전 #QAPLUS"

    metadata = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags or ["HACCP", "FSSC22000", "식품안전", "품질관리", "Shorts"],
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    file_size = os.path.getsize(video_path)

    # 1단계: 업로드 세션 시작 (resumable)
    init_resp = requests.post(
        YOUTUBE_UPLOAD_URL,
        params={"uploadType": "resumable", "part": "snippet,status"},
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(file_size),
        },
        data=json.dumps(metadata),
        timeout=30,
    )
    if init_resp.status_code != 200:
        return {"ok": False, "error": f"업로드 세션 시작 실패: {init_resp.status_code} {init_resp.text}"}

    upload_url = init_resp.headers.get("Location")
    if not upload_url:
        return {"ok": False, "error": "업로드 세션 URL을 받지 못했습니다."}

    # 2단계: 실제 영상 바이너리 업로드
    with open(video_path, "rb") as f:
        video_data = f.read()

    upload_resp = requests.put(
        upload_url,
        headers={"Content-Type": "video/mp4", "Content-Length": str(file_size)},
        data=video_data,
        timeout=300,
    )

    if upload_resp.status_code in (200, 201):
        data = upload_resp.json()
        video_id = data.get("id")
        return {
            "ok": True,
            "video_id": video_id,
            "url": f"https://youtube.com/shorts/{video_id}",
            "status": privacy_status,
        }
    return {"ok": False, "error": f"{upload_resp.status_code} {upload_resp.text[:500]}"}


def _load_dotenv_into_environ():
    """ 이 스크립트를 단독 실행할 때(daily_qa_autopilot.py를 거치지 않을 때) .env를 os.environ에 로드 """
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root_dir, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


if __name__ == "__main__":
    import argparse
    _load_dotenv_into_environ()
    parser = argparse.ArgumentParser(description="QA+ YouTube Shorts Uploader")
    parser.add_argument("--video", required=True, help="업로드할 mp4 파일 경로")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    args = parser.parse_args()

    if not is_configured():
        print("[!] YOUTUBE_REFRESH_TOKEN 및 (YOUTUBE_ 또는 BLOGGER_) CLIENT_ID/SECRET 환경변수가 필요합니다.")
    else:
        result = upload_short(args.video, args.title, args.description, privacy_status=args.privacy)
        print(result)
