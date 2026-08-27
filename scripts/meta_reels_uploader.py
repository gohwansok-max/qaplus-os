#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
큐에이플러스(QA+) 페이스북 릴스 + 인스타그램 릴스 자동 업로드 모듈 (Meta Graph API)

- 페이스북: 리졸버블 업로드로 파일을 직접 전송 (POST /{page-id}/video_reels)
- 인스타그램: Graph API는 파일 직접 업로드가 아니라 "공개적으로 접근 가능한 video_url"을 요구하므로,
  블로그 이미지 때와 동일한 방식으로 GitHub raw URL을 이용해 업로드한다.
  (git_push_helper.push_and_get_raw_url 로 영상을 먼저 깃허브에 올리고, 그 URL을 IG에 넘김)

필요 환경변수:
  META_PAGE_ACCESS_TOKEN  — 장기 페이지 액세스 토큰 (만료 없음)
  META_PAGE_ID            — 페이스북 페이지 ID
  META_IG_USER_ID         — 페이지에 연결된 인스타그램 비즈니스 계정 ID
"""

import os
import time
import requests

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


def is_facebook_configured():
    return bool(os.environ.get("META_PAGE_ACCESS_TOKEN") and os.environ.get("META_PAGE_ID"))


def is_instagram_configured():
    return bool(
        os.environ.get("META_PAGE_ACCESS_TOKEN")
        and os.environ.get("META_IG_USER_ID")
    )


def upload_facebook_reel(video_path, description):
    """ 페이스북 페이지에 릴스로 업로드 (파일 직접 업로드, resumable) """
    page_id = os.environ.get("META_PAGE_ID")
    token = os.environ.get("META_PAGE_ACCESS_TOKEN")
    if not page_id or not token:
        return {"ok": False, "error": "META_PAGE_ID / META_PAGE_ACCESS_TOKEN 환경변수가 필요합니다."}

    file_size = os.path.getsize(video_path)

    # 1단계: 업로드 세션 시작
    start_resp = requests.post(
        f"{GRAPH_API_BASE}/{page_id}/video_reels",
        data={"upload_phase": "start", "access_token": token},
        timeout=30,
    )
    if start_resp.status_code != 200:
        return {"ok": False, "error": f"세션 시작 실패: {start_resp.status_code} {start_resp.text[:300]}"}
    start_data = start_resp.json()
    video_id = start_data.get("video_id")
    upload_url = start_data.get("upload_url")
    if not video_id or not upload_url:
        return {"ok": False, "error": f"세션 응답에 video_id/upload_url 없음: {start_data}"}

    # 2단계: 실제 파일 업로드
    with open(video_path, "rb") as f:
        video_data = f.read()
    upload_resp = requests.post(
        upload_url,
        headers={
            "Authorization": f"OAuth {token}",
            "offset": "0",
            "file_size": str(file_size),
        },
        data=video_data,
        timeout=300,
    )
    if upload_resp.status_code != 200:
        return {"ok": False, "error": f"파일 업로드 실패: {upload_resp.status_code} {upload_resp.text[:300]}"}

    # 3단계: 게시 완료 처리
    publish_resp = requests.post(
        f"{GRAPH_API_BASE}/{page_id}/video_reels",
        data={
            "upload_phase": "finish",
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": description[:2200],
            "access_token": token,
        },
        timeout=30,
    )
    if publish_resp.status_code == 200 and publish_resp.json().get("success"):
        return {"ok": True, "video_id": video_id, "url": f"https://www.facebook.com/reel/{video_id}"}
    return {"ok": False, "error": f"게시 완료 처리 실패: {publish_resp.status_code} {publish_resp.text[:300]}"}


def upload_instagram_reel(video_public_url, caption, max_wait_seconds=180):
    """ 인스타그램 비즈니스 계정에 릴스로 업로드. video_public_url은 외부에서 접근 가능한 mp4 URL이어야 함
    (git_push_helper로 미리 GitHub raw URL을 만들어서 넘길 것). """
    ig_user_id = os.environ.get("META_IG_USER_ID")
    token = os.environ.get("META_PAGE_ACCESS_TOKEN")
    if not ig_user_id or not token:
        return {"ok": False, "error": "META_IG_USER_ID / META_PAGE_ACCESS_TOKEN 환경변수가 필요합니다."}

    # 1단계: 미디어 컨테이너 생성
    create_resp = requests.post(
        f"{GRAPH_API_BASE}/{ig_user_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_public_url,
            "caption": caption[:2200],
            "access_token": token,
        },
        timeout=30,
    )
    if create_resp.status_code != 200:
        return {"ok": False, "error": f"컨테이너 생성 실패: {create_resp.status_code} {create_resp.text[:300]}"}
    container_id = create_resp.json().get("id")
    if not container_id:
        return {"ok": False, "error": f"컨테이너 ID 없음: {create_resp.text[:300]}"}

    # 2단계: 컨테이너 처리 완료(FINISHED) 될 때까지 폴링 (인스타그램이 영상을 내려받아 처리하는 시간 필요)
    waited = 0
    while waited < max_wait_seconds:
        status_resp = requests.get(
            f"{GRAPH_API_BASE}/{container_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=30,
        )
        status_code = status_resp.json().get("status_code")
        if status_code == "FINISHED":
            break
        if status_code == "ERROR":
            return {"ok": False, "error": f"컨테이너 처리 실패(ERROR): {status_resp.text[:300]}"}
        time.sleep(10)
        waited += 10
    else:
        return {"ok": False, "error": f"컨테이너 처리 시간 초과({max_wait_seconds}초). 나중에 수동으로 게시해야 할 수 있습니다."}

    # 3단계: 게시
    publish_resp = requests.post(
        f"{GRAPH_API_BASE}/{ig_user_id}/media_publish",
        data={"creation_id": container_id, "access_token": token},
        timeout=30,
    )
    if publish_resp.status_code == 200:
        media_id = publish_resp.json().get("id")
        return {"ok": True, "media_id": media_id}
    return {"ok": False, "error": f"게시 실패: {publish_resp.status_code} {publish_resp.text[:300]}"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="QA+ Meta(FB/IG) Reels Uploader")
    parser.add_argument("--platform", choices=["facebook", "instagram"], required=True)
    parser.add_argument("--video", help="로컬 파일 경로 (facebook용)")
    parser.add_argument("--video-url", help="공개 접근 가능한 영상 URL (instagram용)")
    parser.add_argument("--caption", default="")
    args = parser.parse_args()

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    if args.platform == "facebook":
        print(upload_facebook_reel(args.video, args.caption))
    else:
        print(upload_instagram_reel(args.video_url, args.caption))
