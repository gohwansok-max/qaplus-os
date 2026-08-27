#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub raw URL을 즉석 파일 호스팅으로 쓰기 위한 공용 헬퍼.
(Blogger 이미지, 인스타그램 릴스 video_url 등 "공개 URL이 필요한데 별도 호스팅이 없는" 경우에 재사용)
"""

import os
import subprocess
import urllib.parse

GITHUB_REPO = "gohwansok-max/qaplus-os"
GITHUB_BRANCH = "main"


def _git(args, cwd):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def push_and_get_raw_url(root_dir, file_path):
    """ 파일 하나를 즉시 git add+commit+push 하고 GitHub raw URL을 반환.
    이미 커밋되어 있고 변경 없는 경우(로캘에 따라 메시지가 다를 수 있어 returncode로만 판단)도 정상 처리하고 URL을 반환한다. """
    rel_path = os.path.relpath(file_path, root_dir).replace("\\", "/")

    _git(["add", rel_path], root_dir)
    _git(["commit", "-m", f"chore(auto): {os.path.basename(file_path)} 자동 커밋 (외부 API 공개 URL용)"], root_dir)

    push = _git(["push", "origin", f"HEAD:{GITHUB_BRANCH}"], root_dir)
    if push.returncode != 0:
        print(f"[!] 파일 푸시 실패 (공개 URL이 아직 안 뜰 수 있음): {push.stderr}")
        return None

    encoded_path = urllib.parse.quote(rel_path)
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{encoded_path}"
