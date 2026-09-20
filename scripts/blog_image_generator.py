#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""블로그 대표 이미지 처리 모듈.
대표 이미지 1장은 기존 실사형 사진을 재사용하고, 본문에는 추가 이미지를 만들지 않는다.
"""

REALISTIC_COVER_URL = "https://raw.githubusercontent.com/gohwansok-max/qaplus-os/main/outputs/2026/09/20/images/img1_ac6a242883.png"

def generate_and_host_images(image_output_text, root_dir, dated_dir, safe_topic):
    print("[*] 실사형 대표 이미지 1장 적용")
    return {"IMAGE_PLACEHOLDER_1": REALISTIC_COVER_URL}
