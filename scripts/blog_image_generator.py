#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QA+ 블로그 글마다 고유한 AI 대표 이미지를 생성·저장한다."""

import base64
import hashlib
import os
import re
from pathlib import Path
from urllib.parse import quote

import requests


def _prompt(image_plan, safe_topic):
    """글 주제와 시각자료 기획을 반영한 한국 식품 제조 현장 대표 이미지 프롬프트."""
    plan = re.sub(r"\s+", " ", image_plan or "").strip()[:1800]
    return f"""Create one unique 16:9 photorealistic DSLR documentary cover image for a Korean food quality-management blog article.
Topic: {safe_topic}
Image direction: {plan}
Show a realistic Korean food manufacturing quality-management or QA standardization scene that directly supports this topic. Use a glossy green epoxy factory floor, naturally worn stainless-steel equipment, bright 5000-5600K LED lighting, and Korean workers only if needed, in clean hooded coveralls, masks, and gloves with faces fully obscured. Use a distinctly different composition, camera angle, equipment arrangement, and scene from prior images. No people are required.
No text, letters, numbers, labels, logos, watermark, infographic, illustration, cartoon, CGI, 3D render, showroom, futuristic laboratory, or identifiable faces. No bare hands or hygiene violations."""


def _extract_image(data):
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"]), inline.get("mimeType", "image/png")
    raise RuntimeError("Gemini 이미지 응답에서 이미지 데이터를 찾지 못했습니다.")


def generate_and_host_images(image_output_text, root_dir, dated_dir, safe_topic):
    """Gemini 이미지 모델로 고유 대표 이미지를 생성하고 GitHub raw URL을 반환한다.
    Gemini 할당량 초과(429) 또는 실패 시 무료 SVG 이미지로 자동 대체한다."""
    import html as _html
    import hashlib
    import subprocess
    import urllib.parse

    GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY", "gohwansok-max/qaplus-os")
    GITHUB_BRANCH = os.environ.get("GITHUB_REF_NAME", "main")

    images_dir = os.path.join(dated_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    topic_hash = hashlib.md5(safe_topic.encode("utf-8")).hexdigest()[:10]

    def _make_svg(title, index):
        colors = [("#123B5D", "#E8F4FA"), ("#1E5B45", "#EAF7F0"), ("#6A4526", "#FFF4E6")]
        bg, accent = colors[(index - 1) % len(colors)]
        safe = _html.escape(title[:90])
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675">
<rect width="1200" height="675" fill="{accent}"/><rect x="0" y="0" width="1200" height="18" fill="{bg}"/>
<circle cx="1050" cy="120" r="150" fill="{bg}" opacity=".12"/><circle cx="1100" cy="520" r="220" fill="{bg}" opacity=".08"/>
<text x="90" y="150" font-family="Arial,sans-serif" font-size="30" fill="{bg}" font-weight="bold">QA PLUS | FOOD QUALITY</text>
<text x="90" y="285" font-family="Arial,sans-serif" font-size="48" fill="{bg}" font-weight="bold">{safe}</text>
<rect x="90" y="360" width="420" height="8" rx="4" fill="{bg}" opacity=".7"/>
<text x="90" y="455" font-family="Arial,sans-serif" font-size="28" fill="{bg}">실무자를 위한 품질관리 콘텐츠</text>
</svg>'''.encode("utf-8")

    def _git(args):
        return subprocess.run(["git"] + args, cwd=root_dir, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")

    def _save_svg_and_url(index):
        filepath = os.path.join(images_dir, f"img{index}_{topic_hash}.svg")
        with open(filepath, "wb") as f:
            f.write(_make_svg(safe_topic, index))
        rel = os.path.relpath(filepath, root_dir).replace("\\", "/")
        url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{urllib.parse.quote(rel)}"
        return filepath, url

    # --- 1. Gemini 이미지 생성 시도 ---
    api_key = os.environ.get("GEMINI_API_KEY")
    model = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
    gemini_ok = False

    if api_key:
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": _prompt(image_output_text, safe_topic)}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
        }
        for attempt in range(2):
            try:
                response = requests.post(gemini_url, json=payload, timeout=120)
                if response.status_code == 429:
                    print(f"[!] Gemini 이미지 할당량 초과(429) — SVG 폴백으로 전환")
                    break
                if response.status_code != 200:
                    raise RuntimeError(f"Gemini 이미지 생성 HTTP {response.status_code}: {response.text[:300]}")
                image_bytes, mime_type = _extract_image(response.json())
                ext = ".jpg" if "jpeg" in mime_type.lower() else ".png"
                digest = hashlib.sha256(image_bytes).hexdigest()[:12]
                images_dir_path = Path(dated_dir) / "images"
                images_dir_path.mkdir(parents=True, exist_ok=True)
                filename = f"cover_{digest}{ext}"
                local_path = images_dir_path / filename
                local_path.write_bytes(image_bytes)
                relative = local_path.relative_to(root_dir).as_posix()
                raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{quote(relative)}"
                print(f"[OK] 고유 AI 대표 이미지 생성: {relative}")
                gemini_ok = True
                return {"IMAGE_PLACEHOLDER_1": raw_url}
            except Exception as exc:
                print(f"[!] 대표 이미지 생성 {attempt + 1}/2 실패: {exc}")

    # --- 2. SVG 폴백 (Gemini 실패 또는 할당량 초과 시) ---
    print(f"[*] SVG 대체 이미지 생성 중 (Gemini 불가)...")
    saved_files = []
    urls = {}
    filepath, url = _save_svg_and_url(1)
    saved_files.append(filepath)
    urls["IMAGE_PLACEHOLDER_1"] = url

    if saved_files:
        rels = [os.path.relpath(p, root_dir).replace("\\", "/") for p in saved_files]
        _git(["add"] + rels)
        commit = _git(["commit", "-m", "chore(auto): SVG 대표 이미지 자동 생성"])
        if commit.returncode != 0 and "nothing to commit" not in (commit.stdout + commit.stderr):
            print(f"[!] 이미지 커밋 실패: {commit.stderr}")
        else:
            push = _git(["push", "origin", f"HEAD:{GITHUB_BRANCH}"])
            if push.returncode != 0:
                print(f"[!] 이미지 푸시 실패: {push.stderr}")
    print(f"[OK] SVG 대표 이미지 생성 완료")
    return urls























































