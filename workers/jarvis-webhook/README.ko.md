# 개인용 Jarvis Telegram 봇 1차 MVP

기존 QA+ 콘텐츠 봇과 완전히 분리된 개인 비공개 봇이다.

```text
개인 Telegram 봇
  → 별도 Cloudflare Worker (`qaplus-jarvis-webhook`)
  → 별도 repository_dispatch 이벤트
  → `.github/workflows/jarvis.yml`
  → Gmail 조회 / AI 요약 / Gmail Draft 생성
  → 개인 Telegram 봇 회신
```

> 이 문서는 설정 절차만 제공한다. Worker 배포, Secret 등록, Gmail OAuth 승인, Telegram webhook 등록은 자동 실행하지 않는다.

## 구현 범위

- 허용된 `JARVIS_TELEGRAM_CHAT_ID`의 텍스트와 Telegram 음성 메시지만 처리
- 텍스트 명령
  - `최근 중요 메일 브리핑해줘`
  - `오늘 할 일 보여줘`
- 음성 메시지를 파일 단위로 내려받아 음성인식 후 같은 명령 분류
- 평일 오전 7:30 KST 최근 24시간 중요 메일 브리핑
- 광고, 뉴스레터, 자동 알림 기본 제외
- 브리핑에 발신자, 제목, 수신 시각, 핵심 요청, 마감일, 답장 필요 여부만 표시
- 답장이 필요하다고 분류된 메일에 `답장 초안 만들기` 버튼 표시
- 유효한 서명과 만료시간을 가진 버튼 승인 후에만 Gmail Draft 생성
- 사용자가 Gmail 임시보관함에서 직접 검토하고 발송

## 의도적으로 구현하지 않은 기능

- 이메일 직접 발송
- 이메일 삭제, 읽음 처리, 라벨 변경 등 메일 수정
- 자동 일정 등록 또는 일정 확정
- 상시 음성 청취, 통화형 기능
- 기존 QA+ 봇, Worker, Secret, Blogger 발행 흐름 변경

## 보안 설계

- 새 Worker, Bot Token, GitHub dispatch token, Secret 이름을 기존 QA+와 분리한다.
- 허용된 개인 `chat_id` 외 요청은 응답 없이 무시한다.
- Telegram webhook의 `X-Telegram-Bot-Api-Secret-Token`을 확인한다.
- Durable Object가 Telegram update ID 또는 callback ID를 7일간 보관해 중복 dispatch를 차단한다.
- 답장 callback에는 Gmail 원문을 넣지 않는다. Gmail message ID, 만료시각, HMAC 서명만 넣고 Telegram의 64바이트 제한 안에서 검증한다.
- Worker와 GitHub Actions가 승인 HMAC, 만료시간, 승인 해시를 각각 다시 검증한다. dispatch token만으로 Draft 생성을 우회할 수 없다.
- 같은 승인 해시를 Durable Object, Actions concurrency, Gmail Draft의 `X-Jarvis-Approval-ID`에 사용해 반복 클릭과 dispatch 재시도의 중복 Draft를 막는다.
- 발신 이메일 주소와 개인 표시 이름은 마스킹하고, OpenAI와 Telegram에 전달하기 전에 이메일·전화번호·식별번호·비밀키·토큰·OTP·금융번호·URL 패턴을 숨긴다.
- Gmail 본문은 인용문을 줄이고 최대 길이를 제한한 뒤 AI 요약 및 답장 초안 작성에만 사용하며 Actions 로그나 Telegram에 원문을 출력하지 않는다.
- AI 시스템 프롬프트는 이메일 본문을 신뢰할 수 없는 참고자료로 선언하며 본문 속 명령을 실행하지 않는다.
- `OPENAI_API_KEY`는 GitHub Actions Secrets에만 저장한다. Cloudflare Worker에는 저장하지 않는다.
- 코드의 Gmail API allowlist는 `messages.list/get`, `drafts.list/get/create`만 허용한다.

## Gmail 최소 OAuth 범위

필요 범위는 다음 두 개다.

```text
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.compose
```

- `gmail.readonly`: 메일 목록과 원문 조회
- `gmail.compose`: Gmail Draft 생성

Google 공식 문서상 `users.drafts.create`는 `gmail.compose`를 허용하고, `users.messages.get`은 `gmail.readonly`를 허용한다.

주의: `gmail.compose` 범위 자체는 Gmail 전송도 허용한다. 더 작은 공식 범위로 원문 읽기와 일반 Draft 생성을 동시에 충족할 수 없으므로 이 범위를 사용하되, 코드에서 `/send` API를 제공하지 않고 allowlist와 단위 테스트로 차단한다. 중복 방지를 위해 Draft 목록과 개별 Draft 조회도 사용하지만 Draft 삭제·수정·전송은 구현하지 않는다.

공식 문서:

- https://developers.google.com/workspace/gmail/api/auth/scopes
- https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/get
- https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.drafts/create

## 필요한 Secrets

### Cloudflare Worker Secrets

| 이름 | 용도 |
|---|---|
| `JARVIS_TELEGRAM_BOT_TOKEN` | 개인 Jarvis Telegram Bot Token |
| `JARVIS_TELEGRAM_CHAT_ID` | 허용할 개인 chat ID |
| `JARVIS_WEBHOOK_SECRET` | Telegram webhook header 검증 및 승인 callback HMAC 키 |
| `JARVIS_DISPATCH_TOKEN` | 이 저장소에 `repository_dispatch`를 생성할 전용 GitHub token |

Worker 일반 변수:

| 이름 | 값 |
|---|---|
| `GITHUB_REPOSITORY` | `gohwansok-max/qaplus-os` |

### GitHub Actions Secrets

| 이름 | 용도 |
|---|---|
| `JARVIS_TELEGRAM_BOT_TOKEN` | 음성 파일 다운로드와 결과 회신 |
| `JARVIS_TELEGRAM_CHAT_ID` | 결과를 보낼 개인 chat ID |
| `JARVIS_WEBHOOK_SECRET` | 답장 승인 callback 서명 생성 |
| `OPENAI_API_KEY` | 음성인식, 메일 요약, 답장 초안 생성. GitHub에만 저장 |
| `GMAIL_CLIENT_ID` | Google OAuth Desktop client ID |
| `GMAIL_CLIENT_SECRET` | Google OAuth Desktop client secret |
| `GMAIL_REFRESH_TOKEN` | 위 최소 범위로 발급한 개인 Gmail refresh token |

선택 GitHub Secrets:

- `JARVIS_OPENAI_MODEL`: 기본값 `gpt-4.1-mini`을 바꿀 때만 사용
- `JARVIS_TRANSCRIPTION_MODEL`: 기본값 `gpt-4o-mini-transcribe`를 바꿀 때만 사용

현재 workflow는 모델명을 Secret으로 전달하지 않으므로 모델을 바꾸려면 workflow env도 함께 추가한다.

## 1. Telegram 개인 봇 준비

1. Telegram의 `@BotFather`에서 기존 QA+ 봇과 다른 새 봇을 만든다.
2. 새 Bot Token을 안전한 로컬 비밀관리 도구에 저장한다.
3. 새 봇에게 개인 계정으로 메시지를 한 번 보낸다.
4. 로컬 PC에서 `getUpdates`를 호출해 개인 대화의 `message.chat.id`를 확인한다. 응답에는 개인 메시지가 포함될 수 있으므로 파일이나 CI 로그로 저장하지 않는다.
5. 확인한 값을 `JARVIS_TELEGRAM_CHAT_ID`로 사용한다.

Telegram 공식 제한:

- webhook `secret_token`: 1~256자, 영문·숫자·`_`·`-`
- `callback_data`: 1~64바이트
- Bot API 음성 파일 다운로드: 최대 20MB

공식 문서: https://core.telegram.org/bots/api

## 2. Google OAuth 준비

1. Google Cloud Console에서 전용 프로젝트를 선택하거나 만든다.
2. Gmail API를 사용 설정한다.
3. OAuth 동의 화면을 구성하고 본인 Google 계정을 테스트 사용자로 추가한다.
4. `OAuth client ID`를 `Desktop app` 유형으로 만든다.
5. OAuth 2.0 Playground에서 설정 아이콘의 `Use your own OAuth credentials`를 켜고 위 Client ID/Secret을 입력한다.
6. 다음 두 범위만 입력해 승인한다.

```text
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.compose
```

7. Authorization code를 token으로 교환하고 refresh token을 확인한다.
8. Client ID, Client Secret, refresh token을 각각 GitHub Actions Secret으로 등록한다.
9. 브라우저 화면, 셸 기록, 메모, 저장소 파일에 refresh token을 남기지 않는다.
10. 개인 Gmail의 최소화·마스킹된 일부 본문이 OpenAI API로 전송된다는 점과 조직의 개인정보 처리정책을 확인한 뒤에만 `OPENAI_API_KEY`를 등록한다. 민감 메일을 외부 AI로 처리할 수 없다면 이 MVP를 활성화하지 않는다.

OAuth 연결과 외부 AI 처리 승인은 사용자가 범위와 정책을 직접 확인한 뒤 진행한다. 이 구현 작업에서는 실제 승인을 수행하지 않는다.

## 3. GitHub dispatch token 준비

기존 QA+ token을 재사용하지 않는다.

1. 만료기간이 짧은 Fine-grained personal access token을 만든다.
2. Repository access를 `gohwansok-max/qaplus-os` 하나로 제한한다.
3. Repository permissions에서 `Contents: Read and write`만 부여한다. GitHub의 repository dispatch 생성에 필요한 권한이다.
4. Cloudflare에 `JARVIS_DISPATCH_TOKEN`으로 등록한다.

## 4. GitHub Actions Secrets 등록

저장소의 `Settings → Secrets and variables → Actions`에서 다음 Secret을 각각 등록한다.

```text
JARVIS_TELEGRAM_BOT_TOKEN
JARVIS_TELEGRAM_CHAT_ID
JARVIS_WEBHOOK_SECRET
OPENAI_API_KEY
GMAIL_CLIENT_ID
GMAIL_CLIENT_SECRET
GMAIL_REFRESH_TOKEN
```

기존 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `QA_DISPATCH_TOKEN`, Blogger Secrets는 수정하거나 삭제하지 않는다.

## 5. Cloudflare Worker Secrets 등록

아래 명령은 저장소 루트에서 사용자가 직접 실행한다. 각 명령은 값을 대화형으로 입력받는다.

```powershell
npx wrangler secret put JARVIS_TELEGRAM_BOT_TOKEN --config workers/jarvis-webhook/wrangler.jsonc
npx wrangler secret put JARVIS_TELEGRAM_CHAT_ID --config workers/jarvis-webhook/wrangler.jsonc
npx wrangler secret put JARVIS_WEBHOOK_SECRET --config workers/jarvis-webhook/wrangler.jsonc
npx wrangler secret put JARVIS_DISPATCH_TOKEN --config workers/jarvis-webhook/wrangler.jsonc
```

`JARVIS_WEBHOOK_SECRET`는 Telegram 제한에 맞는 URL-safe 값으로 만든다. 예: PowerShell에서 로컬로 생성하되 출력값은 Secret 등록 후 안전하게 폐기한다.

```powershell
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
[Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+','-').Replace('/','_')
```

## 6. Worker 배포

사용자 확인 후 다음 명령을 직접 실행한다.

```powershell
npx wrangler deploy --config workers/jarvis-webhook/wrangler.jsonc
```

배포 후 다음 주소를 확인한다.

```text
https://<jarvis-worker-domain>/health
```

`{"ok":true}`가 아니면 webhook을 등록하지 않는다.

## 7. Telegram webhook 등록

Worker URL과 로컬 환경변수를 준비한 뒤 사용자가 직접 실행한다.

```powershell
$workerUrl = "https://<jarvis-worker-domain>/telegram"
$body = @{
  url = $workerUrl
  secret_token = $env:JARVIS_WEBHOOK_SECRET
  allowed_updates = @("message", "callback_query")
  drop_pending_updates = $false
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "https://api.telegram.org/bot$env:JARVIS_TELEGRAM_BOT_TOKEN/setWebhook" `
  -ContentType "application/json" `
  -Body $body
```

기존 QA+ bot의 webhook은 변경하지 않는다. Bot Token이 다르므로 두 webhook은 독립적이다.

## 8. 수동 검증 순서

1. GitHub Actions의 `Jarvis 개인 비서` workflow를 `briefing`으로 수동 실행한다.
2. Telegram에서 `최근 중요 메일 브리핑해줘`를 보낸다.
3. `오늘 할 일 보여줘`를 보낸다.
4. 5분, 20MB 이하 음성 메시지로 같은 명령을 말한다.
5. 브리핑의 `답장 초안 만들기` 버튼을 누른다.
6. Gmail 임시보관함에 Draft만 생겼는지 확인한다.
7. 보낸편지함에 새 메일이 없는지 확인한다.
8. 기존 QA+ 명령과 Blogger 발행 흐름이 그대로 동작하는지 별도 확인한다.

## 예약 실행

`.github/workflows/jarvis.yml`은 GitHub cron 기준 `30 22 * * 0-4`로 설정되어 있다.

- UTC: 일요일~목요일 22:30
- KST: 월요일~금요일 07:30

GitHub schedule은 혼잡 상황에서 수 분 지연될 수 있다.

## 로컬 테스트

```powershell
python -m pip install requests
python -m unittest discover -s tests
node --test workers/jarvis-webhook/test/worker.test.mjs
python -m py_compile scripts/jarvis_gmail.py scripts/jarvis_ai.py scripts/jarvis_telegram.py scripts/jarvis_dispatch.py
```

## 파일 구성

```text
workers/jarvis-webhook/
  src/index.mjs
  test/worker.test.mjs
  package.json
  wrangler.jsonc
  README.ko.md
scripts/
  jarvis_gmail.py
  jarvis_ai.py
  jarvis_telegram.py
  jarvis_dispatch.py
tests/
  test_jarvis_gmail.py
  test_jarvis_ai.py
  test_jarvis_telegram.py
  test_jarvis_dispatch.py
.github/workflows/jarvis.yml
```
