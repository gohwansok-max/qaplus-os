#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
큐에이플러스(QA+) Blogger 자동 임시저장/발행 모듈
- OAuth 리프레시 토큰으로 액세스 토큰을 발급받아 Blogger API v3(posts.insert)를 호출한다.
- 최초 1회, 로컬에서 scripts/get_blogger_refresh_token.py 로 리프레시 토큰을 발급받아야 한다.
"""

import os
import json
import requests

BLOGGER_API_BASE = "https://www.googleapis.com/blogger/v3"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


def get_access_token():
    """ 리프레시 토큰으로 새 액세스 토큰 발급 (매 실행마다 새로 발급 — 만료 걱정 없음) """
    client_id = os.environ.get("BLOGGER_CLIENT_ID")
    client_secret = os.environ.get("BLOGGER_CLIENT_SECRET")
    refresh_token = os.environ.get("BLOGGER_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        return None

    resp = requests.post(GOOGLE_TOKEN_URL, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }, timeout=30)

    if resp.status_code != 200:
        print(f"[!] Blogger 액세스 토큰 발급 실패: {resp.status_code} {resp.text}")
        return None

    return resp.json().get("access_token")


def is_configured():
    """ Blogger 자동 발행에 필요한 환경변수가 전부 있는지 확인 """
    required = ["BLOGGER_BLOG_ID", "BLOGGER_CLIENT_ID", "BLOGGER_CLIENT_SECRET", "BLOGGER_REFRESH_TOKEN"]
    return all(os.environ.get(k) for k in required)


def publish_post(title, html_content, labels=None, is_draft=True):
    """
    Blogger에 글을 올린다.
    is_draft=True  -> 임시저장 (사람이 최종 확인 후 발행 버튼만 누르면 됨, 기본값 — 안전)
    is_draft=False -> 즉시 공개 발행 (완전 자동화, 검수 없이 바로 공개됨)
    """
    blog_id = os.environ.get("BLOGGER_BLOG_ID")
    access_token = get_access_token()
    if not access_token:
        return {"ok": False, "error": "액세스 토큰 발급 실패 (환경변수 미설정 또는 리프레시 토큰 만료)"}

    url = f"{BLOGGER_API_BASE}/blogs/{blog_id}/posts/"
    if is_draft:
        url += "?isDraft=true"

    payload = {
        "kind": "blogger#post",
        "title": title,
        "content": html_content,
    }
    if labels:
        payload["labels"] = labels

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    if resp.status_code in (200, 201):
        data = resp.json()
        return {
            "ok": True,
            "post_id": data.get("id"),
            "url": data.get("url"),
            "status": "임시저장" if is_draft else "발행됨",
        }
    return {"ok": False, "error": f"{resp.status_code} {resp.text}"}


def list_draft_posts():
    """ 현재 블로그의 임시저장(draft) 글 목록을 가져온다 (제목으로 찾아 수정할 때 사용) """
    blog_id = os.environ.get("BLOGGER_BLOG_ID")
    access_token = get_access_token()
    if not access_token:
        return []
    resp = requests.get(
        f"{BLOGGER_API_BASE}/blogs/{blog_id}/posts",
        params={"status": "draft", "maxResults": 50},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"[!] 임시저장 목록 조회 실패: {resp.status_code} {resp.text}")
        return []
    return resp.json().get("items", [])


def update_post(post_id, title, html_content, labels=None, is_draft=True):
    """ 기존 글(post_id)을 새 내용으로 덮어쓴다 (이미지 수정 등 재작업용) """
    blog_id = os.environ.get("BLOGGER_BLOG_ID")
    access_token = get_access_token()
    if not access_token:
        return {"ok": False, "error": "액세스 토큰 발급 실패"}

    url = f"{BLOGGER_API_BASE}/blogs/{blog_id}/posts/{post_id}"
    payload = {"kind": "blogger#post", "title": title, "content": html_content}
    if labels:
        payload["labels"] = labels

    resp = requests.put(
        url,
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=60,
    )
    if resp.status_code == 200:
        data = resp.json()
        return {"ok": True, "post_id": data.get("id"), "url": data.get("url")}
    return {"ok": False, "error": f"{resp.status_code} {resp.text}"}


if __name__ == "__main__":
    if not is_configured():
        print("[!] BLOGGER_BLOG_ID / BLOGGER_CLIENT_ID / BLOGGER_CLIENT_SECRET / BLOGGER_REFRESH_TOKEN 환경변수가 필요합니다.")
    else:
        result = publish_post("테스트 글", "<p>Blogger API 연동 테스트입니다.</p>", is_draft=True)
        print(result)
