#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QA+ 블로그 발행 전 강제 검증 규칙."""

import re
from html.parser import HTMLParser
from urllib.parse import urlparse


INTERNAL_CODE_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:ALL|ENV|FAC|FSC|LAB|MIC|PROC|REG|SAN|EQ|FM|FS|HC|HR|PR|QC|QM)\d{2,4}(?:[-_]\d+)?(?![A-Za-z0-9])",
    re.IGNORECASE,
)
LEADING_CODE_RE = re.compile(
    r"^\s*((?:ALL|ENV|FAC|FSC|LAB|MIC|PROC|REG|SAN|EQ|FM|FS|HC|HR|PR|QC|QM)\d{2,4}(?:[-_]\d+)?)\s*[_\-:：|]*\s*",
    re.IGNORECASE,
)
KOREAN_RE = re.compile(r"[가-힣]")


class _ImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "img":
            return
        values = {key.lower(): (value or "") for key, value in attrs}
        self.images.append(values)


def extract_internal_topic_code(topic):
    match = LEADING_CODE_RE.match(topic or "")
    return match.group(1) if match else None


def strip_internal_topic_code(topic):
    cleaned = LEADING_CODE_RE.sub("", topic or "").strip(" _-:：|")
    return cleaned or (topic or "").strip()


def validate_blog_post(title, body_html, labels=None, source_code=None, minimum_images=3):
    """규칙을 하나라도 어기면 ValueError를 발생시켜 임시저장·발행을 모두 막는다."""
    errors = []
    searchable = "\n".join([title or "", body_html or "", " ".join(labels or [])])
    codes = sorted(set(m.group(0) for m in INTERNAL_CODE_RE.finditer(searchable)))
    if source_code and re.search(rf"(?<![A-Za-z0-9]){re.escape(source_code)}(?![A-Za-z0-9])", searchable, re.I):
        codes = sorted(set(codes + [source_code]))
    if codes:
        errors.append("내부 파일 구분코드가 노출됨: " + ", ".join(codes))

    parser = _ImageParser()
    parser.feed(body_html or "")
    valid_sources = []
    for index, image in enumerate(parser.images, start=1):
        src = image.get("src", "").strip()
        alt = image.get("alt", "").strip()
        parsed = urlparse(src)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or "PLACEHOLDER" in src.upper():
            errors.append(f"이미지 {index}의 URL이 유효하지 않음")
        else:
            valid_sources.append(src)
        if not alt or not KOREAN_RE.search(alt):
            errors.append(f"이미지 {index}의 한글 alt 설명이 없음")

    unique_sources = set(valid_sources)
    if len(unique_sources) < minimum_images:
        errors.append(f"서로 다른 유효 이미지가 {minimum_images}장 미만임 ({len(unique_sources)}장)")
    if len(valid_sources) != len(unique_sources):
        errors.append("중복 이미지 URL이 있음")

    if errors:
        raise ValueError("발행 전 규칙 검사 실패: " + "; ".join(errors))
    return {"image_count": len(unique_sources), "internal_code_count": 0, "passed": True}
