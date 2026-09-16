export const HELP = '👋 큐에이플러스 AI 영상 제작 봇\n\n/make [주제] : 원하는 주제로 쇼츠 제작\n/daily : 다음 주제로 쇼츠 제작\n/help : 도움말\n\n블로그 검토 메시지에서 발행하기 또는 보류를 선택하세요.\n명령은 즉시 접수되며 실제 작업은 GitHub 실행 대기 후 시작됩니다.';

export function classify(update, chatId) {
  if (!Number.isSafeInteger(update?.update_id)) return {kind: 'invalid'};
  const cb = update.callback_query;
  const msg = cb?.message || update.message;
  if (!chatId || String(msg?.chat?.id) !== String(chatId)) return {kind: 'forbidden'};
  if (cb) {
    if (typeof cb.id !== 'string' || cb.id.length > 200) return {kind: 'invalid'};
    const match = /^(blog_publish|blog_hold):(\d{1,30})$/.exec(cb.data || '');
    return {kind: match ? match[1] : 'unknown_callback', post_id: match?.[2], callback_id: cb.id};
  }
  const text = typeof msg.text === 'string' ? msg.text.trim() : '';
  if (!text) return {kind: 'ignore'};
  if (/^\/(?:help|start)(?:@\w+)?$/i.test(text) || text === '도움말') return {kind: 'help'};
  if (/^\/daily(?:@\w+)?$/i.test(text) || ['오늘영상', '오늘'].includes(text)) return {kind: 'video', topic: ''};
  const match = /^(?:\/make(?:@\w+)?(?=\s|$)|만들어줘:?)(.*)$/is.exec(text);
  if (match) {
    const topic = match[1].trim().replace(/^[\[\]'"\s]+|[\[\]'"\s]+$/g, '');
    return topic ? {kind: 'video', topic} : {kind: 'help'};
  }
  return {kind: 'unknown'};
}

async function telegram(env, method, payload) {
  const res = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/${method}`, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload),
    signal: AbortSignal.timeout(5000),
  });
  const data = await res.json();
  if (!res.ok || !data.ok) throw new Error(`telegram_${method}_${res.status}`);
}

export default {
  async fetch(request, env) {
    const path = new URL(request.url).pathname;
    const ready = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'QA_DISPATCH_TOKEN', 'WEBHOOK_SECRET'].every(k => !!env[k]);
    if (path === '/health' && request.method === 'GET') return Response.json({ok: ready}, {status: ready ? 200 : 503});
    if (path !== '/telegram') return new Response('Not found', {status: 404});
    if (request.method !== 'POST') return new Response('Method not allowed', {status: 405});
    if (!ready) return new Response('Not ready', {status: 503});
    if (request.headers.get('X-Telegram-Bot-Api-Secret-Token') !== env.WEBHOOK_SECRET) return new Response('Forbidden', {status: 403});
    const body = await request.text();
    if (body.length > 65536) return new Response('Too large', {status: 413});
    let update;
    try { update = JSON.parse(body); } catch { return new Response('Invalid JSON', {status: 400}); }
    const action = classify(update, env.TELEGRAM_CHAT_ID);
    if (action.kind === 'invalid') return new Response('Invalid update', {status: 400});
    if (['forbidden', 'ignore'].includes(action.kind)) return Response.json({ok: true, ignored: true});
    // Callback ID also deduplicates repeated deliveries carrying a different update ID.
    const key = action.callback_id ? `callback:${action.callback_id}` : `update:${update.update_id}`;
    return env.UPDATES.getByName(key).fetch('https://internal/process', {
      method: 'POST', body: JSON.stringify({...action, update_id: update.update_id}),
    });
  },
};

export class TelegramUpdate {
  constructor(ctx, env) { this.ctx = ctx; this.env = env; }
  async fetch(request) {
    const action = await request.json();
    return this.ctx.blockConcurrencyWhile(async () => {
      if (await this.ctx.storage.get('done')) return Response.json({ok: true, duplicate: true});
      const env = this.env;
      const say = text => telegram(env, 'sendMessage', {chat_id: env.TELEGRAM_CHAT_ID, text});
      const answer = text => telegram(env, 'answerCallbackQuery', {callback_query_id: action.callback_id, text});
      try {
        if (['video', 'blog_publish'].includes(action.kind)) {
          if (!await this.ctx.storage.get('dispatched')) {
            const payload = action.kind === 'video'
              ? {event_type: 'generate_video', client_payload: {topic: action.topic, telegram_update_id: action.update_id}}
              : {event_type: 'telegram_blog_publish', client_payload: {post_id: action.post_id, update_id: action.update_id}};
            const res = await fetch(`https://api.github.com/repos/${env.GITHUB_REPOSITORY}/dispatches`, {
              method: 'POST', headers: {'Authorization': `Bearer ${env.QA_DISPATCH_TOKEN}`, 'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'qaplus-telegram-webhook'},
              body: JSON.stringify(payload), signal: AbortSignal.timeout(8000),
            });
            if (res.status !== 204) throw new Error(`dispatch_${res.status}`);
            await this.ctx.storage.put('dispatched', true);
          }
          // A failed acknowledgement must never re-dispatch a successful job.
          try {
            if (action.callback_id) await answer('발행 요청을 접수했습니다. 완료되면 공개 URL을 보내드립니다.');
            else await say(`🚀 접수 완료\n주제: ${action.topic || '큐의 다음 주제'}\n영상 제작을 시작합니다. 완성되면 이 방으로 도착합니다.`);
          } catch { console.warn(JSON.stringify({event: 'ack_failed', update_id: action.update_id})); }
        } else if (action.kind === 'blog_hold') {
          // Old callbacks may expire; the permanent chat response still confirms the hold.
          try { await answer('보류했습니다. 글은 임시저장 상태로 유지됩니다.'); } catch {}
          await say(`⏸ 보류했습니다. Blogger 글 ${action.post_id}의 상태는 변경하지 않았습니다.`);
        } else if (action.kind === 'unknown_callback') {
          try { await answer('지원하지 않는 버튼입니다.'); } catch {}
        } else await say(action.kind === 'help' ? HELP : '알 수 없는 명령입니다. /help 로 사용법을 확인하세요.');
        await this.ctx.storage.put('done', true);
        await this.ctx.storage.setAlarm(Date.now() + 7 * 86400 * 1000);
        console.log(JSON.stringify({event: 'processed', kind: action.kind, update_id: action.update_id}));
        return Response.json({ok: true});
      } catch {
        console.error(JSON.stringify({event: 'processing_failed', kind: action.kind, update_id: action.update_id}));
        return new Response('Retry later', {status: 503});
      }
    });
  }
  async alarm() { await this.ctx.storage.deleteAll(); }
}
