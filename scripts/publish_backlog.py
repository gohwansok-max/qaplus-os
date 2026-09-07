#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
큐에이플러스(QA+) Blogger 발행 백로그 정리 스크립트
- Blogger 리프레시 토큰이 만료돼있던 동안 status가 "ready_to_publish"로 남은
  outputs/**/blog_log.json 항목을 찾아 지금 살아있는 토큰으로 한 번에 발행한다.
- 정상적으로 매일 도는 generate_blog.py와 달리 새 글을 만들지 않고,
  이미 생성된 [블로그최종]_*.html 파일 내용을 그대로 Blogger에 올린다.
"""

import os
import sys
import re
import json
import glob
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blogger_publisher import is_configured, publish_post

try:
    from telegram_sender import send_message_to_telegram
except Exception:
    def send_message_to_telegram(message):
        print("[!] telegram_sender 모듈을 불러오지 못해 텔레그램 발송을 건너뜁니다.")
        return False

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLISH_INTERVAL_SEC = 10  # Blogger API가 짧은 시간에 몰아치면 429(rateLimitExceeded)를 반환해서 글 사이 최소 간격을 둔다.
RATE_LIMIT_RETRIES = 3
RATE_LIMIT_BACKOFF_SEC = 30


def publish_with_retry(title, body_html, is_draft):
    """ 429(rateLimitExceeded)만 백오프 후 재시도하고, 그 외 오류는 즉시 실패 처리한다. """
    for attempt in range(1, RATE_LIMIT_RETRIES + 1):
        result = publish_post(title, body_html, is_draft=is_draft)
        if result.get("ok") or "429" not in str(result.get("error", "")):
            return result
        if attempt < RATE_LIMIT_RETRIES:
            wait = RATE_LIMIT_BACKOFF_SEC * attempt
            print(f"[!] 429 rate limit — {wait}초 대기 후 재시도 ({attempt}/{RATE_LIMIT_RETRIES})")
            time.sleep(wait)
    return result


def strip_leading_comments(html_text):
    """ generate_blog.py가 파일 맨 위에 붙이는 <!-- 제목: ... --> 등 메타 주석을 제거하고
    실제 본문(<article ...>부터)만 돌려준다. """
    return re.sub(r'^(\s*<!--.*?-->\s*)+', '', html_text, flags=re.DOTALL).strip()


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def main():
    if not is_configured():
        print("[!] BLOGGER_* 환경변수가 설정되어 있지 않습니다. 발행 백로그 처리를 중단합니다.")
        send_message_to_telegram(
            "🚨 <b>[QA+] 발행 백로그 처리 실패</b>\n\nBLOGGER_* 시크릿이 설정되지 않아 진행할 수 없습니다."
        )
        sys.exit(1)

    log_paths = sorted(glob.glob(os.path.join(ROOT_DIR, "outputs", "*", "*", "*", "blog_log.json")))

    is_draft = os.environ.get("BLOGGER_AUTO_PUBLISH", "false").lower() != "true"
    results = []

    for log_path in log_paths:
        blog_log = load_json(log_path, [])
        changed = False

        for entry in blog_log:
            if entry.get("status") != "ready_to_publish":
                continue

            html_path = os.path.join(ROOT_DIR, entry["file"])
            if not os.path.exists(html_path):
                print(f"[!] 파일을 찾을 수 없어 건너뜁니다: {html_path}")
                continue

            with open(html_path, "r", encoding="utf-8") as f:
                body_html = strip_leading_comments(f.read())

            title = entry["title"]
            print(f"[*] 발행 시도: {title}")
            if results:
                time.sleep(PUBLISH_INTERVAL_SEC)
            result = publish_with_retry(title, body_html, is_draft)

            if result.get("ok"):
                entry["status"] = f"blogger_{result['status']}"
                entry["blogger_url"] = result.get("url")
                entry["blogger_post_id"] = result.get("post_id")
                changed = True
                print(f"[OK] {result['status']}: {result.get('url')}")
                results.append({"title": title, "ok": True, "url": result.get("url")})
            else:
                print(f"[!] 발행 실패: {result.get('error')}")
                results.append({"title": title, "ok": False, "error": result.get("error")})

        if changed:
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(blog_log, f, ensure_ascii=False, indent=2)

    if not results:
        print("[*] ready_to_publish 상태인 글이 없습니다. 처리할 백로그가 없습니다.")
        send_message_to_telegram("✅ <b>[QA+] 발행 백로그 없음</b>\n\n처리할 미발행 글이 없습니다.")
        return

    ok_lines = [f"✅ {r['title']}\n{r['url']}" for r in results if r["ok"]]
    fail_lines = [f"❌ {r['title']} — {r['error']}" for r in results if not r["ok"]]
    tg_message = f"📦 <b>[QA+] 발행 백로그 {len(results)}건 처리 완료</b>\n\n"
    if ok_lines:
        tg_message += "\n\n".join(ok_lines)
    if fail_lines:
        tg_message += "\n\n" + "\n".join(fail_lines)
    send_message_to_telegram(tg_message)

    if any(not r["ok"] for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
