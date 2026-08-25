# 할 일 목록

> AI와 함께 관리하는 작업 리스트입니다.
> `/setup` 실행 후 자동으로 첫 할일이 채워집니다.

---

## 🚀 v1.0 릴리스 게이트 (배포 전 완성도 스프린트)

> CEO 지시 (2026-04-08): "누가 받고 분석해도 완벽한 수준"으로 끌어올린 후 v1.0 태그 + master 머지 + 공개.
> 12개 게이트 전부 통과 → CEO 최종 검수 → 릴리스.

### 구조 (P0)
- [x] **G1. 서브에이전트 실재화** — `.claude/agents/` 9개 파일 생성 (cso/cmo/cfo/cto/cdo/coo/cco/cpo/cxo), frontmatter + cognitive-core 인라인 + 도메인 특화. `@include` 허위 문법 제거.
- [x] **G1.5. `/kim-director` 슬래시 커맨드** — `.claude/commands/kim-director.md` 생성, cso 서브에이전트 자동 호출 + 선제 브리핑 프로토콜.
- [ ] **G2. cognitive-core 실작동 검증** — 서브에이전트 호출 시 9명 전원이 표준 보고 템플릿(확신도/Cross-Lens/Inversion) 준수 확인.
- [ ] **[v3 검증] 드라이런 안건**: "이번 주 릴스 3편 기획 — 고객 여정 3단계(무료 가치) 타겟" Tier 2 (CCO+CMO) 병렬 소집. v3 9섹션 스키마 준수 여부 검증 + routing-map.yaml `content-reels` route 매칭 확인. 실행: `김이사, 드라이런 시작` → Task tool로 cco/cmo 병렬 호출.

### 콘텐츠 (P0 채우기)
- [x] **G3. 스킬 5개 풀 공개** — reels-script / weekly-briefing / sales-analysis / monthly-business-review / course-design 전부 sanitize 후 포팅 완료.
- [x] **G4. 워크플로우 3개 골드 스탠다드** — weekly-briefing.md / content-calendar.md / reels-script-pipeline.md 전부 `Task(subagent_type=...)` 호출 블록 + 입출력 샘플 + CEO 명령 예시 포함 완료.
- [x] **G5. 예제 스크립트 3개** — sales_summary_sample.py / instagram_stats_fetch.py / git_backup.sh 실동작 목업 완료.

### 신뢰도 (P1)
- [x] **G6. 숫자/본사 잔재 제거** — README "68명 AI 직원" → "9명 C-Suite" 통일 완료. 플레이스홀더 4곳 제거 완료. (knowledge/ PDF 정체성 명시는 G10에서 처리)
- [ ] **G7. `/setup` End-to-End 통과** — 깨끗한 폴더 clone → `/setup` → 22개 파일 정상 생성 + 주요 슬롯 전부 채워짐.
- [x] **G8. `.claude/settings.json` 권한 확장** — Write/Edit/Bash(세분화) 허용 + statusLine 예시 + deny 리스트 완료. (세션 시작 hook은 Claude Code hooks API 안정화 후 v1.1에서 추가)

### 수강생 체험 (P3)
- [x] **G9. Seed 데이터** — `tasks/predictions.md` P-001~003 샘플, `tasks/lessons.md` 첫 교훈(클러스터 A) 기록, `examples/` 내부에는 WIN + 기록 예시 풀.
- [x] **G10. `examples/1인-프리랜서-디자이너/` 완성본** — README, CLAUDE.md, context 3종, tasks 3종, 전용 커스텀 스킬 1개 = **100% 채워진 풀세트** 완성.

### 오픈소스 기본기 (P2)
- [x] **G11. LICENSE + CHANGELOG + CONTRIBUTING + CODE_OF_CONDUCT + SECURITY + `.github/` 템플릿** — 7종 세트 완성.
- [x] **G12. 영문 README_EN.md + `scripts/doctor.sh` + `scripts/doctor.ps1`** — Bash + PowerShell 양쪽 자가 진단 도구 완성. (설치 데모 GIF는 CEO 수동 녹화 대기)

### 릴리스
- [ ] **검수**: Full dry-run (clone → `/setup` → 첫 미션 E2E) + doctor.sh 자동 검사 통과 + CSO 서브에이전트 셀프 리뷰 + CEO 최종 검수.
- [ ] **태그**: `git tag v1.0 && git push --tags`
- [ ] **공개**: GitHub 공개 전환 + README 상단 배지 정리.

---

## 시작하기 (수강생용)

- [ ] `/setup` 실행하여 AI CEO OS 셋업
- [ ] 첫 번째 업무 AI에게 시켜보기
- [ ] 결과 확인하고 CLAUDE.md 수정

---

## 레포 변경 이력

### [2026-04-07] 강의 3-1/3-2/3-3 정합화 + CEO 시스템 풀 이식 (32개 파일)

**목표**: 부트캠프 수강생이 `[강의FINAL+]_3-1/3-2/3-3` 자료와 함께 받았을 때 강의 내용과 레포가 1:1로 매칭되고, CEO 김이사가 실제 사용하는 시스템을 그대로 가져갈 수 있도록 정합화.

#### 변경 요약
- **민감정보 점검**: 클린. `.gitignore`에 `tasks/curriculum-detail-v1.md`, `CEO/*` 추가 (README + template만 예외)
- **P0 강의 정합 (4건)**: README 숫자 통일(61→68, 8→9), CLAUDE.template 6단계 여정+금지행동+자주시키는작업+에이전트팀+운영원칙6가지, ceo-persona 좋은 예 5+ 슬롯, CSO "김이사" 캐릭터
- **C-Suite 8명 페르소나 풀 작성** (cmo/cfo/cto/cdo/coo/cco/cpo/cxo) — 1줄→90~120줄
- **`.claude/rules/` 6개 신규**: 공통, 품질기준, 의사결정, 자동검수, 도구제안, 산출물
- **CEO/ 폴더 신설** (gitignore 보호): README + 목표/일정_마감/아이디어 템플릿 3개
- **scripts/, execution/ README 신규**: 인프라/비즈니스 로직 스크립트 자리
- **workflows/examples/ 5개 추가**: 릴스 / 유튜브 / 마케팅 분석 / 세일즈 퍼널 / 월간 사업 리뷰
- **`/setup` 인터뷰 Q6~Q12 확장**: 채널, 가격, 경쟁사, 최대 고민. 9명 임원 전원 사업 맞춤 핵심 질문 자동 생성. 첫 미션이 Q12 최대 고민 직결
- **시스템 추가**: tasks/predictions.template.md, session_handoff.template.md, agents/c-suite-protocol.md (3-Tier 운영)

#### 결과
- 9명 임원 전원 활성 (이전엔 3명만 사업 맞춤됨)
- `/setup` 한 번에 22개 파일 자동 생성 (이전엔 7개)
- 강의 3-1/3-2/3-3과 레포 1:1 매칭
- CEO 데이터는 `CEO/` 폴더로 안전 분리 (gitignore)

#### 검증 필요 (다음 작업)
- [ ] 수강생 입장 `/setup` dry-run (22개 자동 생성 슬롯 누락 점검)
- [ ] GitHub 백업 (`scripts/git_backup.ps1` CEO 실행)
- [ ] 부트캠프 강의 자료에 ai-ceo-os GitHub 링크 명시

### [2026-04-07] `.template.md` 파일명 컨벤션 폐기 (9개 파일 정리)

**문제**: 파일명에 `.template.md`가 붙어있어 수강생 혼란 ("복사해서 이름 바꿔야 하나? 그냥 편집해도 되나?")

**조치**:
- **정상 이름으로 재생성 9개**: `CLAUDE.md`, `context/ceo-persona.md`, `context/channel-rules.md`, `context/mission-vision.md`, `tasks/predictions.md`, `tasks/session_handoff.md`, `CEO/목표.md`, `CEO/일정_마감.md`, `CEO/아이디어.md`
- **`.template.md` 잔재 9개 삭제** (CEO PowerShell 직접 실행)
- **참조 5건 수정**: `README.md` 1건 + `skills/setup/SKILL.md` 3건 + `CEO/README.md` 1건
- **`.gitignore` 정리**: `CEO/*` 차단 해제, `**/predictions.md` 차단 해제 → starter 파일 git 추적, 사용자 데이터는 로컬 ignore 권장

**검증**:
- `find . -name "*.template.md"` → **0건** ✅
- 9개 정상 파일 모두 존재 확인 ✅

**원칙**:
- starter 파일은 정상 이름 + `{{slot}}` 채우기 방식
- `/setup` 인터뷰가 자동으로 슬롯 채움 (수동 편집도 가능)
- 사용자 개인 데이터 보호는 `.gitignore` 또는 `git update-index --skip-worktree`로
