const MAX_UPDATE_BYTES = 65_536;
const MAX_VOICE_BYTES = 20 * 1024 * 1024;
const MAX_VOICE_SECONDS = 300;
const CALLBACK_TTL_SECONDS = 48 * 60 * 60;
const MAX_QUERY_CHARS = 2000;
const MAX_MEMORY_BYTES = 256 * 1024;
const PENDING_TTL_MS = 24 * 60 * 60 * 1000;
const MEMORY_LABELS = {
  identity: '정체성·역할', personality: '성격·성향', tone_manner: '말투·톤앤매너',
  preferences: '선호 형식·작업 방식', direction: '목표·방향성', personal_history: '개인사',
  qa_expertise: '품질관리 전문성', ai_capability: 'AI 활용·AI 네이티브·바이브 코딩',
  skills: '반복 업무(스킬)', facts: '기억할 사실',
};

export const HELP = [
  'Jarvis 개인 비서 봇',
  '',
  '• 무엇이든 자유롭게 물어보세요. 대화할수록 말투·성향·전문성을 학습합니다.',
  '• /briefing 최근 중요 메일 브리핑',
  '• /today_tasks 오늘 할 일',
  '• /memory Jarvis가 기억하는 내용 보기',
  '• 기억해: (내용)  직접 기억시키기',
  '• 기억 수정: (내용)  잘못 기억한 것 바로잡기',
  '• /forget_all 학습한 기억 전체 삭제',
  '• 위 내용을 음성 메시지로 말해도 됩니다.',
  '',
  '메일 발송, 삭제, 일정 확정은 하지 않습니다.',
  '답장 초안은 브리핑의 승인 버튼을 누른 경우에만 Gmail 임시보관함에 만듭니다.',
].join('\n');

function normalizedText(value) {
  // 여러 줄 '기억해'를 위해 줄바꿈은 유지하고 줄 안의 공백만 정리한다.
  return typeof value === 'string'
    ? value.split('\n').map(line => line.trim().replace(/[ \t]+/g, ' ')).filter(Boolean).join('\n')
    : '';
}

const SECTION_ALIASES = [
  [/^(정체성|역할|identity)$/i, 'identity'],
  [/^(성격|성향|personality)$/i, 'personality'],
  [/^(말투|톤|톤앤매너|tone)$/i, 'tone_manner'],
  [/^(선호|형식|preferences?)$/i, 'preferences'],
  [/^(방향|방향성|목표|direction)$/i, 'direction'],
  [/^(개인사|경력|history)$/i, 'personal_history'],
  [/^(품질|품질관리|qa)$/i, 'qa_expertise'],
  [/^(ai|바이브코딩|ai네이티브)$/i, 'ai_capability'],
  [/^(스킬|업무|skills?)$/i, 'skills'],
  [/^(사실|기타|facts?)$/i, 'facts'],
];

// "[품질] 식품 QA 20년차" 처럼 줄마다 분류 태그를 붙이면 해당 항목에 저장한다. 태그가 없으면 기억할 사실.
export function parseNoteLines(body, correction = false) {
  const lines = String(body).split('\n').map(line => line.replace(/^[-*•]\s*/, '').trim()).filter(Boolean);
  if (!lines.length || lines.length > 30) return null;
  const items = [];
  for (const line of lines) {
    const tagged = /^\[([^\]]{1,12})\]\s*(.+)$/.exec(line);
    const section = tagged ? SECTION_ALIASES.find(([pattern]) => pattern.test(tagged[1].replace(/\s+/g, '')))?.[1] : 'facts';
    const text = (tagged ? tagged[2] : line).trim();
    if (!section || text.length < 2 || text.length > 300) return null;
    items.push({section, text: correction ? `정정: ${text}` : text});
  }
  return items;
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
  if (/^\/briefing(?:@\w+)?$/i.test(text)) return {kind: 'command', command: 'briefing'};
  if (/^\/today_tasks(?:@\w+)?$/i.test(text)) return {kind: 'command', command: 'today_tasks'};
  if (/^\/memory(?:@\w+)?$/i.test(text)) return {kind: 'memory_show'};
  if (/^\/forget_all(?:@\w+)?$/i.test(text)) return {kind: 'memory_reset'};

  const note = /^(?:\/remember(?:@\w+)?|기억해(?:줘|둬)?|기억\s*수정)\s*[:：]?\s*([\s\S]+)$/i.exec(text);
  if (note) {
    const items = parseNoteLines(note[1], /^기억\s*수정/.test(text));
    if (!items) return {kind: 'memory_note_invalid'};
    return {kind: 'memory_note', items};
  }

  // 띄어쓰기·문장부호를 무시하고 짧은 명령만 내장 명령으로 본다. 긴 문장은 자유 질문으로 보낸다.
  const compact = text.toLowerCase().replace(/[\s.!?~,。！？]+/g, '');
  if (compact.length <= 15 && /(브리핑|briefing)/.test(compact)) return {kind: 'command', command: 'briefing'};
  if (compact.length <= 15 && /(오늘할일|할일보여|오늘업무)/.test(compact)) return {kind: 'command', command: 'today_tasks'};

  if (text.length > MAX_QUERY_CHARS) return {kind: 'query_too_long'};
  return {kind: 'general_query', text};
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
  if (action.kind === 'general_query') {
    // 공개 저장소의 Actions 이벤트에 질문 원문을 싣지 않는다. 원문은 JarvisMemory에 잠시 보관한다.
    return ['jarvis_general_query', {telegram_update_id: action.update_id}];
  }
  return null;
}

const encoder = new TextEncoder();

export async function memoryToken(secret) {
  const key = await crypto.subtle.importKey('raw', encoder.encode(secret), {name: 'HMAC', hash: 'SHA-256'}, false, ['sign']);
  const digest = new Uint8Array(await crypto.subtle.sign('HMAC', key, encoder.encode('jarvis-memory-v1')));
  return Array.from(digest, byte => byte.toString(16).padStart(2, '0')).join('');
}

function safeEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  let difference = 0;
  for (let index = 0; index < a.length; index += 1) difference |= a.charCodeAt(index) ^ b.charCodeAt(index);
  return difference === 0;
}

function memoryStub(env) {
  return env.JARVIS_MEMORY.getByName('owner');
}

async function memoryCall(env, op, body = {}) {
  const response = await memoryStub(env).fetch(`https://internal/${op}`, {method: 'POST', body: JSON.stringify(body)});
  const data = await response.json().catch(() => ({}));
  return {status: response.status, data};
}

export function formatMemory(doc) {
  const profile = doc && typeof doc.profile === 'object' && doc.profile ? doc.profile : {};
  const lines = ['Jarvis가 기억하는 내용'];
  let total = 0;
  for (const [key, label] of Object.entries(MEMORY_LABELS)) {
    const items = Array.isArray(profile[key]) ? profile[key].filter(item => item && typeof item.text === 'string') : [];
    if (!items.length) continue;
    total += items.length;
    const ordered = [...items.filter(item => item.pinned), ...items.filter(item => !item.pinned)];
    lines.push('', `[${label}]`, ...ordered.slice(0, 10).map(item => `- ${item.text.slice(0, 200)}${item.pinned ? ' (직접 기억)' : ''}`));
  }
  if (!total) return '아직 기억한 내용이 없습니다. 대화하거나 "기억해: ..."로 알려주세요.';
  const conversations = Number(doc?.stats?.conversations) || 0;
  lines.push('', `누적 대화 ${conversations}회, 기억 항목 ${total}개`);
  return lines.join('\n').slice(0, 3900);
}

function normalizeKey(text) {
  return String(text).toLowerCase().replace(/[\s.,!?·~"'()[\]-]+/g, '');
}

export function addPinnedNote(doc, text, section = 'facts') {
  if (!Object.hasOwn(MEMORY_LABELS, section)) section = 'facts';
  doc.profile = doc.profile && typeof doc.profile === 'object' ? doc.profile : {};
  const items = Array.isArray(doc.profile[section]) ? doc.profile[section] : [];
  const now = new Date().toISOString().replace(/\.\d+Z$/, '+00:00');
  const existing = items.find(item => item && normalizeKey(item.text) === normalizeKey(text));
  if (existing) {
    existing.pinned = true;
    existing.count = (Number(existing.count) || 1) + 1;
    existing.updated = now;
  } else {
    items.push({text, count: 1, updated: now, pinned: true});
  }
  doc.profile[section] = [...items.filter(item => item?.pinned).slice(-50), ...items.filter(item => item && !item.pinned)];
  return doc;
}

function emptyMemory() {
  return {version: 1, rev: 0, profile: {}, turns: [], stats: {conversations: 0, learned_items: 0}};
}

async function handleMemoryApi(request, env, path) {
  const expected = await memoryToken(env.JARVIS_WEBHOOK_SECRET);
  const provided = (request.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '');
  if (!safeEqual(provided, expected)) return new Response('Forbidden', {status: 403});

  if (path === '/memory' && request.method === 'GET') {
    const {data} = await memoryCall(env, 'get');
    return Response.json({doc: data.doc});
  }
  if (path === '/memory' && request.method === 'PUT') {
    const body = await request.text();
    if (encoder.encode(body).length > MAX_MEMORY_BYTES) return new Response('Too large', {status: 413});
    let parsed;
    try { parsed = JSON.parse(body); } catch { return new Response('Invalid JSON', {status: 400}); }
    if (!parsed || typeof parsed.doc !== 'object' || !Number.isSafeInteger(parsed.expected_rev)) {
      return new Response('Invalid memory', {status: 400});
    }
    const {status, data} = await memoryCall(env, 'put', parsed);
    return Response.json(data, {status});
  }
  if (path === '/memory/pending/take' && request.method === 'POST') {
    let parsed;
    try { parsed = await request.json(); } catch { return new Response('Invalid JSON', {status: 400}); }
    if (!Number.isSafeInteger(parsed?.update_id)) return new Response('Invalid update', {status: 400});
    const {status, data} = await memoryCall(env, 'pending-take', {update_id: parsed.update_id});
    return Response.json(data, {status});
  }
  return new Response('Not found', {status: 404});
}

export default {
  async fetch(request, env) {
    const path = new URL(request.url).pathname;
    const required = [
      'JARVIS_TELEGRAM_BOT_TOKEN', 'JARVIS_TELEGRAM_CHAT_ID', 'JARVIS_WEBHOOK_SECRET',
      'JARVIS_DISPATCH_TOKEN', 'GITHUB_REPOSITORY',
    ];
    const ready = required.every(name => Boolean(env[name])) && Boolean(env.JARVIS_UPDATES) && Boolean(env.JARVIS_MEMORY);
    if (path === '/health' && request.method === 'GET') return Response.json({ok: ready}, {status: ready ? 200 : 503});
    if (path === '/memory' || path.startsWith('/memory/')) {
      if (!ready) return new Response('Not ready', {status: 503});
      return handleMemoryApi(request, env, path);
    }
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
              else if (action.kind === 'general_query') await say('질문을 받았습니다. 답변을 준비하고 있습니다.');
              else await say('요청을 접수했습니다. 준비되는 대로 결과를 보내드리겠습니다.');
              await this.ctx.storage.put('acknowledged', true);
            } catch {
              console.warn(JSON.stringify({event: 'jarvis_ack_failed', kind: action.kind, update_id: action.update_id}));
            }
          }
          if (!await this.ctx.storage.get('dispatched')) {
            if (action.kind === 'general_query') {
              const stored = await memoryCall(this.env, 'pending-put', {update_id: action.update_id, text: action.text});
              if (stored.status !== 200) throw new Error('pending_store_failed');
            }
            await dispatch(this.env, requestToDispatch[0], requestToDispatch[1]);
            await this.ctx.storage.put('dispatched', true);
          }
        } else if (action.kind === 'help') {
          await say(HELP);
        } else if (action.kind === 'memory_show') {
          const {data} = await memoryCall(this.env, 'get');
          await say(formatMemory(data.doc));
        } else if (action.kind === 'memory_note') {
          const {status} = await memoryCall(this.env, 'note', {items: action.items});
          if (status !== 200) throw new Error('memory_note_failed');
          const listed = action.items.map(item => `- [${MEMORY_LABELS[item.section]}] ${item.text}`).join('\n');
          await say(`기억했습니다 (${action.items.length}건):\n${listed}`.slice(0, 3900));
        } else if (action.kind === 'memory_note_invalid') {
          await say([
            '기억할 내용을 이해하지 못했습니다. 한 줄에 2~300자, 최대 30줄까지 가능합니다.',
            '예)',
            '기억해:',
            '[품질] 식품 품질관리 20년차',
            '[선호] 보고서는 결론부터',
            '분류: 정체성, 성격, 말투, 선호, 방향, 개인사, 품질, AI, 스킬, 사실',
          ].join('\n'));
        } else if (action.kind === 'memory_reset') {
          await memoryCall(this.env, 'reset');
          await say('학습한 기억을 모두 삭제했습니다.');
        } else if (action.kind === 'query_too_long') {
          await say(`질문은 ${MAX_QUERY_CHARS}자 이내로 보내주세요.`);
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

// 사용자 1명의 장기 기억(프로필·최근 대화)과 처리 대기 중인 질문 원문을 보관한다.
export class JarvisMemory {
  constructor(ctx, env) { this.ctx = ctx; this.env = env; }

  async fetch(request) {
    const op = new URL(request.url).pathname.slice(1);
    let body = {};
    try { body = await request.json(); } catch {}
    return this.ctx.blockConcurrencyWhile(async () => {
      const storage = this.ctx.storage;
      if (op === 'get') {
        return Response.json({doc: (await storage.get('doc')) || emptyMemory()});
      }
      if (op === 'put') {
        const current = (await storage.get('doc')) || emptyMemory();
        const currentRev = Number(current.rev) || 0;
        if (body.expected_rev !== currentRev) return Response.json({error: 'conflict', rev: currentRev}, {status: 409});
        const doc = {...body.doc, rev: currentRev + 1};
        await storage.put('doc', doc);
        return Response.json({rev: doc.rev});
      }
      if (op === 'note') {
        const items = Array.isArray(body.items) ? body.items.slice(0, 30) : [];
        const valid = items.filter(item => typeof item?.text === 'string' && item.text.trim().length >= 2);
        if (!valid.length) return Response.json({error: 'invalid'}, {status: 400});
        let doc = (await storage.get('doc')) || emptyMemory();
        for (const item of valid) doc = addPinnedNote(doc, item.text.trim().slice(0, 300), item.section);
        doc.rev = (Number(doc.rev) || 0) + 1;
        await storage.put('doc', doc);
        return Response.json({rev: doc.rev});
      }
      if (op === 'reset') {
        const current = (await storage.get('doc')) || emptyMemory();
        await storage.put('doc', {...emptyMemory(), rev: (Number(current.rev) || 0) + 1});
        return Response.json({ok: true});
      }
      if (op === 'pending-put') {
        if (!Number.isSafeInteger(body.update_id) || typeof body.text !== 'string') return Response.json({error: 'invalid'}, {status: 400});
        const now = Date.now();
        const old = await storage.list({prefix: 'pending:'});
        for (const [key, value] of old) if (now - (Number(value?.at) || 0) > PENDING_TTL_MS) await storage.delete(key);
        await storage.put(`pending:${body.update_id}`, {text: body.text.slice(0, MAX_QUERY_CHARS), at: now});
        return Response.json({ok: true});
      }
      if (op === 'pending-take') {
        const key = `pending:${body.update_id}`;
        const value = await storage.get(key);
        if (!value) return Response.json({error: 'not_found'}, {status: 404});
        await storage.delete(key);
        return Response.json({text: value.text});
      }
      return Response.json({error: 'unknown_op'}, {status: 404});
    });
  }
}
