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
    """Gemini 이미지 모델로 고유 대표 이미지를 생성하고 GitHub raw URL을 반환한다."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY가 없어 대표 이미지를 생성할 수 없습니다.")

    model = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": _prompt(image_output_text, safe_topic)}]}], "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}}

    last_error = None
    for attempt in range(2):
        try:
            response = requests.post(url, json=payload, timeout=120)
            if response.status_code != 200:
                raise RuntimeError(f"Gemini 이미지 생성 HTTP {response.status_code}: {response.text[:300]}")
            image_bytes, mime_type = _extract_image(response.json())
            ext = ".jpg" if "jpeg" in mime_type.lower() else ".png"
            digest = hashlib.sha256(image_bytes).hexdigest()[:12]
            images_dir = Path(dated_dir) / "images"
            images_dir.mkdir(parents=True, exist_ok=True)
            filename = f"cover_{digest}{ext}"
            local_path = images_dir / filename
            local_path.write_bytes(image_bytes)
            relative = local_path.relative_to(root_dir).as_posix()
            repo = os.environ.get("GITHUB_REPOSITORY", "gohwansok-max/qaplus-os")
            branch = os.environ.get("GITHUB_REF_NAME", "main")
            raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{quote(relative)}"
            print(f"[OK] 고유 AI 대표 이미지 생성: {relative}")
            return {"IMAGE_PLACEHOLDER_1": raw_url}
        except Exception as exc:
            last_error = exc
            print(f"[!] 대표 이미지 생성 {attempt + 1}/2 실패: {exc}")
    raise RuntimeError(f"대표 이미지 생성에 실패했습니다: {last_error}")























































