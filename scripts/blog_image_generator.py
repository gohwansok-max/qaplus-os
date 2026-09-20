#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""무료 로컬 SVG 이미지 생성기. OpenAI Images API를 호출하지 않는다."""
import os
import subprocess
import urllib.parse
import hashlib
import html

GITHUB_REPO = "gohwansok-max/qaplus-os"
GITHUB_BRANCH = "main"

def extract_image_prompts(image_output_text):
    prompts = {}
    lines = image_output_text.splitlines()
    current = None
    for line in lines:
        if line.startswith("본문 이미지 "):
            try:
                current = int(line.split()[2])
            except Exception:
                current = None
        elif current in (1, 2, 3) and "AI 이미지 프롬프트" in line:
            text = line.split(":", 1)[-1].strip().strip("`")
            prompts[f"IMAGE_PLACEHOLDER_{current}"] = text
            current = None
    return prompts

def _git(args, cwd):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")

def commit_and_push_images(root_dir, file_paths):
    rel_paths = [os.path.relpath(p, root_dir).replace(chr(92), "/") for p in file_paths]
    _git(["add"] + rel_paths, root_dir)
    commit = _git(["commit", "-m", "chore(auto): 무료 SVG 블로그 이미지 생성"], root_dir)
    if commit.returncode != 0 and "nothing to commit" not in (commit.stdout + commit.stderr):
        print(f"[!] 이미지 커밋 실패: {commit.stderr}")
        return False
    push = _git(["push", "origin", f"HEAD:{GITHUB_BRANCH}"], root_dir)
    if push.returncode != 0:
        print(f"[!] 이미지 푸시 실패: {push.stderr}")
        return False
    return True

def _make_svg(title, index):
    colors = [("#123B5D", "#E8F4FA"), ("#1E5B45", "#EAF7F0"), ("#6A4526", "#FFF4E6")]
    bg, accent = colors[(index - 1) % len(colors)]
    safe = html.escape(title[:90])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675">
<rect width="1200" height="675" fill="{accent}"/><rect x="0" y="0" width="1200" height="18" fill="{bg}"/>
<circle cx="1050" cy="120" r="150" fill="{bg}" opacity=".12"/><circle cx="1100" cy="520" r="220" fill="{bg}" opacity=".08"/>
<text x="90" y="150" font-family="Arial,sans-serif" font-size="30" fill="{bg}" font-weight="bold">QA PLUS | FOOD QUALITY</text>
<text x="90" y="285" font-family="Arial,sans-serif" font-size="48" fill="{bg}" font-weight="bold">{safe}</text>
<rect x="90" y="360" width="420" height="8" rx="4" fill="{bg}" opacity=".7"/>
<text x="90" y="455" font-family="Arial,sans-serif" font-size="28" fill="{bg}">실무자를 위한 품질관리 콘텐츠</text>
<text x="90" y="565" font-family="Arial,sans-serif" font-size="22" fill="{bg}" opacity=".8">무료 로컬 SVG 이미지</text>
</svg>'''.encode("utf-8")

def generate_and_host_images(image_output_text, root_dir, dated_dir, safe_topic):
    prompts = extract_image_prompts(image_output_text)
    if not prompts:
        print("[!] 이미지 프롬프트를 찾지 못했습니다.")
        return {}
    images_dir = os.path.join(dated_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    topic_hash = hashlib.md5(safe_topic.encode("utf-8")).hexdigest()[:10]
    saved_files, urls = [], {}
    for idx, (placeholder, prompt) in enumerate(prompts.items(), start=1):
        print(f"[*] 무료 SVG 이미지 생성 중 ({idx}/{len(prompts)})")
        filepath = os.path.join(images_dir, f"img{idx}_{topic_hash}.svg")
        with open(filepath, "wb") as f:
            f.write(_make_svg(prompt, idx))
        saved_files.append(filepath)
        rel = os.path.relpath(filepath, root_dir).replace(chr(92), "/")
        urls[placeholder] = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{urllib.parse.quote(rel)}"
    if saved_files:
        commit_and_push_images(root_dir, saved_files)
    return urls
