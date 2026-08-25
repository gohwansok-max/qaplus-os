#!/usr/bin/env python3
"""
ai-ceo-os Sanitize Scanner
===========================
Public 레포 공개 전 민감정보를 자동 탐지합니다.
실행: python execution/sanitize_for_public.py --check [경로]
"""

import re
import sys
import os
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Finding:
    file: str
    line_num: int
    category: str
    severity: str  # CRITICAL, HIGH, MEDIUM
    snippet: str

# 민감 패턴 정의
PATTERNS = {
    "CRITICAL": [
        (r'100\.\d{1,3}\.\d{1,3}\.\d{1,3}', "Tailscale/내부 IP"),
        (r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{4,5}', "IP:포트"),
        (r'ssh\s+-i\s+', "SSH 명령"),
        (r'\.pem["\'\s]', "PEM 키 참조"),
        (r'/home/ubuntu', "EC2 경로"),
        (r'ANTHROPIC_API_KEY\s*=\s*sk-', "Anthropic API 키 값"),
        (r'META_ACCESS_TOKEN\s*=\s*EA', "Meta 토큰 값"),
        (r'OPENAI_API_KEY\s*=\s*sk-', "OpenAI API 키 값"),
        (r'sk-ant-[a-zA-Z0-9-]+', "Anthropic 키 패턴"),
        (r'xoxb-[0-9]+-[0-9]+-[a-zA-Z0-9]+', "Slack 봇 토큰"),
        (r'discord\.com/api/webhooks/\d+', "Discord Webhook URL"),
    ],
    "HIGH": [
        (r'\d{15,18}', "Facebook/Discord 숫자 ID (15-18자리)"),
        (r'[0-9]+만원|[0-9]+억|[0-9,]+원', "매출/금액 수치"),
        (r'ROAS\s+\d+', "ROAS 수치"),
        (r'전환율\s+[\d.]+%', "전환율 수치"),
        (r'팔로워\s+[\d,]+', "팔로워 수치"),
        (r'구독자\s+[\d,]+', "구독자 수치"),
        (r'@[a-zA-Z0-9_.]+\.(com|co\.kr|net)', "이메일 주소"),
        (r'UCBlTB7GyNQLqZMDRFEZ_cSg', "YouTube 채널 ID"),
        (r'17841\d{10,}', "Instagram ID"),
        (r'58\d{13,}', "Facebook 페이지 ID"),
    ],
    "MEDIUM": [
        (r'ainow-command-center', "내부 인프라 이름"),
        (r'alzalstudio', "NAS 사용자명"),
        (r'shdsjh123', "GitHub 사용자명"),
        (r'신영선|에이나우', "실명/사명 (의도적 포함인지 확인)"),
        (r'G-[A-Z0-9]{10}', "GA4 Measurement ID"),
        (r'904324755785794', "Meta Pixel ID"),
    ],
}

# 스캔 제외 패턴
EXCLUDE_PATTERNS = [
    r'\.git/',
    r'node_modules/',
    r'\.venv/',
    r'__pycache__/',
    r'\.tmp/',
    r'sanitize_for_public\.py$',  # 이 파일 자체
    r'\.env\.example$',  # 예시 파일은 OK
]

def should_exclude(filepath: str) -> bool:
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, filepath):
            return True
    return False

def scan_file(filepath: str) -> list[Finding]:
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except (PermissionError, OSError):
        return findings

    for line_num, line in enumerate(lines, 1):
        for severity, patterns in PATTERNS.items():
            for pattern, category in patterns:
                if re.search(pattern, line):
                    snippet = line.strip()[:80]
                    findings.append(Finding(
                        file=filepath,
                        line_num=line_num,
                        category=category,
                        severity=severity,
                        snippet=snippet,
                    ))
    return findings

def scan_directory(root_path: str) -> list[Finding]:
    all_findings = []
    root = Path(root_path)

    for filepath in root.rglob('*'):
        if filepath.is_file() and filepath.suffix in ('.md', '.py', '.js', '.cjs', '.ts', '.json', '.yml', '.yaml', '.sh', '.env', '.txt'):
            str_path = str(filepath)
            if not should_exclude(str_path):
                findings = scan_file(str_path)
                all_findings.extend(findings)

    return all_findings

def print_report(findings: list[Finding]):
    if not findings:
        print("\n✅ 민감정보 탐지 없음. 공개 준비 완료.")
        return

    # 심각도별 분류
    by_severity = {"CRITICAL": [], "HIGH": [], "MEDIUM": []}
    for f in findings:
        by_severity[f.severity].append(f)

    print(f"\n🔍 총 {len(findings)}건 탐지\n")

    for severity in ["CRITICAL", "HIGH", "MEDIUM"]:
        items = by_severity[severity]
        if items:
            icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}[severity]
            print(f"{icon} {severity}: {len(items)}건")
            print("-" * 60)

            # 파일별 그룹핑
            by_file = {}
            for item in items:
                by_file.setdefault(item.file, []).append(item)

            for filepath, file_findings in by_file.items():
                print(f"  📄 {filepath}")
                for f in file_findings:
                    print(f"     L{f.line_num}: [{f.category}] {f.snippet}")
            print()

    critical_count = len(by_severity["CRITICAL"])
    if critical_count > 0:
        print(f"❌ CRITICAL {critical_count}건 — 공개 전 반드시 수정 필요")
        sys.exit(1)
    else:
        print("⚠️  HIGH/MEDIUM 항목 검토 필요. CRITICAL 없음.")

def main():
    if len(sys.argv) < 2:
        print("사용법: python sanitize_for_public.py --check [경로]")
        print("예시:   python sanitize_for_public.py --check ./projects/ai-ceo-os/")
        sys.exit(1)

    if sys.argv[1] == "--check":
        target = sys.argv[2] if len(sys.argv) > 2 else "."
        print(f"🔍 민감정보 스캔 시작: {target}")
        findings = scan_directory(target)
        print_report(findings)
    else:
        print(f"알 수 없는 명령: {sys.argv[1]}")
        sys.exit(1)

if __name__ == "__main__":
    main()
