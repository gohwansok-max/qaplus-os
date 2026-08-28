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
import re
import requests

YOUTUBE_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


def _clean_topic(topic):
    """큐 ID를 제거하고 검색 결과에서 읽기 쉬운 주제명으로 정리한다."""
    cleaned = re.sub(r"^[A-Z]{2,5}\d{3}\s+", "", str(topic or "").strip())
    replacements = {
        "구분과적용": "구분과 적용",
        "기대와현실": "기대와 현실",
        "개념과효과": "개념과 효과",
        "도입효과": "도입 효과",
    }
    for before, after in replacements.items():
        cleaned = cleaned.replace(before, after)
    return re.sub(r"\s+", " ", cleaned).strip() or "HACCP 현장 실무"


def _search_intent(topic):
    """주제를 실무자가 검색할 가능성이 높은 롱테일 검색 의도로 분류한다."""
    lowered = topic.lower()
    if "fssc" in lowered or any(k in topic for k in ("PRP", "OPRP")):
        return "FSSC 22000 실무", ["FSSC22000", "PRP", "OPRP"]
    if "스마트" in topic or any(k in lowered for k in ("iot", "센서", "자동기록", "위변조")):
        return "스마트 HACCP", ["스마트HACCP", "스마트해썹", "HACCP도입"]
    if any(k in topic for k in ("기준서", "절차서", "SOP", "작성법", "서식")):
        return "HACCP 기준서 작성법", ["HACCP기준서", "해썹기준서", "HACCP서식"]
    if any(k in topic for k in ("심사", "인증", "지적", "부적합", "개선조치", "CAPA")):
        return "HACCP 심사 대비", ["HACCP심사", "해썹인증", "HACCP인증절차"]
    if any(k in topic for k in ("위생", "세척", "손세척", "방진복", "알레르", "교차오염", "ATP")):
        return "식품공장 위생점검", ["식품공장위생", "위생점검", "위생관리"]
    if any(k in topic for k in ("CCP", "한계기준", "가열", "살균", "냉각", "금속검출", "이물")):
        return "HACCP CCP 관리", ["CCP관리", "한계기준", "HACCP모니터링"]
    return "HACCP 실무", ["HACCP실무", "해썹", "식품품질관리"]


def _fit_title(prefix, topic, limit=100):
    suffix = " | 큐에이플러스"
    available = limit - len(prefix) - len(suffix) - 1
    if available < 10:
        suffix = ""
        available = limit - len(prefix) - 1
    shortened = topic if len(topic) <= available else topic[: max(1, available - 1)].rstrip() + "…"
    return f"{prefix} {shortened}{suffix}"[:limit]


def build_short_metadata(topic, scenes=None):
    """영상별 검색 의도에 맞는 제목·설명·태그를 결정론적으로 생성한다.

    제목과 설명 첫 문단에는 동일한 핵심 검색어를 자연스럽게 배치하고,
    태그는 오탈자 및 동의어 보완 용도로만 제한한다.
    """
    clean_topic = _clean_topic(topic)
    primary_keyword, intent_tags = _search_intent(clean_topic)
    title = _fit_title(f"[{primary_keyword}]", clean_topic)

    highlights = []
    for scene in scenes or []:
        candidate = str(scene.get("subtitle") or scene.get("title") or "").replace("\n", " ").strip()
        candidate = re.sub(r"\s+", " ", candidate)
        if candidate and candidate not in highlights:
            highlights.append(candidate[:80])
        if len(highlights) == 3:
            break

    description_lines = [
        f"{primary_keyword} 정보를 찾는 실무자를 위한 ‘{clean_topic}’ 핵심 정리입니다.",
        "HACCP 인증·심사와 식품 품질관리 현장에서 바로 확인할 점검 포인트를 20년 QA 실무 관점으로 설명합니다.",
    ]
    if highlights:
        description_lines.extend(["", "영상 핵심:"] + [f"- {item}" for item in highlights])
    description_lines.extend([
        "",
        "큐에이플러스는 HACCP·FSSC 22000·식품 품질관리 실무 지식을 무료로 나눕니다.",
        "",
        "#HACCP #해썹 #식품품질관리 #Shorts",
    ])

    tags = [
        "HACCP", "해썹", "HACCP인증", "HACCP심사", "식품품질관리",
        "품질관리", "식품QA", "식품QC", "식품안전", "큐에이플러스",
        *intent_tags, clean_topic, "Shorts",
    ]
    unique_tags = []
    for tag in tags:
        normalized = str(tag).strip()
        if normalized and normalized.casefold() not in {t.casefold() for t in unique_tags}:
            unique_tags.append(normalized[:100])

    while len(",".join(unique_tags)) > 450:
        unique_tags.pop()

    return {
        "title": title,
        "description": "\n".join(description_lines)[:5000],
        "tags": unique_tags,
        "primary_keyword": primary_keyword,
        "topic": clean_topic,
    }


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
    설명에 #Shorts를 포함하되, 검색 적합도는 정확한 제목·설명·영상 내용으로 확보한다.
    """
    if not os.path.exists(video_path):
        return {"ok": False, "error": f"영상 파일을 찾을 수 없습니다: {video_path}"}

    access_token = get_access_token()
    if not access_token:
        return {"ok": False, "error": "액세스 토큰 발급 실패 (환경변수 미설정 또는 리프레시 토큰 만료)"}

    if "#shorts" not in title.lower() and "#shorts" not in description.lower():
        description = f"{description}\n\n#Shorts #HACCP #해썹 #식품품질관리"

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
