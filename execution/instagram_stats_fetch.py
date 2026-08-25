#!/usr/bin/env python3
"""
instagram_stats_fetch.py — 인스타그램 Graph API 통계 수집 템플릿

목적:
  릴스/게시물 성과 데이터를 AI가 참조할 수 있는 파일로 저장.
  Zero-Inference Rule — AI는 이 결과만 인용, 직접 계산 금지.

전제 조건 (수강생이 채워야 하는 것):
  1. Meta Business 계정 + 인스타그램 비즈니스/크리에이터 전환
  2. Facebook 페이지 연동
  3. Graph API 액세스 토큰 발급 (Meta for Developers)
  4. .env 파일에 아래 변수 설정:

     IG_ACCESS_TOKEN=EAAG...
     IG_BUSINESS_ACCOUNT_ID=17841400000000000

사용법:
  python execution/instagram_stats_fetch.py [--days 7]
  → knowledge/channel-data/instagram_YYYYMMDD.json 저장

주의:
  이 스크립트는 **템플릿**입니다. 실제 요청은 Meta 정책에 따라 제한이 있으며,
  rate limit, 토큰 만료, 권한 부족 등을 만나면 Meta 공식 문서 참조:
  https://developers.facebook.com/docs/instagram-api
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests  # pip install requests
except ImportError:
    print("[오류] requests 패키지가 필요합니다: pip install requests", file=sys.stderr)
    sys.exit(1)


GRAPH_API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def load_env() -> tuple[str, str]:
    """환경변수 로드. .env 파일이 있으면 그것도 시도."""
    access_token = os.getenv("IG_ACCESS_TOKEN")
    account_id = os.getenv("IG_BUSINESS_ACCOUNT_ID")

    if not access_token or not account_id:
        env_file = Path(".env")
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("IG_ACCESS_TOKEN=") and not access_token:
                    access_token = line.split("=", 1)[1].strip()
                elif line.startswith("IG_BUSINESS_ACCOUNT_ID=") and not account_id:
                    account_id = line.split("=", 1)[1].strip()

    if not access_token or not account_id:
        print(
            "[오류] IG_ACCESS_TOKEN / IG_BUSINESS_ACCOUNT_ID 환경변수가 필요합니다.\n"
            "       .env 파일 또는 쉘 환경변수로 설정하세요.",
            file=sys.stderr,
        )
        sys.exit(1)

    return access_token, account_id


def fetch_account_insights(account_id: str, token: str, days: int = 7) -> dict:
    """계정 단위 인사이트 (팔로워/도달/프로필 방문)."""
    url = f"{BASE_URL}/{account_id}/insights"
    since = int((datetime.now() - timedelta(days=days)).timestamp())
    until = int(datetime.now().timestamp())

    params = {
        "metric": "reach,impressions,profile_views,follower_count",
        "period": "day",
        "since": since,
        "until": until,
        "access_token": token,
    }

    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code != 200:
        print(f"[경고] 계정 인사이트 실패 ({resp.status_code}): {resp.text}", file=sys.stderr)
        return {"error": resp.text}
    return resp.json()


def fetch_recent_media(account_id: str, token: str, limit: int = 25) -> list[dict]:
    """최근 게시물 목록."""
    url = f"{BASE_URL}/{account_id}/media"
    params = {
        "fields": "id,caption,media_type,permalink,timestamp,like_count,comments_count",
        "limit": limit,
        "access_token": token,
    }
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code != 200:
        print(f"[경고] 미디어 목록 실패 ({resp.status_code}): {resp.text}", file=sys.stderr)
        return []
    return resp.json().get("data", [])


def fetch_media_insights(media_id: str, token: str) -> dict:
    """개별 게시물 인사이트 (릴스: plays, 사진: reach 등 media_type에 따라 상이)."""
    url = f"{BASE_URL}/{media_id}/insights"
    params = {
        "metric": "reach,impressions,saved,likes,comments,shares,plays",
        "access_token": token,
    }
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code != 200:
        return {}
    return {item["name"]: item["values"][0]["value"] for item in resp.json().get("data", [])}


def main() -> None:
    days = 7
    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        days = int(sys.argv[idx + 1])

    token, account_id = load_env()

    print(f"[정보] 인스타그램 통계 수집 시작 (최근 {days}일)")

    account = fetch_account_insights(account_id, token, days)
    media_list = fetch_recent_media(account_id, token)

    enriched = []
    for m in media_list:
        insights = fetch_media_insights(m["id"], token)
        enriched.append({**m, "insights": insights})

    output = {
        "fetched_at": datetime.now().isoformat(),
        "period_days": days,
        "account_insights": account,
        "media_count": len(enriched),
        "media": enriched,
    }

    out_dir = Path("knowledge/channel-data")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"instagram_{datetime.now().strftime('%Y%m%d')}.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[완료] {out_path} 저장 (게시물 {len(enriched)}건)")
    print(f"[참고] 김이사는 이 파일의 숫자만 인용할 것. 추정 금지 (Zero-Inference)")


if __name__ == "__main__":
    main()
