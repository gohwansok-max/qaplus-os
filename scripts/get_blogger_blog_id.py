#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
블로그 URL로 Blogger Blog ID를 조회하는 스크립트 (API 키만 있으면 됨, OAuth 불필요).
사용법: python scripts/get_blogger_blog_id.py --api-key YOUR_API_KEY --url https://qaplus-haccp.blogspot.com/
"""
import argparse
import requests

parser = argparse.ArgumentParser()
parser.add_argument("--api-key", required=True, help="Google Cloud Console에서 발급받은 API 키")
parser.add_argument("--url", default="https://qaplus-haccp.blogspot.com/")
args = parser.parse_args()

resp = requests.get(
    "https://www.googleapis.com/blogger/v3/blogs/byurl",
    params={"url": args.url, "key": args.api_key},
    timeout=30,
)

if resp.status_code == 200:
    data = resp.json()
    print(f"\n[OK] Blog ID: {data.get('id')}")
    print(f"블로그 이름: {data.get('name')}")
    print(f"\n.env 또는 GitHub Secret에 아래처럼 등록하세요:")
    print(f"BLOGGER_BLOG_ID={data.get('id')}")
else:
    print(f"[!] 조회 실패: {resp.status_code} {resp.text}")
