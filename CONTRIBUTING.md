# Contributing to ai-ceo-os

ai-ceo-os에 기여해주셔서 감사합니다! 이 문서는 기여 방법을 안내합니다.

---

## 이 프로젝트에 기여하는 방법

ai-ceo-os는 **"1인 CEO가 AI 임원 팀과 일하는 방식"**을 오픈소스로 공개한 레포입니다. 기여는 다음 형태로 환영합니다:

### 1. 새 업종 예시 추가 (가장 환영)
`examples/` 폴더에 본인 업종의 완성본을 PR로 올리세요.

현재 있는 예시:
- `examples/1인-프리랜서-디자이너/`

환영하는 예시:
- `examples/카페-운영자/`
- `examples/1인-코칭-사업자/`
- `examples/쇼핑몰-셀러/`
- `examples/B2B-SaaS-1인/`
- `examples/유튜버/`
- `examples/작가/`

**포함해야 할 것** (1인-프리랜서-디자이너 참고):
- `README.md` — 페르소나 소개
- `CLAUDE.md` — 사업 정의 (슬롯 100% 채움)
- `context/ceo-persona.md`, `channel-rules.md`, `mission-vision.md`
- `tasks/lessons.md`, `predictions.md`, `todo.md` (실제 운영 중 모습)
- `skills/` 하위 본인 업종 전용 커스텀 스킬 1개+

### 2. 스킬 개선
기존 `skills/` 스킬의 검수 기준 추가/수정, 품질 향상.

### 3. 번역
`README_EN.md` 외 영문 문서 추가 또는 다른 언어 지원.

### 4. 버그 리포트
Issue로 등록. 템플릿 사용 권장.

### 5. 문서 개선
오타, 깨진 링크, 설명 보강 등.

---

## PR 프로세스

1. Fork → 브랜치 생성 (`feature/my-example` 또는 `fix/typo-xyz`)
2. 변경사항 커밋 (`git commit -m "feat: add cafe owner example"`)
3. 푸시 → PR 생성
4. PR 템플릿 작성
5. 리뷰 → 머지

### 커밋 메시지 컨벤션 (Conventional Commits 느슨한 버전)

- `feat:` 새 기능/예시 추가
- `fix:` 버그 수정
- `docs:` 문서 변경
- `refactor:` 리팩토링
- `chore:` 잡일 (의존성, 설정)
- `example:` 새 업종 예시

---

## 기여 전 체크리스트

### 모든 PR 공통
- [ ] 내 변경사항이 기존 구조(9명 C-Suite, cognitive-core, 3-Tier)와 충돌하지 않는가
- [ ] `CHANGELOG.md`에 변경사항 1줄 추가했는가
- [ ] 민감정보(실명, 전화번호, API 키, 실제 수익)가 포함되지 않았는가

### 새 예시 PR
- [ ] 페르소나가 **가상**이고 "이것은 허구"가 README에 명시되었는가
- [ ] 슬롯이 100% 채워졌는가 (`{{...}}` 남아있으면 안 됨)
- [ ] 9명 전원 사용이 아니어도 됨 — 본인 업종에 맞는 3~5명만 집중 가능

### 새 스킬 PR
- [ ] 검수 기준(E1~E8+) 포함
- [ ] 필수/권장 구분 명확
- [ ] 합격 기준 명시

---

## 코드 스타일

- **Markdown**: 80자 자동 줄바꿈 금지, 표는 그대로
- **Python**: PEP 8, Black 포맷팅 (실행 가능한 스크립트는 `#!/usr/bin/env python3` 헤더 필수)
- **Shell**: `#!/usr/bin/env bash` + `set -euo pipefail`
- **파일명**: 한글 폴더명 허용 (examples/ 하위). 영문은 `kebab-case`.

---

## 질문이 있다면

1. 먼저 기존 Issue 검색
2. 없으면 새 Issue 생성
3. 템플릿 사용

---

## 행동 강령

이 프로젝트는 [Contributor Covenant](https://www.contributor-covenant.org/) 행동 강령을 따릅니다. 자세한 내용은 `CODE_OF_CONDUCT.md` 참조.

---

## 감사합니다

여러분의 기여가 "1인 CEO도 시스템으로 일한다"는 문화를 만듭니다.
