# 🚀 INSTALL — 3분 설치 가이드

> 압축 파일(`ai-ceo-os-v1.0.zip`)을 받으셨다면, 이 문서 하나만 보면 됩니다.
> 3분 안에 김이사가 첫 브리핑을 드립니다.

---

## 필요한 것

1. **컴퓨터** (Windows / macOS / Linux 아무거나)
2. **Node.js** (16 이상) — 없으면 [nodejs.org](https://nodejs.org)에서 LTS 설치
3. **Claude API 사용 권한** — Claude Code가 쓸 수 있는 계정 (Claude Pro 또는 Anthropic API 키)
4. **Git** (선택) — GitHub 백업 쓰려면 필요, 안 쓰면 생략 가능

---

## Step 1. 압축 해제 (1분)

### Windows
1. `ai-ceo-os-v1.0.zip` 우클릭 → "압축 풀기"
2. 원하는 위치 선택 (예: `C:\Users\YourName\projects\`)
3. 폴더 확인: `ai-ceo-os` 폴더가 생겼으면 OK

### macOS / Linux
```bash
unzip ai-ceo-os-v1.0.zip -d ~/projects/
cd ~/projects/ai-ceo-os
```

---

## Step 2. Claude Code 설치 (최초 1회, 1분)

이미 깔려 있다면 건너뛰세요.

```bash
npm install -g @anthropic-ai/claude-code
```

설치 확인:
```bash
claude --version
```

버전 숫자가 나오면 OK.

> 문제 발생 시 → `guides/00_클로드코드_설치.md` 참조

---

## Step 3. 폴더 안에서 Claude Code 실행 (10초)

```bash
cd ai-ceo-os    # 압축 해제한 폴더로 이동
claude          # Claude Code 실행
```

Claude Code 화면이 뜹니다.

---

## Step 4. 자동 셋업 (5분)

Claude Code 안에 입력:

```
/setup
```

AI가 당신의 사업에 대해 **5~7개 질문**을 합니다. 답변만 하면 됩니다.

**"모르겠어요"도 유효한 답**입니다. AI가 업종 기본값을 자동 적용합니다.

5분 후:
- `CLAUDE.md` (당신 사업 정보가 가득 채워진 AI 두뇌)
- `context/ceo-persona.md` (당신의 톤앤매너)
- `context/mission-vision.md`, `channel-rules.md`
- `CEO/목표.md`, `일정_마감.md`, `아이디어.md`
- `tasks/todo.md` (첫 미션 포함)
- 기타 파일들

...이 자동 생성됩니다.

---

## Step 5. 설치 자가 진단 (30초)

`/setup` 완료 후 터미널에서:

### Windows (PowerShell)
```powershell
.\scripts\doctor.ps1
```

### macOS / Linux
```bash
bash scripts/doctor.sh
```

**모든 체크가 ✓로 통과**하면 준비 완료.

---

## Step 6. 김이사 첫 호출 (즉시)

Claude Code 안에서:

```
/kim-director
```

김이사(CSO)가 당신의 사업을 스캔하고 **선제 브리핑**을 드립니다.

축하합니다. 🎉 당신만의 AI 경영 OS가 가동 중입니다.

---

## 막혔을 때

| 증상 | 해결 |
|:---|:---|
| `claude` 명령어 없음 | Step 2 Claude Code 설치 재확인. 또는 `npx @anthropic-ai/claude-code` |
| `/setup` 실행 중 에러 | `.claude/settings.json` 권한 확인. `Read`, `Write`, `Edit`, `Bash` 허용 필요 |
| "CMO 소집" 시 서브에이전트 안 나옴 | `.claude/agents/cmo.md` 파일 존재 확인. 없으면 압축 해제 재수행 |
| `doctor.sh` 실행 안 됨 (macOS) | `chmod +x scripts/doctor.sh` 먼저 |
| 한글 폴더명 `examples/1인-프리랜서-디자이너/` 깨짐 | 압축 해제 도구를 **유니코드 지원 버전**으로 (7-Zip 권장, Windows 기본은 OK) |

---

## 다음에 읽을 것

- [`examples/1인-프리랜서-디자이너/README.md`](examples/1인-프리랜서-디자이너/README.md) — "채워진 레포는 이렇게 생겼습니다" 샘플
- [`guides/onboarding.md`](guides/onboarding.md) — 첫 30분 / 첫 1주 / 첫 1달 로드맵
- [`guides/customization.md`](guides/customization.md) — 본격 커스터마이징
- [`skills/README.md`](skills/README.md) — 5개 풀 공개 스킬 목록
- [`workflows/examples/`](workflows/examples/) — 실제 작동하는 파이프라인 3개

---

## 이 자료에 대해

- **제공**: 에이나우 (AINOW)
- **버전**: v1.0 (2026-04-08)
- **라이선스**: MIT (`LICENSE` 파일 참조)
- **공식 채널**: 에이나우 부트캠프에서 라이브 구축 과정 공개

문의/피드백은 에이나우 공식 채널로 부탁드립니다.

**반드시 좋은 사업 되세요.** 🚀
