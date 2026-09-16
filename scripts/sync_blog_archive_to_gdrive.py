#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub의 QA+ 블로그 산출물을 이 PC의 Google Drive 폴더로 동기화한다."""

import argparse
import datetime
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


REPOSITORY = os.environ.get("QA_BLOG_GITHUB_REPOSITORY", "gohwansok-max/qaplus-os")
DEFAULT_ARCHIVE_ROOT = pathlib.Path(
    os.environ.get(
        "QA_BLOG_ARCHIVE_ROOT",
        r"G:\내 드라이브\02_유튜브_콘텐츠\03_QA_플러스\04_블로그_아카이브",
    )
)


def api_json(url):
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "QAPlus-Blog-Archiver/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def list_remote_files(remote_path):
    encoded = urllib.parse.quote(remote_path, safe="/")
    url = f"https://api.github.com/repos/{REPOSITORY}/contents/{encoded}?ref=main"
    try:
        entries = api_json(url)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return []
        raise
    files = []
    for entry in entries:
        if entry.get("type") == "file":
            files.append(entry)
        elif entry.get("type") == "dir":
            files.extend(list_remote_files(entry["path"]))
    return files


def download_file(url, destination):
    # GitHub API가 한글 파일명의 download_url을 비인코딩 상태로 돌려주는 경우가 있다.
    encoded_url = urllib.parse.quote(url, safe=":/?=&%")
    request = urllib.request.Request(encoded_url, headers={"User-Agent": "QAPlus-Blog-Archiver/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        content = response.read()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.read_bytes() == content:
        return False
    destination.write_bytes(content)
    return True


def sync_date(date_text, archive_root=DEFAULT_ARCHIVE_ROOT):
    parsed = datetime.date.fromisoformat(date_text)
    remote_root = f"outputs/{parsed:%Y/%m/%d}"
    destination_root = pathlib.Path(archive_root) / f"{parsed:%Y}" / f"{parsed:%m}" / f"{parsed:%d}"
    files = list_remote_files(remote_root)
    if not files:
        print(f"동기화할 블로그 산출물이 아직 없습니다: {remote_root}")
        return 0

    changed = 0
    for entry in files:
        relative = pathlib.PurePosixPath(entry["path"]).relative_to(remote_root)
        destination = destination_root.joinpath(*relative.parts)
        if download_file(entry["download_url"], destination):
            changed += 1
            print(f"저장: {destination}")
    print(f"완료: 총 {len(files)}개 확인, {changed}개 갱신 → {destination_root}")
    return changed


def main():
    parser = argparse.ArgumentParser(description="QA+ 블로그 산출물을 Google Drive로 아카이브")
    parser.add_argument("--date", help="YYYY-MM-DD, 생략하면 한국시간 오늘")
    parser.add_argument("--archive-root", type=pathlib.Path, default=DEFAULT_ARCHIVE_ROOT)
    args = parser.parse_args()
    date_text = args.date or datetime.datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    sync_date(date_text, args.archive_root)


if __name__ == "__main__":
    main()
