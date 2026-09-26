# Jarvis PC 에이전트 (구독형 모델)

Claude Pro, ChatGPT Plus, Google AI Pro(Gemini) 구독을 API 키 없이 공식 CLI 로그인으로 사용해 Jarvis 자유 질문에 답합니다.

## 동작
- PC 에이전트가 3초마다 Worker에 질문이 있는지 확인합니다(에이전트 전용 토큰).
- 질문이 오면 학습 기억을 불러와 페르소나 프롬프트로 구독 모델에 묻고, 답을 Telegram으로 보냅니다.
- 답변 후 Claude Haiku가 새로 알게 된 사용자 정보를 추출해 기억에 병합합니다.
- PC가 꺼져 있으면(최근 20초간 확인 없음) 질문은 GitHub Actions(OpenAI API)로 갑니다. 에이전트가 60초 안에 가져가지 않거나 6분 안에 끝내지 못해도 Actions로 자동 전환됩니다.

## 모델 선택
| 질문 | 모델 |
|---|---|
| 일반 질문 | Claude Sonnet (Pro) |
| 코드·엑셀 수식·스크립트 | ChatGPT/Codex (Plus) |
| 최신 정보(뉴스, 개정, 시세, 날씨 등) | Gemini (AI Pro, 웹 검색) |
| `@claude`, `@gpt`, `@gemini` 로 시작 | 지정 모델 |
| `@all` 로 시작 | 세 모델 답 비교 |

한 모델이 사용 한도에 걸리거나 실패하면 다음 모델로 넘어가고, 답변 끝에 사용한 모델을 표시합니다.

## 안전장치
- CLI는 도구 없이 답변 텍스트만 생성합니다(Claude `--tools ""`, Codex `--sandbox read-only`, Gemini `--approval-mode plan`).
- 자식 프로세스에서 API 키 환경변수를 제거해 구독 로그인만 사용합니다.
- Claude는 `--setting-sources project,local` 로 사용자 전역 설정의 모델 재지정(opus/크레딧 모델)을 적용하지 않습니다. 전역 설정 파일은 수정하지 않습니다.
- 로그(`%LOCALAPPDATA%\JarvisAgent\agent.log`)에는 질문·답변 원문을 남기지 않습니다.

## 설치
```powershell
powershell -ExecutionPolicy Bypass -File agent\jarvis-local\install.ps1 -WorkerUrl https://qaplus-jarvis-webhook.<subdomain>.workers.dev
# config.json의 agentToken을 Worker Secret으로 등록
(Get-Content $env:LOCALAPPDATA\JarvisAgent\config.json | ConvertFrom-Json).agentToken | npx wrangler secret put JARVIS_AGENT_TOKEN --config workers/jarvis-webhook/wrangler.jsonc
```
Gemini는 터미널에서 `gemini` 를 한 번 실행해 Google 계정으로 로그인하면 10분 안에 자동으로 합류합니다.

## 관리
- 상태: `Get-ScheduledTask JarvisAgent`, 로그: `Get-Content $env:LOCALAPPDATA\JarvisAgent\agent.log -Tail 20`
- 중지: `Stop-ScheduledTask JarvisAgent` / 제거: `Unregister-ScheduledTask JarvisAgent` 후 `npx wrangler secret delete JARVIS_AGENT_TOKEN`
