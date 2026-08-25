# -*- coding: utf-8 -*-
"""
YouTube Shorts Automated Uploader via YouTube Data API v3
"""

import os
import sys
import argparse
import pickle
import time

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
except ImportError:
    print("[ERROR] Required packages not installed. Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

DEFAULT_TITLE = "HACCP 심사 탈락 1순위? CCP 한계기준 & 유효성검증 1분 핵심 #Shorts"
DEFAULT_DESCRIPTION = """HACCP/FSSC22000 인증 준비 중 CCP 한계기준(CL)과 유효성검증(Validation) 때문에 막히셨나요?
20년 품질관리 실무 선배가 알려주는 3대 핵심 포인트!

📌 핵심 요약
1. 한계기준(CL) vs 운용한계(OL) 차이점
2. 유효성검증(Validation) vs 일상검증(Verification)
3. 식약처 심사관이 확인하는 3대 필수 서류

💬 200명이 함께하는 HACCP 실무 오픈채팅방 (무료 자료 배포)
👉 설명란 / 고정댓글 링크를 확인하세요!

#Shorts #HACCP #FSSC22000 #CCP #식품안전 #품질관리 #QA #QC #식약처심사
"""

DEFAULT_TAGS = ["HACCP", "CCP", "FSSC22000", "식품안전", "품질관리", "유효성검증", "한계기준", "식약처", "Shorts"]

def get_authenticated_service(client_secrets_file="client_secret.json", token_file="token.pickle"):
    credentials = None
    if os.path.exists(token_file):
        with open(token_file, "rb") as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("[INFO] Refreshing existing access token...")
            credentials.refresh(Request())
        else:
            if not os.path.exists(client_secrets_file):
                print(f"\n[ERROR] '{client_secrets_file}' 파일이 필요합니다.")
                print("1. Google Cloud Console (https://console.cloud.google.com) 접속")
                print("2. 'YouTube Data API v3' 사용 설정")
                print("3. '사용자 인증 정보' -> 'OAuth 클라이언트 ID (데스크톱 앱)' 생성 후 JSON 다운로드")
                print(f"4. 다운로드한 파일을 '{client_secrets_file}' 이름으로 저장해주세요.\n")
                return None

            print("[INFO] Initiating browser OAuth 2.0 login...")
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            credentials = flow.run_local_server(port=0)

        with open(token_file, "wb") as token:
            pickle.dump(credentials, token)
            print(f"[OK] Saved auth token to {token_file}")

    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def upload_video(youtube, file_path, title, description, tags, category_id="27", privacy_status="unlisted"):
    if not os.path.exists(file_path):
        print(f"[ERROR] Video file not found: {file_path}")
        return None

    # Ensure #Shorts is in title or description
    if "#Shorts" not in title and "#shorts" not in title:
        title = f"{title} #Shorts"

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(file_path, chunksize=1024*1024*5, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    print(f"\n[START] Uploading '{file_path}' to YouTube ({privacy_status})...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            print(f"  Uploading... {progress}%")

    video_id = response.get("id")
    shorts_url = f"https://www.youtube.com/shorts/{video_id}"
    watch_url = f"https://www.youtube.com/watch?v={video_id}"

    print("\n=======================================================")
    print("🎉 [SUCCESS] YouTube Shorts 업로드 완료!")
    print(f"  - Video ID:    {video_id}")
    print(f"  - Title:       {title}")
    print(f"  - Privacy:     {privacy_status}")
    print(f"  - Shorts Link: {shorts_url}")
    print(f"  - Watch Link:  {watch_url}")
    print("=======================================================\n")
    return video_id

def main():
    parser = argparse.ArgumentParser(description="YouTube Shorts Automated Uploader")
    parser.add_argument("--file", default="remotion/out/ccp_shorts.mp4", help="Video file path")
    parser.add_argument("--title", default=DEFAULT_TITLE, help="Video title")
    parser.add_argument("--description", default=DEFAULT_DESCRIPTION, help="Video description")
    parser.add_argument("--tags", default=",".join(DEFAULT_TAGS), help="Comma separated tags")
    parser.add_argument("--privacy", default="unlisted", choices=["public", "unlisted", "private"], help="Privacy status")
    parser.add_argument("--secrets", default="client_secret.json", help="OAuth client secret JSON")

    args = parser.parse_args()
    tags_list = [t.strip() for t in args.tags.split(",") if t.strip()]

    youtube = get_authenticated_service(args.secrets)
    if not youtube:
        sys.exit(1)

    upload_video(
        youtube,
        file_path=args.file,
        title=args.title,
        description=args.description,
        tags=tags_list,
        privacy_status=args.privacy
    )

if __name__ == "__main__":
    main()