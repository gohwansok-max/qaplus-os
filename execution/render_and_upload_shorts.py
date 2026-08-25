# -*- coding: utf-8 -*-
"""
One-Click Remotion 9:16 Shorts Render & YouTube Upload Pipeline
"""

import os
import sys
import subprocess
import argparse

def run_pipeline(privacy="unlisted", secrets_file="client_secret.json"):
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    remotion_dir = os.path.join(root_dir, "remotion")
    output_mp4 = os.path.join(remotion_dir, "out", "ccp_shorts.mp4")

    os.makedirs(os.path.join(remotion_dir, "out"), exist_ok=True)

    print("\n=======================================================")
    print("🚀 [STEP 1/2] Remotion 9:16 세로 숏츠 비디오 렌더링 시작")
    print("=======================================================\n")
    
    cmd_render = [
        "npx.cmd" if os.name == "nt" else "npx",
        "remotion",
        "render",
        "src/index.ts",
        "CcpShortsVertical",
        "out/ccp_shorts.mp4"
    ]

    res = subprocess.run(cmd_render, cwd=remotion_dir)
    if res.returncode != 0:
        print("[ERROR] Remotion 렌더링에 실패했습니다.")
        sys.exit(res.returncode)

    print(f"\n[OK] 렌더링 완료: {output_mp4}")

    print("\n=======================================================")
    print("🚀 [STEP 2/2] YouTube Data API로 숏츠 자동 업로드 시작")
    print("=======================================================\n")

    uploader_script = os.path.join(root_dir, "execution", "youtube_shorts_uploader.py")
    cmd_upload = [
        sys.executable,
        uploader_script,
        "--file", output_mp4,
        "--privacy", privacy,
        "--secrets", os.path.join(root_dir, secrets_file)
    ]

    res_upload = subprocess.run(cmd_upload, cwd=root_dir)
    if res_upload.returncode != 0:
        print("\n[INFO] 업로드를 완료하려면 client_secret.json 설정이 필요합니다.")
        print("상세 가이드를 참조하세요.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="One-Click Shorts Pipeline")
    parser.add_argument("--privacy", default="unlisted", choices=["public", "unlisted", "private"])
    parser.add_argument("--secrets", default="client_secret.json")
    args = parser.parse_args()
    run_pipeline(privacy=args.privacy, secrets_file=args.secrets)