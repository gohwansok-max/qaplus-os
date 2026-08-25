#!/usr/bin/env bash
#
# git_backup.sh — 일일 자동 백업 스크립트
#
# 목적:
#   프로젝트 변경사항을 매일 자동으로 GitHub에 백업.
#   "코드/문서 날아갈까봐" 불안함을 제거하고, AI CEO OS를 자유롭게 실험 가능하게 함.
#
# 사용법:
#   chmod +x scripts/git_backup.sh
#   ./scripts/git_backup.sh
#
# 크론 등록 (매일 오전 2시):
#   crontab -e
#   0 2 * * * cd /path/to/ai-ceo-os && ./scripts/git_backup.sh >> ~/git_backup.log 2>&1
#
# Windows (Task Scheduler):
#   Git Bash로 동일 스크립트 실행 가능
#   또는 PowerShell 버전을 만드세요 (git_backup.ps1)
#

set -euo pipefail

# --- 설정 -------------------------------------------------------------------
BRANCH="${BRANCH:-master}"
DATE_STAMP="$(date '+%Y-%m-%d')"
COMMIT_MSG="backup: ${DATE_STAMP} 일일 자동 백업"

# --- 색상 (터미널 출력용) ---------------------------------------------------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# --- 사전 점검 --------------------------------------------------------------

# 1. git 저장소인가?
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    log_error "git 저장소가 아닙니다. git init 먼저 실행하세요."
    exit 1
fi

# 2. remote 설정 확인
if ! git remote get-url origin > /dev/null 2>&1; then
    log_error "origin remote가 설정되어 있지 않습니다."
    log_error "git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
    exit 1
fi

# 3. 브랜치 확인
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "${CURRENT_BRANCH}" != "${BRANCH}" ]; then
    log_warn "현재 브랜치(${CURRENT_BRANCH})가 기본 백업 브랜치(${BRANCH})와 다릅니다."
    log_warn "현재 브랜치 기준으로 백업합니다."
    BRANCH="${CURRENT_BRANCH}"
fi

# --- 변경사항 감지 ----------------------------------------------------------

log_info "변경사항 확인 중..."

if git diff --quiet && git diff --cached --quiet && [ -z "$(git status --porcelain)" ]; then
    log_info "변경사항 없음. 백업 스킵."
    exit 0
fi

# 변경 파일 수 카운트
CHANGED_COUNT="$(git status --porcelain | wc -l | tr -d ' ')"
log_info "변경 파일 ${CHANGED_COUNT}개 감지"

# --- 커밋 & 푸시 -----------------------------------------------------------

log_info "스테이징 중..."
git add -A

log_info "커밋 생성: ${COMMIT_MSG} (${CHANGED_COUNT}개 파일)"
git commit -m "${COMMIT_MSG} (${CHANGED_COUNT}개 파일)"

log_info "원격(origin/${BRANCH})으로 푸시 중..."
if git push origin "${BRANCH}"; then
    log_info "✅ 백업 완료"
else
    log_error "푸시 실패. 원격 저장소 권한/네트워크 확인 필요."
    exit 1
fi

# --- 정리 ------------------------------------------------------------------

log_info "백업 완료: ${DATE_STAMP}"
log_info "다음 백업: 내일 동일 시각"
