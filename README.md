# ai-ceo-os

### 9명의 C-Suite AI가 1인 CEO를 돕는 경영 OS

**Claude Code 위에서 실제로 작동하는** 9명 AI 임원 팀의 전체 구조를 공개합니다.

- **CSO 김이사** (전략 총괄) + **CMO/CFO/CTO/CDO/COO/CCO/CPO/CXO** 8명 C-level
- 각 임원은 독립된 `.claude/agents/*.md` 서브에이전트로 실재합니다 — 흉내가 아닙니다
- 3-Tier 운영 (일상은 김이사 단독, 복잡한 건은 2~3명 병렬 소집, 가격/런칭은 8명 전원 반박 라운드)
- 제1원칙 사고 + 참모진 × C-Suite 매트릭스 + 확신도 표기 + Zero-Inference Rule
- 매 결정에 Cross-Lens 자가 점검 + Inversion(망치는 3가지 시나리오) 의무

> 본사 시스템(68명 에이전트 풀스택)의 **핵심 9명을 오픈소스로 공개**한 버전입니다. 뼈대만으로 작동하지 않으며, 당신의 사업 데이터/전략/콘텐츠 공식을 채워야 합니다.

---

## 이런 문제가 있다면

- **"AI 에이전트 만들었는데 3일 후 안 쓴다"** — 에이전트에 역할과 판단 기준이 없기 때문입니다
- **"Claude 프로젝트 파일을 어떻게 구조화해야 할지 모르겠다"** — CLAUDE.md 하나가 AI OS의 두뇌입니다
- **"1인 기업인데 팀처럼 돌아가는 시스템이 필요하다"** — 9명의 C-Suite AI(CSO 김이사 + 8명)가 각자의 관점에서 판단합니다

---

## 이 레포가 주는 것

### 1. C-Suite 서브에이전트 9명 (실제 Claude Code 서브에이전트로 실재)
혼자서 마케팅, 재무, 콘텐츠, 고객관리를 다 하시죠?
9명의 AI 임원이 각자의 관점에서 **독립적으로** 판단합니다. `.claude/agents/{cso,cmo,cfo,...}.md`로 Claude Code Task tool이 직접 호출.

```
CEO (당신)
  └── CSO 김이사 (전략 총괄)
       ├── CMO — 마케팅+세일즈
       ├── CFO — 재무+전략
       ├── CTO — 기술+인프라
       ├── CDO — 데이터+분석
       ├── COO — 운영+조직
       ├── CCO — 콘텐츠+미디어
       ├── CPO — 제품+교육
       └── CXO — 고객경험+커뮤니티
```

> **3-Tier 운영**: 일상 90%는 김이사 단독(Tier 1), 광고/시스템 변경 9%는 관련 임원 2~3명 소집(Tier 2), 가격/런칭/분기 리뷰 1%는 8명 전원 + 상호 반박(Tier 3). 상세: [agents/c-suite-protocol.md](agents/c-suite-protocol.md)

### 2. 워크플로우 파이프라인 (골드 스탠다드 3개 풀 공개)
"릴스 대본 써줘"가 아닙니다. 기획→생산→분석까지 전체가 파이프라인으로 연결됩니다. 실제 Task tool 호출 블록까지 포함한 3개 레퍼런스 구현 공개:

- `workflows/examples/weekly-briefing.md` — 주간 브리핑 (김이사 + Tier 2 조건부 소집)
- `workflows/examples/content-calendar.md` — 월간 콘텐츠 캘린더 (CCO + CMO 병렬)
- `workflows/examples/reels-script-pipeline.md` — 릴스 대본 3버전 (CCO 주도 + CMO 검증)

→ [워크플로우 전체 목록](workflows/README.md)

### 3. CLAUDE.md 패턴
AI의 두뇌를 설계하는 설정 파일. 이 하나의 파일이 AI가 당신의 사업을 이해하게 만듭니다.

→ [CLAUDE.md](CLAUDE.md)

### 4. 스킬 매뉴얼 체계 (5개 풀 공개)
반복되는 업무를 체계화한 매뉴얼. 검수 기준(스킬 이밸)까지 포함한 5개 스킬 풀 공개:

- `skills/content/reels-script/` — 릴스 대본 3버전 + 캡션 3버전
- `skills/strategy/weekly-briefing/` — 김이사 주간 브리핑
- `skills/strategy/monthly-business-review/` — 월간 OKR/P&L/AI 운영 비용 리뷰
- `skills/marketing/sales-analysis/` — C.L.O.S.E 퍼널 진단
- `skills/edutech/course-design/` — L.E.A.R.N 커리큘럼 설계

→ [스킬 가이드](skills/README.md)

---

## 빠르게 시작하기

```bash
# 1. Claude Code 설치 (최초 1회)
npm install -g @anthropic-ai/claude-code

# 2. 압축 파일 해제 (zip 받으신 경우) 또는 git clone (GitHub 공개 후)
# - ZIP 받았다면: 압축 해제 후 폴더로 이동
# - git clone 받았다면: git clone ... && cd ai-ceo-os

# 3. 해당 폴더로 이동 후 Claude Code 실행
cd ai-ceo-os
claude

# 4. 자동 셋업 (AI가 인터뷰 → 파일 자동 생성)
/setup

# 5. 설치 자가 진단 (모든 게 제대로 깔렸는지 확인)
./scripts/doctor.sh       # macOS/Linux
# .\scripts\doctor.ps1    # Windows

# 6. 김이사 호출 → 선제 브리핑
/kim-director
```

> **처음이신가요?** → [`INSTALL.md`](INSTALL.md) 3분 설치 가이드부터 보세요.

→ [Claude Code 설치 가이드](guides/00_클로드코드_설치.md) — Windows/Mac 모두 지원
→ [퀵스타트 가이드](guides/quickstart.md)
→ [커스터마이징 가이드](guides/customization.md)
→ [완성본 샘플: 1인 프리랜서 디자이너](examples/1인-프리랜서-디자이너/README.md) — "채워지면 이렇게 됩니다"
→ 🇬🇧 [English README](README_EN.md)

---

## 구조

```
ai-ceo-os/
├── agents/        ← AI 직원 정의 (C-Suite 9명: 김이사 + 8명)
├── context/       ← 사업 맥락 (CEO 페르소나, 미션)
├── knowledge/     ← 지식 저장소 (채널 데이터, 전략 참고)
├── skills/        ← 업무 매뉴얼
├── workflows/     ← 자동화 파이프라인
├── execution/     ← 스크립트
└── guides/        ← 사용 가이드
```

---

<!-- 1기 종료 후 추가 예정
## 실제 결과

> 이 시스템으로 교육받은 30명의 성과

| 수강생 | Before | After |
|:---|:---|:---|
| A님 | ... | ... |
| B님 | ... | ... |
| C님 | ... | ... |
-->

---

## 이 시스템을 직접 구축하고 싶다면

이 레포는 뼈대입니다.
뼈대만으로는 작동하지 않습니다 — 당신의 사업 데이터, 전략, 콘텐츠 공식을 채워 넣어야 합니다.

이 뼈대에 살을 붙이는 전체 과정을 CEO가 직접 라이브로 보여드립니다.

**→ 부트캠프 라이브 (링크는 에이나우 공식 채널에서 공지)**

---

## License

MIT License — 자유롭게 포크하고 수정하세요.

## Star History

이 레포가 도움이 됐다면 Star를 눌러주세요.
