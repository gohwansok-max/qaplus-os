"""수동 운영 도구. 비밀값은 GitHub Secrets에서만 주입하고 출력하지 않는다."""
import json
import os
import sys
import time
import requests

WORKER = 'qaplus-telegram-webhook'
ACCOUNT = 'ff60de4c6d6aa9e84aa7c07a72a7d057'


def checked(method, url, **kwargs):
    response = requests.request(method, url, timeout=30, **kwargs)
    if not response.ok:
        raise RuntimeError(f'외부 요청 실패 HTTP {response.status_code}')
    return response


def tg(method, payload=None):
    result = checked('POST', f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/{method}",
                     json=payload or {}).json()
    if not result.get('ok'):
        raise RuntimeError('Telegram API 실패')
    return result.get('result')


def status():
    info = tg('getWebhookInfo')
    print(json.dumps({k: info.get(k) for k in ('url', 'pending_update_count', 'last_error_date',
                                               'last_error_message', 'max_connections', 'allowed_updates')}))


def main():
    mode = os.environ['ADMIN_MODE']
    base = os.environ.get('WEBHOOK_BASE_URL', '').rstrip('/')
    if mode == 'sync_secrets':
        # GitHub 내부에서 Cloudflare 비밀 저장소로 직접 전달. 로컬/로그로 반출하지 않는다.
        for name in ('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'QA_DISPATCH_TOKEN', 'WEBHOOK_SECRET'):
            result = checked('PUT', f'https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/workers/scripts/{WORKER}/secrets',
                             headers={'Authorization': f"Bearer {os.environ['CF_BOOTSTRAP_TOKEN']}"},
                             json={'name': name, 'text': os.environ[name], 'type': 'secret_text'}).json()
            if not result.get('success'):
                raise RuntimeError('Cloudflare Secret 등록 실패')
            print(f'{name}: 등록 성공')
    elif mode == 'enable':
        checked('GET', base + '/health')
        try:
            tg('setWebhook', {'url': base + '/telegram', 'secret_token': os.environ['WEBHOOK_SECRET'],
                              'allowed_updates': ['message', 'callback_query'], 'max_connections': 5,
                              'drop_pending_updates': False})
            if tg('getWebhookInfo').get('url') != base + '/telegram':
                raise RuntimeError('Webhook 주소 확인 실패')
        except Exception:
            tg('deleteWebhook', {'drop_pending_updates': False})
            raise
        status()
    elif mode == 'rollback':
        tg('deleteWebhook', {'drop_pending_updates': False})
        status()
    elif mode == 'status':
        status()
    elif mode == 'prepare_test':
        from blogger_publisher import publish_post
        result = publish_post('[QA PLUS 운영검증] Telegram webhook 발행 테스트',
                              '<p>Telegram 승인 발행 경로를 검증하기 위한 임시 테스트 글입니다. 검증 후 임시저장으로 회수합니다.</p>',
                              labels=['시스템 운영검증'], is_draft=True)
        if not result.get('ok'):
            raise RuntimeError('테스트 임시저장 실패')
        post_id = result['post_id']
        msg = tg('sendMessage', {'chat_id': os.environ['TELEGRAM_CHAT_ID'],
             'text': f'🧪 QA PLUS webhook 운영 검증용 글\n글 번호: {post_id}\n보류 확인 후 발행하기를 테스트합니다.',
             'reply_markup': {'inline_keyboard': [[{'text': '발행하기', 'callback_data': f'blog_publish:{post_id}'},
                                                   {'text': '보류', 'callback_data': f'blog_hold:{post_id}'}]]}})
        print(json.dumps({'test_post_id': post_id, 'message_id': msg['message_id']}))
    elif mode in ('verify_post', 'revert_test'):
        from blogger_publisher import get_access_token, BLOGGER_API_BASE
        post_id = os.environ['TEST_POST_ID']
        if not post_id.isdigit():
            raise ValueError('잘못된 글 번호')
        url = f"{BLOGGER_API_BASE}/blogs/{os.environ['BLOGGER_BLOG_ID']}/posts/{post_id}"
        headers = {'Authorization': f'Bearer {get_access_token()}'}
        post = checked('GET', url, params={'view': 'ADMIN'}, headers=headers).json()
        if mode == 'revert_test':
            if post.get('title') != '[QA PLUS 운영검증] Telegram webhook 발행 테스트':
                raise ValueError('검증 전용 글만 회수 가능')
            post = checked('POST', url + '/revert', headers=headers).json()
        elif post.get('status') == 'LIVE':
            checked('GET', post['url'])
        print(json.dumps({k: post.get(k) for k in ('id', 'status', 'title', 'url')}, ensure_ascii=False))
    elif mode == 'smoke':
        endpoint = base + '/telegram'
        headers = {'X-Telegram-Bot-Api-Secret-Token': os.environ['WEBHOOK_SECRET']}
        seed = int(time.time() * 1000)
        chat = os.environ['TELEGRAM_CHAT_ID']
        invalid = requests.post(endpoint, json={}, timeout=20)
        assert invalid.status_code == 403
        print('잘못된 Secret 차단: PASS')
        foreign = checked('POST', endpoint, headers=headers, json={'update_id': seed,
                          'message': {'chat': {'id': 'unauthorized-test'}, 'text': '/help'}}).json()
        assert foreign.get('ignored')
        print('다른 CHAT_ID 차단: PASS')
        for number, text in enumerate(('/help', 'webhook 운영검증용 일반 텍스트')):
            update = {'update_id': seed + number + 1, 'message': {'chat': {'id': chat}, 'text': text}}
            started = time.monotonic()
            result = checked('POST', endpoint, headers=headers, json=update).json()
            assert result.get('ok')
            print(f'명령 테스트 {number + 1}: PASS, {time.monotonic() - started:.3f}초')
            duplicate = checked('POST', endpoint, headers=headers, json=update).json()
            assert duplicate.get('duplicate')
            print('동일 update 재전송 차단: PASS')
        status()
    else:
        raise ValueError('지원하지 않는 운영 모드')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('::error::운영 도구 실패. 비밀값 보호를 위해 응답/예외 원문은 기록하지 않습니다.')
        sys.exit(1)
