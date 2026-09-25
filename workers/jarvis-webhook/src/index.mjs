const MAX_UPDATE_BYTES = 65_536;
const MAX_VOICE_BYTES = 20 * 1024 * 1024;
const MAX_VOICE_SECONDS = 300;
const CALLBACK_TTL_SECONDS = 48 * 60 * 60;

export const HELP = [
  'Jarvis 개인 비서 봇',
  '',
  '• 최근 중요 메일 브리핑해줘',
  '• 오늘 할 일 보여줘',
  '• 위 명령을 Telegram 음성 메시지로 말하기',
  '',
  '메일 발송, 삭제, 일정 확정은 하지 않습니다.',
  '답장 초안은 브리핑의 승인 버튼을 누른 경우에만 Gmail 임시보관함에 만듭니다.',
].join('\n');

function normalizedText(value) {
  return typeof value === 'string' ? value.trim().replace(/\s+/g, ' ') : '';
}

export function classify(update, chatId) {
  if (!Number.isSafeInteger(update?.update_id)) return {kind: 'invalid'};
  const callback = update.callback_query;
  const message = callback?.message || update.message;
  if (!chatId || String(message?.chat?.id) !== String(chatId)) return {kind: 'forbidden'};

  if (callback) {
    if (typeof callback.id !== 'string' || callback.id.length > 200) return {kind: 'invalid'};
    const data = typeof callback.data === 'string' ? callback.data : '';
    if (new TextEncoder().encode(data).length > 64) return {kind: 'invalid'};
    const match = /^d:([A-Za-z0-9_-]{5,32}):([0-9a-z]{1,10}):([A-Za-z0-9_-]{16})$/.exec(data);
    return {
      kind: match ? 'draft_callback' : 'unknown_callback',
      callback_id: callback.id,
      callback_data: data,
      message_id: match?.[1],
      expires: match?.[2],
      signature: match?.[3],
    };
  }

  const voice = message?.voice;
  if (voice) {
    if (typeof voice.file_id !== 'string' || !voice.file_id || voice.file_id.length > 512) return {kind: 'invalid'};
    const fileSize = Number(voice.file_size || 0);
    const duration = Number(voice.duration || 0);
    if (fileSize > MAX_VOICE_BYTES || duration > MAX_VOICE_SECONDS) return {kind: 'voice_too_large'};
    return {kind: 'voice', file_id: voice.file_id, duration: Math.max(0, Math.trunc(duration))};
  }

  const text = normalizedText(message?.text);
  if (!text) return {kind: 'ignore'};
  if (/^\/(?:help|start)(?:@\w+)?$/i.test(text) || text === '도움말') return {kind: 'help'};
  if (text === '최근 중요 메일 브리핑해줘' || text === '중요 메일 브리핑') return {kind: 'command', command: 'briefing'};
  if (text === '오늘 할 일 보여줘' || text === '오늘 할 일') return {kind: 'command', command: 'today_tasks'};
  return {kind: 'unknown'};
}

function base64UrlDecode(value) {
  const padded = value.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - value.length % 4) % 4);
  const raw = atob(padded);
  return Uint8Array.from(raw, character => character.charCodeAt(0));
}

export async function verifyDraftCallback(action, secret, nowMs = Date.now()) {
  if (action.kind !== 'draft_callback' || !secret) return false;
  const expiresMinutes = Number.parseInt(action.expires, 36);
  if (!Number.isSafeInteger(expiresMinutes)) return false;
  const nowSeconds = Math.floor(nowMs / 1000);
  const expiresSeconds = expiresMinutes * 60;
  if (expiresSeconds < nowSeconds || expiresSeconds > nowSeconds + CALLBACK_TTL_SECONDS + 120) return false;

  let provided;
  try { provided = base64UrlDecode(action.signature); } catch { return false; }
  const payload = `d:${action.message_id}:${action.expires}`;
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(secret), {name: 'HMAC', hash: 'SHA-256'}, false, ['sign'],
  );
  const digest = new Uint8Array(await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(payload))).slice(0, 12);
  if (provided.length !== digest.length) return false;
  let difference = 0;
  for (let index = 0; index < digest.length; index += 1) difference |= digest[index] ^ provided[index];
  return difference === 0;
}

export async function callbackApprovalId(callbackData) {
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(callbackData)));
  return Array.from(digest.slice(0, 12), byte => byte.toString(16).padStart(2, '0')).join('');
}

export function dedupeKey(action, updateId) {
  if (action.kind === 'draft_callback' && action.approval_id) return `draft:${action.approval_id}`;
  if (action.callback_id) return `callback:${action.callback_id}`;
  return `update:${updateId}`;
}

async function telegram(env, method, payload) {
  const response = await fetch(`https://api.telegram.org/bot${env.JARVIS_TELEGRAM_BOT_TOKEN}/${method}`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(5000),
  });
  let data;
  try { data = await response.json(); } catch { data = null; }
  if (!response.ok || !data?.ok) throw new Error(`telegram_${method}_${response.status}`);
}

async function dispatch(env, eventType, clientPayload) {
  const response = await fetch(`https://api.github.com/repos/${env.GITHUB_REPOSITORY}/dispatches`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.JARVIS_DISPATCH_TOKEN}`,
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'qaplus-jarvis-webhook',
    },
    body: JSON.stringify({event_type: eventType, client_payload: clientPayload}),
    signal: AbortSignal.timeout(8000),
  });
  if (response.status !== 204) throw new Error(`dispatch_${response.status}`);
}

function dispatchRequest(action) {
  if (action.kind === 'command') {
    return ['jarvis_command', {command: action.command, telegram_update_id: action.update_id}];
  }
  if (action.kind === 'voice') {
    return ['jarvis_voice_command', {
      voice_file_id: action.file_id,
      voice_duration: action.duration,
      telegram_update_id: action.update_id,
    }];
  }
  if (action.kind === 'draft_callback') {
    return ['jarvis_create_draft', {
      approval: action.callback_data,
      approval_id: action.approval_id,
      telegram_update_id: action.update_id,
    }];
  }
  return null;
}

export default {
  async fetch(request, env) {
    const path = new URL(request.url).pathname;
    const required = [
      'JARVIS_TELEGRAM_BOT_TOKEN', 'JARVIS_TELEGRAM_CHAT_ID', 'JARVIS_WEBHOOK_SECRET',
      'JARVIS_DISPATCH_TOKEN', 'GITHUB_REPOSITORY',
    ];
    const ready = required.every(name => Boolean(env[name])) && Boolean(env.JARVIS_UPDATES);
    if (path === '/health' && request.method === 'GET') return Response.json({ok: ready}, {status: ready ? 200 : 503});
    if (path !== '/telegram') return new Response('Not found', {status: 404});
    if (request.method !== 'POST') return new Response('Method not allowed', {status: 405});
    if (!ready) return new Response('Not ready', {status: 503});
    if (request.headers.get('X-Telegram-Bot-Api-Secret-Token') !== env.JARVIS_WEBHOOK_SECRET) {
      return new Response('Forbidden', {status: 403});
    }

    const body = await request.text();
    if (new TextEncoder().encode(body).length > MAX_UPDATE_BYTES) return new Response('Too large', {status: 413});
    let update;
    try { update = JSON.parse(body); } catch { return new Response('Invalid JSON', {status: 400}); }
    const action = classify(update, env.JARVIS_TELEGRAM_CHAT_ID);
    if (action.kind === 'invalid') return new Response('Invalid update', {status: 400});
    if (action.kind === 'draft_callback') {
      if (!await verifyDraftCallback(action, env.JARVIS_WEBHOOK_SECRET)) action.kind = 'invalid_callback';
      else action.approval_id = await callbackApprovalId(action.callback_data);
    }
    if (['forbidden', 'ignore'].includes(action.kind)) return Response.json({ok: true, ignored: true});

    const key = dedupeKey(action, update.update_id);
    return env.JARVIS_UPDATES.getByName(key).fetch('https://internal/process', {
      method: 'POST',
      body: JSON.stringify({...action, update_id: update.update_id}),
    });
  },
};

export class JarvisUpdate {
  constructor(ctx, env) { this.ctx = ctx; this.env = env; }

  async fetch(request) {
    const action = await request.json();
    return this.ctx.blockConcurrencyWhile(async () => {
      if (await this.ctx.storage.get('done')) return Response.json({ok: true, duplicate: true});
      const say = text => telegram(this.env, 'sendMessage', {chat_id: this.env.JARVIS_TELEGRAM_CHAT_ID, text});
      const answer = text => telegram(this.env, 'answerCallbackQuery', {callback_query_id: action.callback_id, text});
      try {
        const requestToDispatch = dispatchRequest(action);
        if (requestToDispatch) {
          if (!await this.ctx.storage.get('acknowledged')) {
            try {
              if (action.callback_id) await answer('승인을 확인했습니다. Gmail 초안 생성 요청을 접수합니다.');
              else if (action.kind === 'voice') await say('음성 명령을 접수했습니다. 인식 후 결과를 보내드리겠습니다.');
              else await say('요청을 접수했습니다. 준비되는 대로 결과를 보내드리겠습니다.');
              await this.ctx.storage.put('acknowledged', true);
            } catch {
              console.warn(JSON.stringify({event: 'jarvis_ack_failed', kind: action.kind, update_id: action.update_id}));
            }
          }
          if (!await this.ctx.storage.get('dispatched')) {
            await dispatch(this.env, requestToDispatch[0], requestToDispatch[1]);
            await this.ctx.storage.put('dispatched', true);
          }
        } else if (action.kind === 'help') {
          await say(HELP);
        } else if (action.kind === 'voice_too_large') {
          await say('음성 메시지는 5분, 20MB 이하만 처리합니다. 짧게 다시 보내주세요.');
        } else if (action.kind === 'unknown_callback' || action.kind === 'invalid_callback') {
          try { await answer('유효하지 않거나 만료된 승인 버튼입니다. 새 브리핑을 요청해주세요.'); } catch {}
        } else {
          await say(`지원하지 않는 명령입니다.\n\n${HELP}`);
        }
        await this.ctx.storage.put('done', true);
        await this.ctx.storage.setAlarm(Date.now() + 7 * 86400 * 1000);
        console.log(JSON.stringify({event: 'jarvis_processed', kind: action.kind, update_id: action.update_id}));
        return Response.json({ok: true});
      } catch {
        console.error(JSON.stringify({event: 'jarvis_processing_failed', kind: action.kind, update_id: action.update_id}));
        return new Response('Retry later', {status: 503});
      }
    });
  }

  async alarm() { await this.ctx.storage.deleteAll(); }
}
