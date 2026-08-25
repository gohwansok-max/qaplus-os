# doctor.ps1 — ai-ceo-os 설치 자가 진단 (Windows PowerShell 버전)
#
# 사용법:
#   .\scripts\doctor.ps1
#
# 결과 코드:
#   0 — 정상
#   1 — 경고
#   2 — 치명적

$ErrorActionPreference = "Continue"

# --- 카운터 ---
$script:Checks = 0
$script:Passed = 0
$script:Warned = 0
$script:Failed = 0

function Write-Pass($msg) {
    $script:Checks++
    $script:Passed++
    Write-Host "  ✓ $msg" -ForegroundColor Green
}

function Write-Warn($msg) {
    $script:Checks++
    $script:Warned++
    Write-Host "  ⚠ $msg" -ForegroundColor Yellow
}

function Write-Fail($msg) {
    $script:Checks++
    $script:Failed++
    Write-Host "  ✗ $msg" -ForegroundColor Red
}

function Write-Section($title) {
    Write-Host ""
    Write-Host "━━ $title ━━" -ForegroundColor Cyan
}

# --- 헤더 ---
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        🩺  ai-ceo-os 설치 진단 도구 (doctor.ps1)         ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# --- 1. 핵심 파일 ---
Write-Section "1. 핵심 파일"

$requiredFiles = @(
    "CLAUDE.md", "README.md", "LICENSE", "CHANGELOG.md",
    ".claude/settings.json", ".claude/commands/setup.md", ".claude/commands/kim-director.md",
    "context/ceo-persona.md", "context/mission-vision.md", "context/channel-rules.md",
    "tasks/todo.md", "tasks/lessons.md", "tasks/predictions.md", "tasks/session_handoff.md"
)

foreach ($f in $requiredFiles) {
    if (Test-Path $f) { Write-Pass $f } else { Write-Fail "$f 없음 — 필수 파일" }
}

# --- 2. 서브에이전트 9명 ---
Write-Section "2. C-Suite 서브에이전트 9명"

$agents = @("cso", "cmo", "cfo", "cto", "cdo", "coo", "cco", "cpo", "cxo")
foreach ($a in $agents) {
    $f = ".claude/agents/$a.md"
    if (-not (Test-Path $f)) {
        Write-Fail "$f 없음"
        continue
    }

    $content = Get-Content $f -Raw
    if ($content -match ("(?s)^---.*?name:\s*" + $a + ".*?---")) {
        Write-Pass "$a 서브에이전트 (frontmatter 정상)"
    } else {
        Write-Warn "$a 있지만 frontmatter가 이상함"
    }
}

# --- 3. 스킬 5개 ---
Write-Section "3. 풀 공개 스킬"

$skills = @(
    "skills/content/reels-script/SKILL.md",
    "skills/strategy/weekly-briefing/SKILL.md",
    "skills/strategy/monthly-business-review/SKILL.md",
    "skills/marketing/sales-analysis/SKILL.md",
    "skills/edutech/course-design/SKILL.md",
    "skills/setup/SKILL.md"
)

foreach ($s in $skills) {
    if (Test-Path $s) { Write-Pass $s } else { Write-Fail "$s 없음" }
}

# --- 4. 워크플로우 ---
Write-Section "4. 워크플로우 골드 스탠다드"

$workflows = @(
    "workflows/examples/weekly-briefing.md",
    "workflows/examples/content-calendar.md",
    "workflows/examples/reels-script-pipeline.md"
)

foreach ($w in $workflows) {
    if (-not (Test-Path $w)) {
        Write-Fail "$w 없음"
        continue
    }
    $content = Get-Content $w -Raw
    if ($content -match 'Task\(') {
        Write-Pass "$w (Task tool 호출 블록 포함)"
    } else {
        Write-Warn "$w 있지만 Task 호출 블록 없음"
    }
}

# --- 5. 예제 스크립트 ---
Write-Section "5. 예제 스크립트"

$scripts = @(
    "execution/sales_summary_sample.py",
    "execution/instagram_stats_fetch.py",
    "scripts/git_backup.sh"
)

foreach ($s in $scripts) {
    if (Test-Path $s) { Write-Pass $s } else { Write-Fail "$s 없음" }
}

# --- 6. 미치환 슬롯 검사 ---
Write-Section "6. 플레이스홀더 미치환 검사"

$slotCount = 0
$files = Get-ChildItem -Path "CLAUDE.md", "context" -Filter "*.md" -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch '\.template\.' }
foreach ($f in $files) {
    $matches = Select-String -Path $f.FullName -Pattern '\{\{.*?\}\}'
    if ($matches) {
        $slotCount += $matches.Count
    }
}

if ($slotCount -eq 0) {
    Write-Pass "CLAUDE.md + context/ 에 미치환 슬롯 없음 (/setup 완료 상태)"
} elseif ($slotCount -le 20) {
    Write-Warn "$slotCount 개 슬롯 미치환 — /setup 실행 또는 수동 편집 필요"
    Write-Host "     (clone 직후라면 정상)" -ForegroundColor Yellow
} else {
    Write-Pass "$slotCount 개 슬롯 대기 중 (clone 직후 초기 상태 — /setup 실행 필요)"
    Write-Host "     ℹ 다음 단계: claude → /setup" -ForegroundColor Cyan
}

# --- 7. 오픈소스 기본기 ---
Write-Section "7. 오픈소스 기본기"

$basics = @(
    "LICENSE", "CHANGELOG.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md",
    "SECURITY.md", ".github/PULL_REQUEST_TEMPLATE.md", ".github/ISSUE_TEMPLATE/bug_report.md"
)

foreach ($b in $basics) {
    if (Test-Path $b) { Write-Pass $b } else { Write-Warn "$b 없음 (권장)" }
}

# --- 8. Git ---
Write-Section "8. Git 설정"

if (Test-Path ".git") {
    Write-Pass "Git 저장소"

    $remote = git remote get-url origin 2>$null
    if ($remote) {
        Write-Pass "Origin remote: $remote"
    } else {
        Write-Warn "Origin remote 없음"
    }

    if (Test-Path ".gitignore") {
        $gitignore = Get-Content ".gitignore" -Raw
        if ($gitignore -match '\.env') {
            Write-Pass ".gitignore에 .env 포함"
        } else {
            Write-Warn ".gitignore에 .env 누락 — 보안 위험"
        }
    } else {
        Write-Fail ".gitignore 없음"
    }
} else {
    Write-Warn "Git 저장소 아님 — git init 권장"
}

# --- 요약 ---
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                        진단 결과                           ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  총 체크: $script:Checks"
Write-Host "  통과: $script:Passed" -ForegroundColor Green
Write-Host "  경고: $script:Warned" -ForegroundColor Yellow
Write-Host "  실패: $script:Failed" -ForegroundColor Red
Write-Host ""

if ($script:Failed -gt 0) {
    Write-Host "⛔ 치명적 문제 $script:Failed 건. 수정 후 다시 실행하세요." -ForegroundColor Red
    Write-Host ""
    Write-Host "다음 단계:"
    Write-Host "  1. /setup 재실행"
    Write-Host "  2. 수동 수정"
    Write-Host "  3. .\scripts\doctor.ps1 재실행"
    exit 2
} elseif ($script:Warned -gt 0) {
    Write-Host "⚠️  경고 $script:Warned 건. 계속 사용 가능하지만 해결 권장." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✅ 모든 체크 통과. 김이사 호출 준비 완료." -ForegroundColor Green
    Write-Host ""
    Write-Host "다음 단계:"
    Write-Host "  claude → /kim-director"
    exit 0
}
