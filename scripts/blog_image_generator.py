#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
큐에이플러스(QA+) 블로그 본문 이미지 실제 생성 + 호스팅 모듈.
- OpenAI Images API(DALL-E 3)로 이미지를 생성해 base64로 받아 로컬 파일로 저장.
- 저장한 이미지를 git commit + push해서 GitHub raw URL로 공개 접근 가능하게 만든다
  (Blogger API가 파일 업로드를 지원하지 않아, 이미 있는 git push 인프라를 이미지 호스팅으로 재사용).
"""

import os
import re
import json
import base64
import subprocess
import urllib.request
import urllib.parse
import urllib.error

GITHUB_REPO = "gohwansok-max/qaplus-os"
GITHUB_BRANCH = "main"


def _get_api_key():
    key = os.environ.get("OFFICIAL_OPENAI_API_KEY")
    if key and not key.startswith("your_"):
        return key
    return None


def generate_image_png(prompt, size="1024x1024"):
    """ OpenAI Images API(dall-e-3) 호출, 실패 시 None 반환 (예외를 던지지 않음 — 이미지 실패가 전체 파이프라인을 막으면 안 됨) """
    api_key = _get_api_key()
    if not api_key:
        print("[!] OFFICIAL_OPENAI_API_KEY가 없어 이미지 생성을 건너뜁니다.")
        return None

    payload = {
        "model": "gpt-image-2",
        "prompt": prompt[:4000],
        "n": 1,
        "size": size,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            b64 = data["data"][0]["b64_json"]
            return base64.b64decode(b64)
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8")
        print(f"[!] 이미지 생성 API 오류: {e.code} {err}")
        return None
    except Exception as e:
        print(f"[!] 이미지 생성 실패: {e}")
        return None


def extract_image_prompts(image_output_text):
    """ 03_image_agent.md 출력 규격에서 본문 이미지 1/2의 AI 프롬프트를 추출 """
    prompts = {}
    m1 = re.search(r"본문 이미지 1[\s\S]*?AI 이미지 프롬프트[^\n`]*[:：]\s*`([^`]+)`", image_output_text)
    m2 = re.search(r"본문 이미지 2[\s\S]*?AI 이미지 프롬프트[^\n`]*[:：]\s*`([^`]+)`", image_output_text)
    if m1:
        prompts["IMAGE_PLACEHOLDER_1"] = m1.group(1).strip()
    if m2:
        prompts["IMAGE_PLACEHOLDER_2"] = m2.group(1).strip()
    return prompts


def _git(args, cwd):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def commit_and_push_images(root_dir, file_paths):
    """ 새로 생성한 이미지 파일만 즉시 커밋 + 푸시해 raw.githubusercontent.com URL을 살린다 """
    rel_paths = [os.path.relpath(p, root_dir).replace("\\", "/") for p in file_paths]
    _git(["add"] + rel_paths, root_dir)
    commit = _git(["commit", "-m", "chore(auto): 블로그 본문 이미지 자동 생성"], root_dir)
    if commit.returncode != 0 and "nothing to commit" not in (commit.stdout + commit.stderr):
        print(f"[!] 이미지 커밋 실패: {commit.stderr}")
        return False
    push = _git(["push", "origin", f"HEAD:{GITHUB_BRANCH}"], root_dir)
    if push.returncode != 0:
        print(f"[!] 이미지 푸시 실패 (Blogger에는 GitHub raw URL이 아직 안 뜰 수 있음): {push.stderr}")
        return False
    return True


def generate_and_host_images(image_output_text, root_dir, dated_dir, safe_topic):
    """
    반환: {"IMAGE_PLACEHOLDER_1": "https://raw.githubusercontent.com/.../img1.png", ...}
    실패한 이미지는 딕셔너리에서 아예 빠진다 (호출부에서 플레이스홀더를 제거 처리).
    """
    prompts = extract_image_prompts(image_output_text)
    if not prompts:
        print("[!] 이미지 프롬프트를 추출하지 못했습니다.")
        return {}

    images_dir = os.path.join(dated_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    # 한글 파일명이 raw.githubusercontent.com에서 URL 인코딩 문제로 404가 나는 경우가 있어
    # 이미지 파일명은 순수 ASCII(해시)로만 만든다. 한글 주제명은 alt 텍스트에만 남긴다.
    import hashlib
    topic_hash = hashlib.md5(safe_topic.encode("utf-8")).hexdigest()[:10]

    saved_files = []
    urls = {}
    for idx, (placeholder, prompt) in enumerate(prompts.items(), start=1):
        print(f"[*] 이미지 생성 중 ({idx}/{len(prompts)}): {prompt[:60]}...")
        img_bytes = generate_image_png(prompt)
        if not img_bytes:
            continue
        filename = f"img{idx}_{topic_hash}.png"
        filepath = os.path.join(images_dir, filename)
        with open(filepath, "wb") as f:
            f.write(img_bytes)
        saved_files.append(filepath)
        rel = os.path.relpath(filepath, root_dir).replace("\\", "/")
        urls[placeholder] = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{urllib.parse.quote(rel)}"

    if saved_files:
        ok = commit_and_push_images(root_dir, saved_files)
        if not ok:
            print("[!] 이미지가 아직 GitHub에 반영되지 않아 Blogger에서 당장 안 보일 수 있습니다 (다음 push 때 해결됨).")

    return urls
