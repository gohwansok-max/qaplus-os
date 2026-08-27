#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube 업로드용 리프레시 토큰 최초 1회 발급 스크립트 — 반드시 로컬(본인 PC)에서 직접 실행하세요.

사전 준비 (Google Cloud Console, Blogger 때 만든 'qaplus-blog' 프로젝트 재사용):
  1. https://console.cloud.google.com/apis/library/youtube.googleapis.com?project=qaplus-blog
     에서 "YouTube Data API v3" 사용 설정
  2. OAuth 클라이언트는 Blogger 때 만든 걸 그대로 씁니다 (.env의 BLOGGER_CLIENT_ID/SECRET) — 새로 안 만들어도 됨

사용법:
  python scripts/get_youtube_refresh_token.py

실행하면 브라우저가 열리고 Google 로그인 + 동의 화면이 나옵니다. 본인이 직접 로그인/승인하세요.
완료되면 터미널에 YOUTUBE_REFRESH_TOKEN 값이 출력되고, .env 파일에 자동으로 추가할지 물어봅니다.
"""

import os
import sys
import webbrowser
import urllib.parse
import http.server
import socketserver
import threading
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT_DIR, ".env")
REDIRECT_PORT = 8766  # Blogger 스크립트(8765)와 겹치지 않게 다른 포트 사용
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/"
SCOPE = "https://www.googleapis.com/auth/youtube.upload"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

_received_code = {"code": None}


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        if "code" in params:
            _received_code["code"] = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>인증 완료! 이 창은 닫으셔도 됩니다.</h2>".encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def load_env():
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def main():
    env = load_env()
    # Blogger 때 만든 OAuth 클라이언트를 재사용 (YOUTUBE_CLIENT_ID가 따로 있으면 그걸 우선)
    client_id = env.get("YOUTUBE_CLIENT_ID") or env.get("BLOGGER_CLIENT_ID") or input("Google OAuth 클라이언트 ID를 입력하세요: ").strip()
    client_secret = env.get("YOUTUBE_CLIENT_SECRET") or env.get("BLOGGER_CLIENT_SECRET") or input("Google OAuth 클라이언트 보안 비밀을 입력하세요: ").strip()

    auth_params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(auth_params)}"

    print(f"\n[*] 브라우저를 엽니다. 열리지 않으면 아래 URL을 직접 여세요:\n{url}\n")
    webbrowser.open(url)

    server = socketserver.TCPServer(("localhost", REDIRECT_PORT), _CallbackHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.start()
    thread.join(timeout=180)
    server.server_close()

    code = _received_code["code"]
    if not code:
        print("[!] 인증 코드를 받지 못했습니다 (3분 타임아웃 또는 취소됨). 다시 시도해주세요.")
        sys.exit(1)

    resp = requests.post(TOKEN_URL, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }, timeout=30)

    if resp.status_code != 200:
        print(f"[!] 토큰 발급 실패: {resp.status_code} {resp.text}")
        sys.exit(1)

    tokens = resp.json()
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        print("[!] refresh_token이 응답에 없습니다. Google 계정 설정 > 타사 앱 액세스에서 이 앱 연결을")
        print("    해제한 후 다시 시도해주세요.")
        sys.exit(1)

    print("\n========================================================")
    print("[OK] YouTube 리프레시 토큰 발급 성공!")
    print(f"YOUTUBE_REFRESH_TOKEN={refresh_token}")
    print("========================================================\n")

    answer = input(".env 파일에 자동으로 저장할까요? (y/n): ").strip().lower()
    if answer == "y":
        lines = []
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
        lines = [l for l in lines if not l.startswith("YOUTUBE_REFRESH_TOKEN=")]
        lines.append(f"YOUTUBE_REFRESH_TOKEN={refresh_token}\n")
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"[OK] {ENV_PATH} 에 저장했습니다.")
    else:
        print("[*] 위 값을 직접 .env 또는 GitHub Secrets에 등록해주세요.")


if __name__ == "__main__":
    main()
