#!/usr/bin/env bash
#
# doctor.sh — ai-ceo-os 설치 자가 진단 도구
#
# 목적:
#   수강생이 clone + /setup 완료 후, 모든 것이 제대로 설치되었는지 체크.
#   깨진 구조를 찾아 구체적 수정 방법을 안내.
#
# 사용법:
#   ./scripts/doctor.sh
#
# 결과 코드:
#   0 — 모든 체크 통과 (정상)
#   1 — 경고 있음 (계속 사용 가능)
#   2 — 치명적 문제 (수정 필요)
#

set -uo pipefail

# --- 색상 -------------------------------------------------------------------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS="${GREEN}✓${NC}"
FAIL="${RED}✗${NC}"
WARN="${YELLOW}⚠${NC}"

# --- 카운터 -----------------------------------------------------------------
CHECKS=0
PASSED=0
WARNED=0
FAILED=0

check_pass() {
    CHECKS=$((CHECKS + 1))
    PASSED=$((PASSED + 1))
    echo -e "  ${PASS} $1"
}

check_warn() {
    CHECKS=$((CHECKS + 1))
    WARNED=$((WARNED + 1))
    echo -e "  ${WARN} $1"
}

check_fail() {
    CHECKS=$((CHECKS + 1))
    FAILED=$((FAILED + 1))
    echo -e "  ${FAIL} $1"
}

section() {
    echo ""
    echo -e "${BLUE}━━ $1 ━━${NC}"
}

# --- 헤더 -------------------------------------------------------------------
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║        🩺  ai-ceo-os 설치 진단 도구 (doctor.sh)          ║"
echo "╚══════════════════════════════════════════════════════════╝"

# --- 체크 1: 핵심 파일 존재 ----------------------------------------------
section "1. 핵심 파일"

REQUIRED_FILES=(
    "CLAUDE.md"
    "README.md"
    "LICENSE"
    "CHANGELOG.md"
    ".claude/settings.json"
    ".claude/commands/setup.md"
    ".claude/commands/kim-director.md"
    "context/ceo-persona.md"
    "context/mission-vision.md"
    "context/channel-rules.md"
    "tasks/todo.md"
    "tasks/lessons.md"
    "tasks/predictions.md"
    "tasks/session_handoff.md"
)

for f in "${REQUIRED_FILES[@]}"; do
    if [ -f "$f" ]; then
        check_pass "$f"
    else
        check_fail "$f 없음 — 필수 파일"
    fi
done

# --- 체크 2: 9개 서브에이전트 -------------------------------------------
section "2. C-Suite 서브에이전트 9명"

AGENTS=(cso cmo cfo cto cdo coo cco cpo cxo)
for agent in "${AGENTS[@]}"; do
    f=".claude/agents/${agent}.md"
    if [ ! -f "$f" ]; then
        check_fail "${f} 없음"
        continue
    fi

    # frontmatter 확인
    if head -1 "$f" | grep -q "^---$" && grep -q "^name: ${agent}$" "$f"; then
        check_pass "${agent} 서브에이전트 (frontmatter 정상)"
    else
        check_warn "${agent} 있지만 frontmatter가 이상함 (name: ${agent} 있는지 확인)"
    fi
done

# --- 체크 3: 공개 스킬 5개 -----------------------------------------------
section "3. 풀 공개 스킬"

SKILLS=(
    "skills/content/reels-script/SKILL.md"
    "skills/strategy/weekly-briefing/SKILL.md"
    "skills/strategy/monthly-business-review/SKILL.md"
    "skills/marketing/sales-analysis/SKILL.md"
    "skills/edutech/course-design/SKILL.md"
    "skills/setup/SKILL.md"
)

for skill in "${SKILLS[@]}"; do
    if [ -f "$skill" ]; then
        check_pass "${skill}"
    else
        check_fail "${skill} 없음"
    fi
done

# --- 체크 4: 워크플로우 예제 ---------------------------------------------
section "4. 워크플로우 골드 스탠다드"

WORKFLOWS=(
    "workflows/examples/weekly-briefing.md"
    "workflows/examples/content-calendar.md"
    "workflows/examples/reels-script-pipeline.md"
)

for wf in "${WORKFLOWS[@]}"; do
    if [ ! -f "$wf" ]; then
        check_fail "${wf} 없음"
        continue
    fi
    # 실제 Task 호출 블록 포함 여부
    if grep -q "Task(" "$wf"; then
        check_pass "${wf} (Task tool 호출 블록 포함)"
    else
        check_warn "${wf} 있지만 Task 호출 블록 없음 — 실행 가능한지 확인"
    fi
done

# --- 체크 5: 예제 스크립트 -----------------------------------------------
section "5. 예제 스크립트"

SCRIPTS=(
    "execution/sales_summary_sample.py"
    "execution/instagram_stats_fetch.py"
    "scripts/git_backup.sh"
)

for s in "${SCRIPTS[@]}"; do
    if [ -f "$s" ]; then
        check_pass "${s}"
    else
        check_fail "${s} 없음"
    fi
done

# --- 체크 6: 슬롯 미채움 검사 --------------------------------------------
section "6. 플레이스홀더 미치환 검사"

SLOT_COUNT=$(grep -rn '{{.*}}' CLAUDE.md context/ 2>/dev/null | grep -v '\.template\.' | wc -l | tr -d ' ')

if [ "$SLOT_COUNT" -eq 0 ]; then
    check_pass "CLAUDE.md + context/ 에 미치환 슬롯 없음 (/setup 완료 상태)"
elif [ "$SLOT_COUNT" -le 20 ]; then
    check_warn "${SLOT_COUNT}개 슬롯 미치환 — /setup 실행 또는 수동 편집 필요"
    echo -e "${YELLOW}     (clone 직후 상태라면 /setup 실행 전까지는 정상)${NC}"
else
    # 20개 이상이면 '초기 상태'로 판단
    check_pass "${SLOT_COUNT}개 슬롯 대기 중 (clone 직후 초기 상태로 판단 — /setup 실행 필요)"
    echo -e "${BLUE}     ℹ 다음 단계: claude → /setup${NC}"
fi

# --- 체크 7: 오픈소스 기본기 ---------------------------------------------
section "7. 오픈소스 기본기"

BASICS=(
    "LICENSE"
    "CHANGELOG.md"
    "CONTRIBUTING.md"
    "CODE_OF_CONDUCT.md"
    "SECURITY.md"
    ".github/PULL_REQUEST_TEMPLATE.md"
    ".github/ISSUE_TEMPLATE/bug_report.md"
)

for b in "${BASICS[@]}"; do
    if [ -f "$b" ]; then
        check_pass "$b"
    else
        check_warn "$b 없음 (선택사항이지만 권장)"
    fi
done

# --- 체크 8: git 상태 -----------------------------------------------------
section "8. Git 설정"

if git rev-parse --git-dir > /dev/null 2>&1; then
    check_pass "Git 저장소"

    if git remote get-url origin > /dev/null 2>&1; then
        REMOTE=$(git remote get-url origin)
        check_pass "Origin remote: $REMOTE"
    else
        check_warn "Origin remote 없음 — GitHub 백업 설정 필요"
    fi

    if [ -f ".gitignore" ]; then
        if grep -q ".env" .gitignore; then
            check_pass ".gitignore에 .env 포함 (민감정보 보호)"
        else
            check_warn ".gitignore에 .env 누락 — 보안 위험"
        fi
    else
        check_fail ".gitignore 없음"
    fi
else
    check_warn "Git 저장소 아님 — git init 권장"
fi

# --- 요약 ------------------------------------------------------------------
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                        진단 결과                           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "  총 체크: $CHECKS"
echo -e "  ${GREEN}통과: $PASSED${NC}"
echo -e "  ${YELLOW}경고: $WARNED${NC}"
echo -e "  ${RED}실패: $FAILED${NC}"
echo ""

if [ "$FAILED" -gt 0 ]; then
    echo -e "${RED}⛔ 치명적 문제 $FAILED건. 수정 후 다시 실행하세요.${NC}"
    echo ""
    echo "다음 단계:"
    echo "  1. /setup 재실행 (누락 파일 자동 생성)"
    echo "  2. 수동 수정이 필요한 파일 보강"
    echo "  3. ./scripts/doctor.sh 재실행"
    exit 2
elif [ "$WARNED" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  경고 $WARNED건. 계속 사용 가능하지만 해결 권장.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ 모든 체크 통과. 김이사 호출 준비 완료.${NC}"
    echo ""
    echo "다음 단계:"
    echo "  claude → /kim-director"
    exit 0
fi
