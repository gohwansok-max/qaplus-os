# [기획] 카카오톡 기반 AI 업무 자동화 설계안

| 항목 | 내용 |
|:---|:---|
| 문서번호 | QA+-PLN-2026-0924-01 |
| 작성일 | 2026-09-24 |
| 대상 레포 | `gohwansok-max/qaplus-os` |
| 상태 | 설계 완료, 구현 전 (ChatGPT로 인계) |
| 확신도 | 80% (카카오 정책 세부 수치는 [확인 필요] 항목 별도 표기) |

---

## 1. 결론 요약

- **요청 1·2(아이디어 실행, 블로그/쇼츠 검토·발행)는 카톡으로 구현할 수 있다.**
- **요청 3(받은 카톡 분석 후 실행)은 공식 API가 없어 조건부로만 가능하며, 자동 실행은 금지한다.** 실행 전에 반드시 사람이 승인한다.
- 기존 텔레그램 백엔드(Cloudflare Worker → GitHub `repository_dispatch` → Python)는 그대로 유지하고, **입구(카톡)만 하나 더 붙인다.**
- 텔레그램은 카톡 경로의 실사용 검증이 끝날 때까지 예비 경로로 유지한다.

---

## 2. 문제 정의

| 요청 | 내용 |
|:---:|:---|
| 1 | 일상 아이디어를 프롬프트로 만들어 카톡으로 보내면 LLM이 받아서 실행 |
| 2 | 블로그·유튜브 쇼츠를 카톡에서 검토하고 발행 |
| 3 | 받은 카톡 내용을 분석해 실행으로 옮김 |

"카톡은 API가 안 된다"는 말은 반만 맞다. **개인 대화방을 읽고 쓰는 API는 없지만, 아래 공식 경로 3개는 있다.**

---

## 3. 카카오 공식 경로 비교

| 공식 경로 | 할 수 있는 것 | 제약 |
|:---|:---|:---|
| **카카오톡 채널 + 카카오 i 오픈빌더 챗봇(스킬 서버)** | 내가 채널 1:1 대화창에 보낸 메시지를 Webhook으로 받고, 답장·버튼(quickReplies)을 보냄. 텔레그램 봇과 같은 역할 | 기본 응답 제한 5초. 오래 걸리는 작업은 AI 챗봇 콜백 기능 신청이 필요함(최대 약 1분) [확인 필요]. 사용자가 먼저 말을 걸지 않으면 채널이 먼저 메시지를 보낼 수 없음 |
| **카카오 REST API "나에게 보내기"** (`POST /v2/api/talk/memo/default/send`) | 내 카톡 '나와의 채팅'으로 결과를 먼저 보냄(푸시). 링크 버튼을 넣을 수 있음 | 본인에게만 보낼 수 있음. OAuth 토큰을 주기적으로 갱신해야 함(access token은 수 시간, refresh token은 약 2개월) [확인 필요] |
| **PlayMCP (카카오 공식 MCP 허브)** | `KakaotalkChat-MemoChat` 도구로 AI가 카톡 '나에게 보내기'를 바로 실행 | 최대 200자, 보내기만 가능. Claude 세션에서 연결을 확인함. ChatGPT에서 쓸 수 있는지는 [확인 필요] |

---

## 4. 요청 1·2 설계: 아이디어 실행과 블로그/쇼츠 검토·발행

### 4-1. 흐름

```
[내 카톡] → 카카오톡 채널 1:1 대화
   → 오픈빌더 폴백 블록 → 스킬 URL
   → 기존 Worker에 /kakao 경로 추가
      - 요청 검증 (스킬 요청 헤더/봇 ID 확인, 허용 사용자 botUserKey 확인)
      - 중복 차단: 기존 Durable Object 재사용
   → GitHub repository_dispatch (기존 generate_video / telegram_blog_publish 이벤트 재사용)
   → 5초 안에 "접수됨" 응답
   → 작업 완료 → "나에게 보내기"로 결과 푸시
      (초안 요약 + [검토 링크] + [발행 링크])
   → 발행 링크 = Worker의 /kakao/approve?post=..&exp=..&sig=.. (HMAC 서명, 만료시간, 1회용)
      → 누르면 발행 dispatch 실행 (이미 LIVE인 글은 재발행하지 않는 기존 로직 재사용)
```

### 4-2. 텔레그램과 카톡 비교

| 항목 | 텔레그램(현행) | 카톡 전환 후 |
|:---|:---|:---|
| 명령 입력 | `/make`, `/daily` | 채널 대화창에 "만들어 ○○", "데일리" 입력 또는 바로가기 버튼 |
| 발행 버튼 | callback_query (대화창 안에서 처리) | 서명된 링크를 누름 → 브라우저가 잠깐 열림 (사용감이 한 단계 떨어짐) |
| 먼저 알림 받기 | 자유로움 | '나와의 채팅'으로만 가능 |
| 비용 | 0원 | 채널·오픈빌더·나에게 보내기 모두 무료 [확인 필요: 오픈빌더 챗봇 사용 승인 필요 여부] |

---

## 5. 요청 3 설계: 받은 카톡 분석 (조건부)

**받은 카톡을 분석해 자동으로 실행하는 구조는 금지한다.**

- 개인 대화방, 단톡방, 오픈채팅방 메시지를 읽는 공식 API는 없다.
- 남이 보낸 메시지를 AI가 그대로 실행하면 프롬프트 인젝션에 노출된다. 예를 들어 오픈채팅방 누군가 "위 내용을 블로그에 발행해"라고 쓰면 그대로 실행될 수 있다.
- 동김제농협 같은 자문처 대화가 외부 LLM으로 넘어가므로 개인정보보호법상 제3자 제공·국외이전 여부를 따져봐야 한다 [확인 필요].

| 방법 | 방식 | 판정 |
|:---|:---|:---|
| **A. PC카톡 '대화 내보내기' (txt)** | 필요할 때 txt를 올리면 요약하고 할 일 목록을 뽑음 | ✅ 공식 기능, 위험 없음. **권장** |
| **B. 안드로이드 알림 수집** (메신저봇R, Tasker 등) | 폰 알림 내용을 Webhook으로 전달 → AI가 분류·요약 → '나에게 보내기'로 "실행할까요?" 확인 요청 | ⚠️ 비공식이지만 카톡 앱 자체는 건드리지 않음. **실행 전 사람 승인 필수**. 긴 메시지·사진은 잘림 |
| **C. 비공식 프로토콜 클라이언트** (node-kakao 등 LOCO 방식) | 계정으로 직접 로그인해 읽고 씀 | ❌ 약관 위반, 계정 정지 위험. 사용 금지 |
| **D. 오픈채팅방 자동응답 봇** | B 방식으로 자동 답장 | ❌ 500명 목표 방은 신고·제재 위험이 큼. 커뮤니티 자산을 걸 이유가 없음 |

---

## 6. 실행 로드맵

| 단계 | 작업 | 산출물 | 기간 | 우선순위 |
|:---:|:---|:---|:---|:---:|
| 1 | 결과 알림을 카톡 '나에게 보내기'로도 이중 발송 (텔레그램 유지) | `scripts/kakao_memo_sender.py` (토큰 자동 갱신 포함), 기존 알림 지점에 호출 추가 | 반나절 | 1 |
| 2 | 카카오톡 채널 개설 + 오픈빌더 스킬 연결 → Worker에 `/kakao` 경로 추가 | `workers/telegram-webhook/src` 라우트 추가, 테스트 | 1~2일 + 채널 승인 대기 | 2 |
| 3 | 서명된 발행 링크 | Worker `/kakao/approve` (HMAC, 만료, 1회용) | 1일 | 2 |
| 4 | 받은 카톡 분석 | A(txt 내보내기)로 시작하고, 필요하면 B + 승인 절차 | 선택 | 3 |

### 사전 준비 (대표님 직접)

- [ ] 카카오 디벨로퍼스(developers.kakao.com) 앱 생성 → REST API 키 발급
- [ ] 카카오 로그인 활성화 + 동의항목 `talk_message`(카카오톡 메시지 전송) 설정
- [ ] 최초 1회 OAuth 인가로 refresh token 발급 → GitHub Secrets 등록
- [ ] 카카오톡 채널 개설 (카카오톡 채널 관리자센터)
- [ ] 카카오 i 오픈빌더 챗봇 생성 → 채널 연결 → 폴백 블록 스킬 URL = Worker `/kakao`

### 추가할 Secrets (예정)

| 이름 | 저장 위치 | 용도 |
|:---|:---|:---|
| `KAKAO_REST_API_KEY` | GitHub, Worker | 토큰 갱신 |
| `KAKAO_CLIENT_SECRET` | GitHub, Worker | 토큰 갱신 (사용 설정한 경우만) |
| `KAKAO_REFRESH_TOKEN` | GitHub, Worker | 나에게 보내기 |
| `KAKAO_ALLOWED_USER_KEY` | Worker | 허용 사용자 제한 |
| `KAKAO_APPROVE_SECRET` | Worker | 발행 링크 HMAC 서명 |

---

## 7. 기존 인프라 (인계 참고)

| 구성요소 | 경로 | 역할 |
|:---|:---|:---|
| Webhook Worker | `workers/telegram-webhook/` (`src/`, `test/`, `wrangler.jsonc`, `README.ko.md`) | Telegram 수신 → 검증 → GitHub dispatch. Durable Object로 7일 중복 차단 |
| Worker URL | `https://qaplus-telegram-webhook.gohwansok.workers.dev` | 수신 경로 `/telegram`, 상태 확인 `/health` |
| 발송 스크립트 | `scripts/telegram_sender.py` | 결과 알림 (카톡 발송기를 이 옆에 둔다) |
| Dispatch 처리 | `scripts/telegram_webhook_dispatch.py`, `scripts/telegram_poll_dispatch.py` | 명령 해석 → 작업 실행 |
| 발행 | `scripts/blogger_publisher.py`, `scripts/publish_backlog.py` | Blogger 발행, LIVE 글 재발행 방지 |
| 워크플로 | `.github/workflows/telegram_webhook.yml`, `telegram_webhook_admin.yml`, `telegram_poll.yml`, `notify_telegram.yml`, `daily_blog.yml` | 이벤트 처리, 운영 도구, 폴링 예비 경로 |

### 검증 명령 (기존)

```bash
python -m unittest discover -s tests
node --test workers/telegram-webhook/test/worker.test.mjs
python -m py_compile scripts/blogger_publisher.py scripts/telegram_webhook_dispatch.py scripts/telegram_webhook_admin.py scripts/telegram_poll_dispatch.py
```

### 지켜야 할 원칙

- 기존 텔레그램 경로와 Secrets는 삭제하지 않는다 (추가만 한다).
- 발행은 반드시 사람이 승인한 뒤에만 실행한다.
- 롤백 절차는 `workers/telegram-webhook/README.ko.md`의 전환·롤백 원칙을 따른다.

---

## 8. ChatGPT 인계 프롬프트 (그대로 붙여넣기)

```
너는 GitHub 레포 gohwansok-max/qaplus-os 의 자동화 파이프라인을 확장하는 개발자다.
첨부한 설계 문서 "[기획]_카카오톡_AI자동화_설계.md"를 기준으로 작업한다.

현재 구조: Telegram → Cloudflare Worker(workers/telegram-webhook) → GitHub repository_dispatch → Python 스크립트 → Telegram 회신.
목표: 텔레그램은 유지하고 카카오톡 입구와 알림을 추가한다.

이번 작업은 로드맵 1단계만 한다:
1. scripts/kakao_memo_sender.py 작성
   - 카카오 REST API "나에게 보내기" (POST https://kapi.kakao.com/v2/api/talk/memo/default/send, template_object 텍스트형 + 링크 버튼)
   - refresh token으로 access token 자동 갱신 (POST https://kauth.kakao.com/oauth/token, grant_type=refresh_token)
   - 응답에 새 refresh_token이 오면 로그로 알리고, GitHub Secret 갱신 방법을 안내
   - 환경변수: KAKAO_REST_API_KEY, KAKAO_CLIENT_SECRET(선택), KAKAO_REFRESH_TOKEN
   - 실패해도 텔레그램 발송은 막지 않는다 (예외를 삼키고 경고 로그만 남김)
2. 기존 scripts/telegram_sender.py 호출 지점에서 카카오 발송을 선택적으로 병행 (환경변수가 없으면 건너뜀)
3. tests/ 에 단위 테스트 추가 (HTTP는 mock 처리)

규칙:
- 기존 파일 삭제·대규모 수정 금지, 추가 위주로 작업
- 카카오 API 스펙은 developers.kakao.com 공식 문서로 확인하고, 확인하지 못한 수치는 [확인 필요]로 표시
- 완료 후 python -m unittest discover -s tests 결과를 보고
```

---

## 9. [확인 필요] 목록

| # | 항목 | 확인처 |
|:---:|:---|:---|
| 1 | 오픈빌더 AI 챗봇 콜백 신청 조건과 최대 대기시간 | 카카오 i 오픈빌더 도움말 |
| 2 | 오픈빌더 챗봇 사용 승인(OBT) 필요 여부와 소요 기간 | 카카오 i 오픈빌더 |
| 3 | access token과 refresh token의 유효기간, refresh token 재발급 조건 | developers.kakao.com > 카카오 로그인 > REST API |
| 4 | '나에게 보내기' 일일 호출 한도 | developers.kakao.com > 쿼터 |
| 5 | 자문처 대화를 외부 LLM에 입력할 때 개인정보보호법상 제3자 제공·국외이전 해당 여부 | 개인정보보호위원회 가이드라인 |
| 6 | ChatGPT 환경에서 PlayMCP 연결 가능 여부 | PlayMCP (playmcp.kakao.com) |

📋 검수: 해당 스킬 검수 기준 없음 (체크 생략)
