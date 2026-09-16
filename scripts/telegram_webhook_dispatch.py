"""Webhook 발행 요청 처리. Telegram 수신과 Blogger OAuth 실행을 분리한다."""
import json
import os
import re
import sys
import requests
from blogger_publisher import publish_draft


def send(text):
    token = os.environ['TELEGRAM_BOT_TOKEN']
    try:
        response = requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
                                 json={'chat_id': os.environ['TELEGRAM_CHAT_ID'], 'text': text}, timeout=20)
        if not response.ok or not response.json().get('ok'):
            raise RuntimeError('Telegram 회신 실패')
    except requests.RequestException:
        raise RuntimeError('Telegram 연결 실패') from None


def main():
    with open(os.environ['GITHUB_EVENT_PATH'], encoding='utf-8') as stream:
        event = json.load(stream)
    if event.get('action') != 'telegram_blog_publish':
        raise ValueError('지원하지 않는 이벤트')
    post_id = str(event.get('client_payload', {}).get('post_id', ''))
    if not re.fullmatch(r'[0-9]{1,30}', post_id):
        raise ValueError('잘못된 Blogger 글 번호')
    result = publish_draft(post_id)
    if not result.get('ok'):
        send(f'🚨 [QA+] 발행 실패\n글 번호: {post_id}\nGitHub 실행 로그를 확인해 주세요.')
        raise RuntimeError('Blogger 공개 발행 실패')
    send(f"✅ [QA+] 공개 발행 완료\n\n📌 {result.get('title') or '블로그 글'}\n🔗 {result.get('url') or ''}")
    print(json.dumps({'ok': True, 'post_id': post_id, 'url': result.get('url'),
                      'already_live': result.get('already_live', False)}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('::error::Webhook 발행 처리 실패. 비밀값 보호를 위해 예외 원문을 출력하지 않습니다.')
        sys.exit(1)
