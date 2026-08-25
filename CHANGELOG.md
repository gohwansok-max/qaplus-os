# Changelog

이 프로젝트의 모든 주요 변경사항을 기록합니다.

형식: [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 기준
버전: [Semantic Versioning](https://semver.org/lang/ko/) 기준

---

## [1.0.0] — 2026-04-08

첫 공개 릴리스. 수강생이 clone해서 즉시 사용 가능한 수준까지 완성.

### Added — 새로 추가된 것
- **9명 C-Suite 서브에이전트** (`.claude/agents/{cso,cmo,cfo,cto,cdo,coo,cco,cpo,cxo}.md`)
  - YAML frontmatter + cognitive-core 인라인 + 도메인 특화
  - Claude Code Task tool이 실제로 호출 가능한 구조
- **`/kim-director` 슬래시 커맨드** — cso 서브에이전트 자동 호출 + 선제 브리핑 프로토콜
- **5개 스킬 풀 공개** (검수 기준 포함)
  - `skills/content/reels-script/` — 릴스 대본 3버전 + 캡션 3버전 (후킹 12타입)
  - `skills/strategy/weekly-briefing/` — 주간 브리핑 (위험 신호 + 시스템 위생)
  - `skills/strategy/monthly-business-review/` — 월간 OKR/P&L/AI 운영 비용 리뷰
  - `skills/marketing/sales-analysis/` — C.L.O.S.E 퍼널 진단
  - `skills/edutech/course-design/` — L.E.A.R.N 커리큘럼 설계
- **3개 골드 스탠다드 워크플로우** (실제 Task tool 호출 블록 포함)
  - `workflows/examples/weekly-briefing.md`
  - `workflows/examples/content-calendar.md`
  - `workflows/examples/reels-script-pipeline.md`
- **3개 예제 스크립트**
  - `execution/sales_summary_sample.py` — 일별/월별 매출 집계 (167줄, 실행 가능)
  - `execution/instagram_stats_fetch.py` — 인스타그램 Graph API 템플릿
  - `scripts/git_backup.sh` — 일일 자동 백업 (크론 등록 가이드 포함)
- **완성본 샘플**: `examples/1인-프리랜서-디자이너/`
  - CLAUDE.md, context 3종, tasks 3종, 전용 스킬 1개
  - 가상 페르소나 "박소영"의 한 달 운영 모습 풀세트
- **Seed 데이터**
  - `tasks/lessons.md` — 첫 교훈(전제 조건 미확인 실수) 5 Whys 기록
  - `tasks/predictions.md` — 샘플 예측 3건
- **`.claude/settings.json` 권한 확장** — Write/Edit/Bash(세분화) + statusLine + deny 리스트
- **오픈소스 기본기**
  - `LICENSE` (MIT)
  - `CHANGELOG.md` (이 파일)
  - `CONTRIBUTING.md`
  - `CODE_OF_CONDUCT.md`
  - `SECURITY.md`
  - `.github/ISSUE_TEMPLATE/`
  - `.github/PULL_REQUEST_TEMPLATE.md`
- **`README_EN.md`** — 영문 진입점
- **`scripts/doctor.sh`** + **`scripts/doctor.ps1`** — 설치 자가 진단 도구

### Changed — 변경된 것
- `README.md` "68명 AI 직원" → "9명 C-Suite AI" (본사 카피 잔재 제거)
- `skills/README.md` 허위 13개 스킬 목록 → 실재 5개 풀 공개로 교체
- 플레이스홀더 `{{부트캠프_링크}}`, `{{디스코드_링크}}` 4곳 전부 제거
- `workflows/examples/*.md` — 흐름도 수준 → 실행 가능 레퍼런스 구현으로 격상

### Removed — 삭제된 것
- `@include ../_shared/cognitive-core.md` 허위 문법 참조 (Claude Code가 전처리하지 않음)
- `skills/setup/SKILL.md` 에서 `agents/*/README.md` 를 "AI 실행 경로"로 취급하던 혼선. 이제 `.claude/agents/*.md` 9개가 실행 경로, `agents/*/README.md` 9개는 사람이 읽는 페르소나 문서로 명확히 분리.

### Fixed — 버그 수정
- 9개 agent가 Task tool로 호출 불가능하던 구조 → `.claude/agents/*.md` 서브에이전트로 실재화
- `.claude/settings.json` 권한 부족 → Write/Edit/Bash 세분화 허용
- setup SKILL이 허위로 `{{카테고리}}/{{스킬}}` 경로만 명시 → 실제 풀 공개 스킬 5개 경로와 정합
- 수강생 clone 직후 doctor.sh 실행 시 슬롯 경고를 "치명적 오류"로 오검출 → "초기 상태 정상" 메시지로 완화

### Fixed — 버그 수정
- 9개 agent README가 서브에이전트로 실재하지 않아 Task tool로 호출 불가능하던 문제
- `.claude/settings.json` 권한 부족으로 `/setup` 실행 시 Write/Edit 거부되던 문제
- 수강생 클론 직후 `/kim-director` 호출 시 "없는 명령어" 에러

---

## [0.x] — 2026-04-07 이전

비공개 개발 단계. 내부 사용 전용.
