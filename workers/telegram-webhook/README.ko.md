# Telegram webhook 운영

Telegram → Cloudflare Worker → 필요한 GitHub repository_dispatch → 기존 Python 처리 → Telegram 결과 회신.

- `/help`, 잘못된 명령, 보류: Worker에서 처리하므로 Actions 실행 없음.
- `/make [주제]`, `/daily`: 기존 `generate_video` 이벤트 1회.
- 발행 버튼: `telegram_blog_publish` 이벤트 1회. 글별 실행을 직렬화하고 Blogger LIVE 상태이면 재발행하지 않음.
- Worker URL: https://qaplus-telegram-webhook.gohwansok.workers.dev
- 수신 경로 `/telegram`, 준비 상태 `/health`.
- 허용 CHAT_ID와 Telegram secret header 검증. Blogger 비밀값은 GitHub에만 유지.
- Durable Object가 update ID 또는 callback ID를 7일간 저장하여 재전송/동시 중복 요청을 차단.
- GitHub 전달 실패는 HTTP 503으로 Telegram 재전송을 유도. 전달 성공 이후 Telegram ACK 실패는 재실행하지 않음.
- 네트워크 단절이 GitHub 접수 직후 발생하는 극단적 상황에서는 dispatch 재전송 가능성이 있음. Blogger 공개 상태 검사로 재발행 방지. 영상 작업의 완전한 exactly-once 보장은 아님.
- 같은 글에서 새로 버튼을 누르는 동작은 별도 이벤트이며 공개 상태 확인 후 기존 URL 회신.

## 배포

`npx wrangler deploy --config workers/telegram-webhook/wrangler.jsonc`

Worker Secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `QA_DISPATCH_TOKEN`, `WEBHOOK_SECRET`.
GitHub에 동일한 `WEBHOOK_SECRET`과 `WEBHOOK_BASE_URL` variable을 둔다.
초기 이관은 수동 `telegram_webhook_admin.yml`의 `sync_secrets`로 GitHub → Cloudflare Secrets에 직접 전달한다.
이관용 `CF_BOOTSTRAP_TOKEN`은 일회성 연결용이며 이관 직후 GitHub에서 삭제한다.
기존 Secrets는 삭제하지 않는다.

## 전환 순서

1. polling schedule 유지 상태에서 Worker/발행 workflow 배포 및 Secrets 설정.
2. 수동 운영 도구 `status`, `smoke`로 준비 상태·인증·CHAT_ID·응답·중복 차단 검증.
3. `enable`로 webhook 등록. pending update는 버리지 않는다.
4. `prepare_test`로 검증 전용 draft와 버튼을 보낸다.
5. Telegram에서 `/help`, 일반 텍스트, 보류, 발행 버튼을 실제 실행.
6. 발행 workflow 성공, 공개 URL 회신, `verify_post`의 LIVE 및 공개 페이지 HTTP 200 확인.
7. 검증 완료 후에만 polling schedule 제거. `revert_test`로 검증 전용 글을 draft로 회수.

## 롤백

1. 수동 운영 workflow `telegram_webhook_admin.yml`에서 `mode=rollback` 실행.
   `deleteWebhook(drop_pending_updates=false)` 후 URL이 비어 있는지 확인.
2. 기존 `telegram_poll.yml`을 수동 실행하여 명령/버튼 처리 정상 확인.
3. 지속 복구가 필요하면 `telegram_poll.yml`의 `on.schedule`에 `cron: '*/5 * * * *'`를 복원하여 main에 반영.
4. `daily_blog.yml`과 Blogger Secrets는 변경하지 않는다.

## 검증 명령

`python -m unittest discover -s tests`

`node --test workers/telegram-webhook/test/worker.test.mjs`

`python -m py_compile scripts/blogger_publisher.py scripts/telegram_webhook_dispatch.py scripts/telegram_webhook_admin.py scripts/telegram_poll_dispatch.py`

## 참고 문서

- [Telegram Bot API](https://core.telegram.org/bots/api#setwebhook)
- [Cloudflare Durable Objects](https://developers.cloudflare.com/durable-objects/best-practices/rules-of-durable-objects/)
- [GitHub concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
