#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blogger API 리프레시 토큰 최초 1회 발급 스크립트 — 반드시 로컬(본인 PC)에서 직접 실행하세요.
GitHub Actions나 다른 사람 서버에서 실행하면 안 됩니다 (본인 Google 계정 로그인이 필요함).

사전 준비 (Google Cloud Console에서 직접 진행):
  1. https://console.cloud.google.com/ 에서 새 프로젝트 생성 (또는 기존 프로젝트 사용)
  2. "API 및 서비스 > 라이브러리"에서 "Blogger API v3" 검색 후 사용 설정
  3. "API 및 서비스 > OAuth 동의 화면" 설정 (테스트 사용자에 본인 Google 계정 추가, User Type: 외부)
  4. "API 및 서비스 > 사용자 인증 정보 > 사용자 인증 정보 만들기 > OAuth 클라이언트 ID"
     - 애플리케이션 유형: "데스크톱 앱"
     - 생성된 클라이언트 ID / 클라이언트 보안 비밀을 아래 실행 시 입력하거나 .env에 미리 저장

사용법:
  python scripts/get_blogger_refresh_token.py

실행하면 브라우저가 열리고 Google 로그인 + 동의 화면이 나옵니다. 본인이 직접 로그인/승인하세요.
완료되면 터미널에 BLOGGER_REFRESH_TOKEN 값이 출력되고, .env 파일에 자동으로 추가할지 물어봅니다.
"""

import os
import sys
import json
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
REDIRECT_PORT = 8765
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/"
SCOPE = "https://www.googleapis.com/auth/blogger"
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
        pass  # 콘솔 출력 억제


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
    client_id = env.get("BLOGGER_CLIENT_ID") or input("Google OAuth 클라이언트 ID를 입력하세요: ").strip()
    client_secret = env.get("BLOGGER_CLIENT_SECRET") or input("Google OAuth 클라이언트 보안 비밀을 입력하세요: ").strip()

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
        print("[!] refresh_token이 응답에 없습니다. 이미 이 앱에 동의한 적이 있다면 Google 계정 설정에서")
        print("    '타사 앱 액세스'에서 이 앱 연결을 해제한 후 다시 시도해주세요 (access_type=offline이어도")
        print("    이미 승인된 앱은 refresh_token을 재발급하지 않는 경우가 있습니다).")
        sys.exit(1)

    print("\n========================================================")
    print("[OK] 리프레시 토큰 발급 성공!")
    print(f"BLOGGER_REFRESH_TOKEN={refresh_token}")
    print("========================================================\n")

    answer = input(".env 파일에 자동으로 저장할까요? (y/n): ").strip().lower()
    if answer == "y":
        lines = []
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
        lines = [l for l in lines if not l.startswith(("BLOGGER_CLIENT_ID=", "BLOGGER_CLIENT_SECRET=", "BLOGGER_REFRESH_TOKEN="))]
        lines.append(f"BLOGGER_CLIENT_ID={client_id}\n")
        lines.append(f"BLOGGER_CLIENT_SECRET={client_secret}\n")
        lines.append(f"BLOGGER_REFRESH_TOKEN={refresh_token}\n")
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"[OK] {ENV_PATH} 에 저장했습니다.")
        print("[!] BLOGGER_BLOG_ID는 별도로 .env에 추가해야 합니다 (블로그 ID 조회는 scripts/get_blogger_blog_id.py 참고).")
    else:
        print("[*] 위 값을 직접 .env 또는 GitHub Secrets에 등록해주세요.")


if __name__ == "__main__":
    main()
