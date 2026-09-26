const MAX_UPDATE_BYTES = 65_536;
const MAX_VOICE_BYTES = 20 * 1024 * 1024;
const MAX_VOICE_SECONDS = 300;
const CALLBACK_TTL_SECONDS = 48 * 60 * 60;
const MAX_QUERY_CHARS = 2000;
// PC 에이전트(구독 CLI)가 최근 이 시간 안에 폴링했으면 질문을 에이전트에 맡긴다.
const AGENT_FRESH_MS = 20 * 1000;
// 에이전트가 이 시간 안에 가져가지 않거나 끝내지 못하면 GitHub Actions(API)로 넘긴다.
const AGENT_CLAIM_TIMEOUT_MS = 60 * 1000;
const AGENT_WORK_TIMEOUT_MS = 6 * 60 * 1000;
const PAIR_TTL_MS = 10 * 60 * 1000;
const MAX_PENDING_PAIRS = 3;
const MAX_DEVICES = 5;
const MAX_MEMORY_BYTES = 256 * 1024;
const PENDING_TTL_MS = 24 * 60 * 60 * 1000;
// 작업 기준(이름 붙인 답변 규칙). 학습 기억(doc)과 별도 키에 저장해 /forget_all, 구버전 에이전트 저장에 영향받지 않는다.
const MAX_STANDARDS = 30;
const MAX_STANDARD_BODY = 1500;
const STANDARD_NAME = /^[\w가-힣 .·()+&-]{1,30}$/;
// 파일 저장: 마지막 답변 전문(학습 기억 turns는 900자로 잘림)과 저장 요청 스냅숏.
const MAX_LAST_CHARS = 12000;
const MAX_SAVE_TITLE = 60;
const SAVE_TTL_MS = 24 * 60 * 60 * 1000;
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
  '• /status 또는 "점검"  PC 에이전트·모델·기억·Actions 상태 점검',
  '• 저장해줘 (또는 "저장해줘: 제목")  직전 답변을 Google Drive "Jarvis 저장함"에 md 파일로 저장',
  '• 기억해: (내용)  직접 기억시키기',
  '• 기억 수정: (내용)  잘못 기억한 것 바로잡기',
  '• /forget_all 학습한 기억 전체 삭제 (작업 기준은 유지)',
  '',
  '작업 기준 (반복 업무의 답변 규칙)',
  '• 기준 저장: 이름 (다음 줄부터 본문)  같은 이름이면 덮어씀',
  '• /standards 기준 목록  • 기준 보기: 이름  • 기준 삭제: 이름',
  '• 질문에 기준 이름이나 #이름을 넣으면 그 기준을 적용해 답합니다.',
  '',
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

// "기준 저장: 이름\n본문" 또는 "기준 저장: 이름 / 본문". 이름 1~30자, 본문 2~1500자.
export function parseStandard(body) {
  const raw = String(body).trim();
  const newline = raw.indexOf('\n');
  let name;
  let text;
  if (newline >= 0) {
    name = raw.slice(0, newline);
    text = raw.slice(newline + 1);
  } else {
    const slash = raw.indexOf(' / ');
    if (slash < 0) return null;
    name = raw.slice(0, slash);
    text = raw.slice(slash + 3);
  }
  name = name.replace(/^#/, '').trim();
  text = text.trim();
  if (!STANDARD_NAME.test(name) || text.length < 2 || text.length > MAX_STANDARD_BODY) return null;
  return {name, body: text};
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
    const pair = /^pair(no)?:([0-9a-f]{8})$/.exec(data);
    if (pair) return {kind: 'pair_callback', callback_id: callback.id, approve: !pair[1], pair_id: pair[2]};
    const unpair = /^unpair:([0-9a-f]{12})$/.exec(data);
    if (unpair) return {kind: 'unpair_callback', callback_id: callback.id, device: unpair[1]};
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
  if (/^\/devices(?:@\w+)?$/i.test(text)) return {kind: 'devices_show'};
  const save = /^(?:\/save(?:@\w+)?|저장(?:해줘|해|하기)?|파일로\s*저장(?:해줘)?)(?:\s*[:：]\s*([^\n]+))?$/i.exec(text);
  if (save) {
    const title = (save[1] || '').trim();
    if (title.length > MAX_SAVE_TITLE) return {kind: 'save_invalid'};
    return {kind: 'save_output', title};
  }
  if (/^\/status(?:@\w+)?$/i.test(text) || /^(?:자비스\s*)?(?:상태\s*)?점검$/.test(text)) return {kind: 'status'};
  if (/^\/standards(?:@\w+)?$/i.test(text) || /^기준\s*목록$/.test(text)) return {kind: 'standard_list'};

  const standard = /^기준\s*(저장|보기|삭제)\s*[:：]\s*([\s\S]+)$/.exec(text);
  if (standard) {
    if (standard[1] === '저장') {
      const parsed = parseStandard(standard[2]);
      return parsed ? {kind: 'standard_save', ...parsed} : {kind: 'standard_invalid'};
    }
    const name = standard[2].replace(/^#/, '').trim();
    if (!STANDARD_NAME.test(name)) return {kind: 'standard_invalid'};
    return {kind: standard[1] === '보기' ? 'standard_show' : 'standard_delete', name};
  }

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
  if (action.kind === 'save_output') {
    // 제목·답변 원문은 공개 페이로드에 싣지 않는다. Actions가 JarvisMemory의 저장 스냅숏을 한 번만 꺼낸다.
    return ['jarvis_save_output', {telegram_update_id: action.update_id}];
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

const PROVIDER_NAMES = {claude: 'Claude', codex: 'ChatGPT·Codex', gemini: 'Gemini'};

export function ago(ms, now = Date.now()) {
  const seconds = Math.max(0, Math.round((now - ms) / 1000));
  if (seconds < 60) return `${seconds}초 전`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}분 전`;
  if (seconds < 86400) return `${Math.round(seconds / 3600)}시간 전`;
  return `${Math.round(seconds / 86400)}일 전`;
}

// 점검 결과 메시지. 원문(질문·기억 내용)은 넣지 않고 개수와 시각만 보여준다.
export function formatStatus(state, {ready, agentEnabled, actions}, now = Date.now()) {
  const lines = [`Jarvis 점검 (${new Date(now + 9 * 3600 * 1000).toISOString().slice(0, 16).replace('T', ' ')} KST)`, ''];
  const lastSeen = Number(state.lastSeen) || 0;
  if (!agentEnabled) {
    lines.push('[PC 에이전트] 미설정 (JARVIS_AGENT_TOKEN 없음) → 모든 질문을 GitHub Actions로 처리');
  } else if (!lastSeen) {
    lines.push('[PC 에이전트] 연결 기록 없음 → 질문은 GitHub Actions(OpenAI API)로 처리');
  } else if (now - lastSeen <= AGENT_FRESH_MS) {
    lines.push(`[PC 에이전트] 정상 · ${ago(lastSeen, now)} 확인${state.agentName ? ` · ${state.agentName}` : ''}`);
  } else {
    lines.push(`[PC 에이전트] 꺼짐 · 마지막 확인 ${ago(lastSeen, now)} → 질문은 GitHub Actions(OpenAI API)로 처리`);
  }
  if (agentEnabled && lastSeen) {
    const caps = Array.isArray(state.capabilities) ? state.capabilities : [];
    lines.push(`- 사용 가능 모델: ${Object.entries(PROVIDER_NAMES).map(([id, name]) => `${name} ${caps.includes(id) ? 'O' : 'X'}`).join(' · ')}`);
    lines.push(`- 마지막 답변 완료: ${state.lastDone ? ago(state.lastDone, now) : '기록 없음'}`);
  }
  lines.push(`[대기열] 처리 대기 ${state.pending || 0}건${state.stuck ? ` · 지연 ${state.stuck}건(제한 시간 초과, Actions 전환 대기)` : ''}`);
  lines.push(`[기억] 대화 ${state.conversations || 0}회 · 기억 항목 ${state.items || 0}개 · 작업 기준 ${state.standards || 0}개`);
  lines.push(`[연결 PC] 기본 PC${state.devices ? ` + 페어링 ${state.devices}대` : ''}`);
  lines.push(`[GitHub Actions] ${actions}`);
  lines.push(`[Worker 설정] ${ready ? '필수 설정 정상' : '필수 설정 누락'}`);
  return lines.join('\n');
}

async function lastActionsRun(env, now = Date.now()) {
  try {
    const response = await fetch(`https://api.github.com/repos/${env.GITHUB_REPOSITORY}/actions/workflows/jarvis.yml/runs?per_page=1`, {
      headers: {
        'Authorization': `Bearer ${env.JARVIS_DISPATCH_TOKEN}`,
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'qaplus-jarvis-webhook',
      },
      signal: AbortSignal.timeout(5000),
    });
    if (response.status === 401 || response.status === 403 || response.status === 404) return '조회 불가 (dispatch 토큰에 Actions 읽기 권한 필요)';
    if (!response.ok) return `조회 실패 (${response.status})`;
    const run = (await response.json())?.workflow_runs?.[0];
    if (!run) return '실행 기록 없음';
    const result = run.status !== 'completed' ? '실행 중' : run.conclusion === 'success' ? '성공' : `실패(${run.conclusion})`;
    const at = Date.parse(run.updated_at || run.created_at);
    return `최근 실행 ${result} · ${run.event === 'repository_dispatch' ? run.display_title || 'dispatch' : run.event} · ${Number.isFinite(at) ? ago(at, now) : ''}`.trim();
  } catch {
    return '조회 실패 (시간 초과)';
  }
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

export async function sha256Hex(text) {
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', encoder.encode(text)));
  return Array.from(digest, byte => byte.toString(16).padStart(2, '0')).join('');
}

// 반환: {role:'agent'}(기본 PC 토큰) | {role:'actions'} | {role:'device', hash}(페어링 기기 후보, 저장소에서 검증) | null
async function callerOf(request, env) {
  const provided = (request.headers.get('Authorization') || '').replace(/^Bearer\s+/i, '');
  if (!provided) return null;
  if (env.JARVIS_AGENT_TOKEN && env.JARVIS_AGENT_TOKEN.length >= 32 && safeEqual(provided, env.JARVIS_AGENT_TOKEN)) return {role: 'agent'};
  if (safeEqual(provided, await memoryToken(env.JARVIS_WEBHOOK_SECRET))) return {role: 'actions'};
  if (provided.length >= 32 && provided.length <= 128) return {role: 'device', hash: await sha256Hex(provided)};
  return null;
}

const PAIR_NAME = /^[\w가-힣 .()-]{1,40}$/;

async function handlePairing(request, env, path) {
  if (request.method !== 'POST') return new Response('Method not allowed', {status: 405});
  let parsed = {};
  try { parsed = await request.json(); } catch { return new Response('Invalid JSON', {status: 400}); }
  const hash = typeof parsed.token_hash === 'string' ? parsed.token_hash : '';
  if (!/^[0-9a-f]{64}$/.test(hash)) return new Response('Invalid hash', {status: 400});
  if (path === '/agent/pair/status') {
    const {data} = await memoryCall(env, 'pair-status', {hash});
    return Response.json({approved: Boolean(data.approved)});
  }
  const name = typeof parsed.name === 'string' ? parsed.name.trim() : '';
  if (!PAIR_NAME.test(name)) return new Response('Invalid name', {status: 400});
  const {status, data} = await memoryCall(env, 'pair-request', {hash, name});
  if (status !== 200) return Response.json(data, {status});
  await telegram(env, 'sendMessage', {
    chat_id: env.JARVIS_TELEGRAM_CHAT_ID,
    text: [
      `새 PC 연결 요청: "${name}"`,
      `확인 코드: ${data.code}`,
      '',
      '그 PC 화면에 나온 코드와 같고 본인이 요청한 것이 맞을 때만 승인하세요.',
      '승인하면 그 PC가 Jarvis 질문을 받아 답하고 기억을 읽고 쓸 수 있습니다. (10분 후 만료)',
    ].join('\n'),
    reply_markup: {inline_keyboard: [[
      {text: '승인', callback_data: `pair:${data.id}`},
      {text: '거절', callback_data: `pairno:${data.id}`},
    ]]},
  });
  return Response.json({code: data.code});
}

async function sendChunks(env, text) {
  const body = String(text || '').slice(0, 12000);
  for (let index = 0; index < Math.max(body.length, 1); index += 3900) {
    await telegram(env, 'sendMessage', {chat_id: env.JARVIS_TELEGRAM_CHAT_ID, text: body.slice(index, index + 3900) || '(빈 응답)'});
  }
}

async function handleAgentApi(request, env, path) {
  if (path === '/agent/pair' || path === '/agent/pair/status') return handlePairing(request, env, path);
  const caller = await callerOf(request, env);
  if (!caller || caller.role === 'actions') return new Response('Forbidden', {status: 403});
  // 기본 토큰은 Worker가 검증했다. 페어링 기기는 저장소가 같은 호출 안에서 해시를 검증한다.
  const device = caller.role === 'device' ? caller.hash : null;
  if (request.method !== 'POST') return new Response('Method not allowed', {status: 405});
  let parsed = {};
  try { parsed = await request.json(); } catch { return new Response('Invalid JSON', {status: 400}); }
  if (path === '/agent/poll') {
    const {status, data} = await memoryCall(env, 'agent-poll', {capabilities: parsed.capabilities, device});
    return Response.json(data, {status});
  }
  if (path === '/agent/reply') {
    const text = typeof parsed.text === 'string' ? parsed.text.trim() : '';
    if (!Number.isSafeInteger(parsed.update_id) || (!text && !parsed.done)) {
      return new Response('Invalid reply', {status: 400});
    }
    const {status} = await memoryCall(env, 'agent-check', {update_id: parsed.update_id, device});
    if (status === 403) return new Response('Forbidden', {status: 403});
    if (status !== 200) return Response.json({error: 'not_claimed'}, {status: 409});
    if (text) await sendChunks(env, text);  // text 없이 done만 오면 완료 처리만 한다
    if (parsed.done) await memoryCall(env, 'agent-done', {update_id: parsed.update_id, device});
    return Response.json({ok: true});
  }
  return new Response('Not found', {status: 404});
}

async function handleMemoryApi(request, env, path) {
  const caller = await callerOf(request, env);
  if (!caller) return new Response('Forbidden', {status: 403});
  // 페어링 기기는 기억 API에도 접근하므로, 기본 PC 토큰과 달리 저장소의 승인 기록을 확인한다.
  if (caller.role === 'device') {
    const {status} = await memoryCall(env, 'device-check', {hash: caller.hash});
    if (status !== 200) return new Response('Forbidden', {status: 403});
  }

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
  if (path === '/memory/last' && request.method === 'PUT') {
    let parsed;
    try { parsed = await request.json(); } catch { return new Response('Invalid JSON', {status: 400}); }
    if (typeof parsed?.a !== 'string' || !parsed.a.trim()) return new Response('Invalid answer', {status: 400});
    const {status, data} = await memoryCall(env, 'last-put', {q: String(parsed.q || ''), a: parsed.a, source: String(parsed.source || '')});
    return Response.json(data, {status});
  }
  if (path === '/memory/save/take' && request.method === 'POST') {
    let parsed;
    try { parsed = await request.json(); } catch { return new Response('Invalid JSON', {status: 400}); }
    if (!Number.isSafeInteger(parsed?.update_id)) return new Response('Invalid update', {status: 400});
    const {status, data} = await memoryCall(env, 'save-take', {update_id: parsed.update_id});
    return Response.json(data, {status});
  }
  if (path === '/memory/standards' && request.method === 'GET') {
    const {data} = await memoryCall(env, 'standards-list');
    return Response.json({standards: data.standards || []});
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
    if (path.startsWith('/agent/')) {
      if (!ready) return new Response('Not ready', {status: 503});
      return handleAgentApi(request, env, path);
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
          if (action.kind === 'save_output') {
            // 재시도해도 같은 스냅숏을 쓴다(save-put은 멱등). 저장할 답변이 없으면 접수 안내 없이 끝낸다.
            const stored = await memoryCall(this.env, 'save-put', {update_id: action.update_id, title: action.title});
            if (stored.status === 404) {
              await say('저장할 직전 답변이 없습니다. 질문에 답을 받은 뒤 "저장해줘"를 보내주세요.');
              await this.ctx.storage.put('done', true);
              await this.ctx.storage.setAlarm(Date.now() + 7 * 86400 * 1000);
              return Response.json({ok: true, nothing: true});
            }
            if (stored.status !== 200) throw new Error('save_store_failed');
          }
          if (!await this.ctx.storage.get('acknowledged')) {
            try {
              if (action.callback_id) await answer('승인을 확인했습니다. Gmail 초안 생성 요청을 접수합니다.');
              else if (action.kind === 'voice') await say('음성 명령을 접수했습니다. 인식 후 결과를 보내드리겠습니다.');
              else if (action.kind === 'general_query') await say('질문을 받았습니다. 답변을 준비하고 있습니다.');
              else if (action.kind === 'save_output') await say('직전 답변을 Google Drive에 저장합니다.');
              else await say('요청을 접수했습니다. 준비되는 대로 결과를 보내드리겠습니다.');
              await this.ctx.storage.put('acknowledged', true);
            } catch {
              console.warn(JSON.stringify({event: 'jarvis_ack_failed', kind: action.kind, update_id: action.update_id}));
            }
          }
          if (!await this.ctx.storage.get('dispatched')) {
            let mode = 'actions';
            if (action.kind === 'general_query') {
              const stored = await memoryCall(this.env, 'pending-put', {
                update_id: action.update_id, text: action.text, agent_enabled: Boolean(this.env.JARVIS_AGENT_TOKEN),
              });
              if (stored.status !== 200) throw new Error('pending_store_failed');
              mode = stored.data.mode;
            }
            // PC 에이전트가 켜져 있으면 구독 모델이 처리하므로 GitHub Actions를 부르지 않는다.
            if (mode !== 'agent') await dispatch(this.env, requestToDispatch[0], requestToDispatch[1]);
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
        } else if (action.kind === 'status') {
          const [{data}, actions] = await Promise.all([memoryCall(this.env, 'status'), lastActionsRun(this.env)]);
          await say(formatStatus(data, {ready: true, agentEnabled: Boolean(this.env.JARVIS_AGENT_TOKEN), actions}));
        } else if (action.kind === 'standard_save') {
          const {status, data} = await memoryCall(this.env, 'standard-put', {name: action.name, body: action.body});
          if (status === 409) {
            await say(`작업 기준은 최대 ${MAX_STANDARDS}개까지 저장합니다. "기준 삭제: 이름"으로 정리한 뒤 다시 저장해주세요.`);
          } else if (status !== 200) {
            throw new Error('standard_put_failed');
          } else {
            await say([
              `작업 기준 "${action.name}"을 ${data.replaced ? '덮어썼습니다' : '저장했습니다'} (${action.body.length}자).`,
              `질문에 "${action.name}" 또는 #${action.name.replace(/\s+/g, '')} 를 넣으면 이 기준을 적용해 답합니다.`,
            ].join('\n'));
          }
        } else if (action.kind === 'standard_list') {
          const {data} = await memoryCall(this.env, 'standards-list');
          const list = Array.isArray(data.standards) ? data.standards : [];
          await say(list.length
            ? [`저장된 작업 기준 ${list.length}개`, ...list.map(s => `- ${s.name} (${s.body.length}자, ${String(s.updated).slice(0, 10)})`), '', '"기준 보기: 이름"으로 본문 확인'].join('\n')
            : '저장된 작업 기준이 없습니다.\n예)\n기준 저장: 협찬 거절\n감사 인사 → 어려운 이유 → 다음 기회, 세 문장으로 답한다.');
        } else if (action.kind === 'standard_show') {
          const {status, data} = await memoryCall(this.env, 'standard-get', {name: action.name});
          await say(status === 200 ? `[작업 기준] ${data.standard.name}\n\n${data.standard.body}` : `"${action.name}" 기준이 없습니다. /standards 로 목록을 확인하세요.`);
        } else if (action.kind === 'standard_delete') {
          const {status, data} = await memoryCall(this.env, 'standard-delete', {name: action.name});
          await say(status === 200 ? `작업 기준 "${data.name}"을 삭제했습니다.` : `"${action.name}" 기준이 없습니다. /standards 로 목록을 확인하세요.`);
        } else if (action.kind === 'save_invalid') {
          await say(`저장 제목은 ${MAX_SAVE_TITLE}자 이내 한 줄로 적어주세요. 예) 저장해줘: 협찬 거절 답장`);
        } else if (action.kind === 'standard_invalid') {
          await say([
            `기준 형식을 이해하지 못했습니다. 이름은 30자 이내, 본문은 ${MAX_STANDARD_BODY}자 이내입니다.`,
            '예)',
            '기준 저장: 협찬 거절',
            '감사 인사 → 이번에는 어려운 이유 → 다음 기회 제안. 세 문장, 담백하게.',
          ].join('\n'));
        } else if (action.kind === 'query_too_long') {
          await say(`질문은 ${MAX_QUERY_CHARS}자 이내로 보내주세요.`);
        } else if (action.kind === 'voice_too_large') {
          await say('음성 메시지는 5분, 20MB 이하만 처리합니다. 짧게 다시 보내주세요.');
        } else if (action.kind === 'pair_callback') {
          const {status, data} = await memoryCall(this.env, action.approve ? 'pair-approve' : 'pair-reject', {id: action.pair_id});
          if (status !== 200) {
            try { await answer('만료되었거나 이미 처리된 요청입니다.'); } catch {}
          } else {
            try { await answer(action.approve ? '승인했습니다.' : '거절했습니다.'); } catch {}
            await say(action.approve
              ? `PC "${data.name}" 연결을 승인했습니다. /devices 로 연결된 기기를 확인·해제할 수 있습니다.`
              : `PC "${data.name}" 연결 요청을 거절했습니다.`);
          }
        } else if (action.kind === 'devices_show') {
          const {data} = await memoryCall(this.env, 'devices-list');
          const devices = Array.isArray(data.devices) ? data.devices : [];
          const lines = ['연결된 PC', '- 기본 PC(최초 설치, Worker 비밀값 토큰)', ...devices.map(d => `- ${d.name} (승인 ${String(d.addedAt).slice(0, 10)})`)];
          const keyboard = devices.map(d => [{text: `${d.name} 연결 해제`, callback_data: `unpair:${d.prefix}`}]);
          await telegram(this.env, 'sendMessage', {
            chat_id: this.env.JARVIS_TELEGRAM_CHAT_ID, text: lines.join('\n'),
            ...(keyboard.length ? {reply_markup: {inline_keyboard: keyboard}} : {}),
          });
        } else if (action.kind === 'unpair_callback') {
          const {status, data} = await memoryCall(this.env, 'device-remove', {prefix: action.device});
          try { await answer(status === 200 ? '해제했습니다.' : '이미 해제된 기기입니다.'); } catch {}
          if (status === 200) await say(`PC "${data.name}" 연결을 해제했습니다. 그 PC는 더 이상 질문을 받거나 기억에 접근할 수 없습니다.`);
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
      if (op === 'status') {
        const now = Date.now();
        const doc = (await storage.get('doc')) || emptyMemory();
        const profile = doc.profile && typeof doc.profile === 'object' ? doc.profile : {};
        const items = Object.values(profile).reduce((sum, list) => sum + (Array.isArray(list) ? list.length : 0), 0);
        const pending = [...await storage.list({prefix: 'pending:'})].map(([, value]) => value);
        const stuck = pending.filter(v => v?.mode === 'agent' && now - (v.claimedAt ? v.claimedAt + AGENT_WORK_TIMEOUT_MS : v.at + AGENT_CLAIM_TIMEOUT_MS) > 0).length;
        const agent = (await storage.get('agent:info')) || {};
        return Response.json({
          lastSeen: Number(await storage.get('agent:lastSeen')) || 0,
          capabilities: agent.capabilities || [],
          agentName: agent.name || '',
          lastDone: Number(await storage.get('agent:lastDone')) || 0,
          pending: pending.length,
          stuck,
          conversations: Number(doc.stats?.conversations) || 0,
          items,
          standards: ((await storage.get('standards')) || []).length,
          devices: Object.keys((await storage.get('devices')) || {}).length,
        });
      }
      if (op === 'last-put') {
        await storage.put('last', {
          q: String(body.q || '').slice(0, MAX_QUERY_CHARS),
          a: String(body.a || '').slice(0, MAX_LAST_CHARS),
          source: String(body.source || '').slice(0, 80),
          at: new Date().toISOString(),
        });
        return Response.json({ok: true});
      }
      if (op === 'save-put') {
        // 요청 시점의 직전 답변을 고정한다. 그 사이 새 질문이 와도 요청한 답변이 저장된다.
        const now = Date.now();
        for (const [key, value] of await storage.list({prefix: 'save:'})) if (now - (Number(value?.requestedAt) || 0) > SAVE_TTL_MS) await storage.delete(key);
        if (!Number.isSafeInteger(body.update_id)) return Response.json({error: 'invalid'}, {status: 400});
        const key = `save:${body.update_id}`;
        if (await storage.get(key)) return Response.json({ok: true});
        const last = await storage.get('last');
        if (!last?.a) return Response.json({error: 'nothing'}, {status: 404});
        await storage.put(key, {...last, title: String(body.title || '').slice(0, MAX_SAVE_TITLE), requestedAt: now});
        return Response.json({ok: true});
      }
      if (op === 'save-take') {
        const key = `save:${body.update_id}`;
        const value = await storage.get(key);
        if (!value) return Response.json({error: 'not_found'}, {status: 404});
        await storage.delete(key);
        return Response.json({save: value});
      }
      if (op === 'standards-list') {
        return Response.json({standards: (await storage.get('standards')) || []});
      }
      if (op === 'standard-put' || op === 'standard-get' || op === 'standard-delete') {
        const name = typeof body.name === 'string' ? body.name.trim() : '';
        if (!STANDARD_NAME.test(name)) return Response.json({error: 'invalid'}, {status: 400});
        const standards = (await storage.get('standards')) || [];
        const index = standards.findIndex(s => normalizeKey(s.name) === normalizeKey(name));
        if (op === 'standard-get') {
          return index >= 0 ? Response.json({standard: standards[index]}) : Response.json({error: 'not_found'}, {status: 404});
        }
        if (op === 'standard-delete') {
          if (index < 0) return Response.json({error: 'not_found'}, {status: 404});
          const [removed] = standards.splice(index, 1);
          await storage.put('standards', standards);
          return Response.json({name: removed.name});
        }
        const text = typeof body.body === 'string' ? body.body.trim() : '';
        if (text.length < 2 || text.length > MAX_STANDARD_BODY) return Response.json({error: 'invalid'}, {status: 400});
        if (index < 0 && standards.length >= MAX_STANDARDS) return Response.json({error: 'too_many'}, {status: 409});
        const entry = {name, body: text, updated: new Date().toISOString()};
        if (index >= 0) standards[index] = entry; else standards.push(entry);
        await storage.put('standards', standards);
        return Response.json({ok: true, replaced: index >= 0});
      }
      if (op === 'pending-put') {
        if (!Number.isSafeInteger(body.update_id) || typeof body.text !== 'string') return Response.json({error: 'invalid'}, {status: 400});
        const now = Date.now();
        const old = await storage.list({prefix: 'pending:'});
        for (const [key, value] of old) if (now - (Number(value?.at) || 0) > PENDING_TTL_MS) await storage.delete(key);
        const key = `pending:${body.update_id}`;
        const existing = await storage.get(key);
        if (existing) return Response.json({ok: true, mode: existing.mode || 'actions'});  // 재시도 시 같은 결정 유지
        const lastSeen = Number(await storage.get('agent:lastSeen')) || 0;
        const mode = body.agent_enabled && now - lastSeen <= AGENT_FRESH_MS ? 'agent' : 'actions';
        await storage.put(key, {text: body.text.slice(0, MAX_QUERY_CHARS), at: now, mode});
        if (mode === 'agent') await this.scheduleAlarm(now + AGENT_CLAIM_TIMEOUT_MS);
        return Response.json({ok: true, mode});
      }
      if (op === 'pending-take') {
        const key = `pending:${body.update_id}`;
        const value = await storage.get(key);
        if (!value || value.mode === 'agent') return Response.json({error: 'not_found'}, {status: 404});
        await storage.delete(key);
        return Response.json({text: value.text});
      }
      if (op.startsWith('agent-') && body.device) {
        const devices = (await storage.get('devices')) || {};
        if (!devices[body.device]) return Response.json({error: 'forbidden'}, {status: 403});
      }
      if (op === 'device-check') {
        const devices = (await storage.get('devices')) || {};
        return devices[body.hash] ? Response.json({ok: true}) : Response.json({error: 'forbidden'}, {status: 403});
      }
      if (op === 'pair-request') {
        const now = Date.now();
        const pairs = [...await storage.list({prefix: 'pair:'})];
        for (const [key, value] of pairs) if (now - value.at > PAIR_TTL_MS) await storage.delete(key);
        const live = pairs.filter(([, value]) => now - value.at <= PAIR_TTL_MS);
        const devices = (await storage.get('devices')) || {};
        if (devices[body.hash]) return Response.json({error: 'already_paired'}, {status: 409});
        if (Object.keys(devices).length >= MAX_DEVICES) return Response.json({error: 'too_many_devices'}, {status: 409});
        if (live.length >= MAX_PENDING_PAIRS) return Response.json({error: 'too_many_requests'}, {status: 429});
        const random = crypto.getRandomValues(new Uint32Array(2));
        const id = random[0].toString(16).padStart(8, '0');
        const code = String(random[1] % 1000000).padStart(6, '0');
        await storage.put(`pair:${id}`, {hash: body.hash, name: body.name, code, at: now});
        return Response.json({id, code});
      }
      if (op === 'pair-approve' || op === 'pair-reject') {
        const key = `pair:${body.id}`;
        const value = await storage.get(key);
        if (!value || Date.now() - value.at > PAIR_TTL_MS) { await storage.delete(key); return Response.json({error: 'expired'}, {status: 404}); }
        await storage.delete(key);
        if (op === 'pair-approve') {
          const devices = (await storage.get('devices')) || {};
          devices[value.hash] = {name: value.name, addedAt: new Date().toISOString()};
          await storage.put('devices', devices);
        }
        return Response.json({name: value.name});
      }
      if (op === 'pair-status') {
        const devices = (await storage.get('devices')) || {};
        return Response.json({approved: Boolean(devices[body.hash])});
      }
      if (op === 'devices-list') {
        const devices = (await storage.get('devices')) || {};
        return Response.json({devices: Object.entries(devices).map(([hash, d]) => ({name: d.name, addedAt: d.addedAt, prefix: hash.slice(0, 12)}))});
      }
      if (op === 'device-remove') {
        const devices = (await storage.get('devices')) || {};
        const hash = Object.keys(devices).find(key => key.startsWith(String(body.prefix)));
        if (!hash) return Response.json({error: 'not_found'}, {status: 404});
        const {name} = devices[hash];
        delete devices[hash];
        await storage.put('devices', devices);
        return Response.json({name});
      }
      if (op === 'agent-poll') {
        const now = Date.now();
        await storage.put('agent:lastSeen', now);
        // 점검용: 사용 가능한 구독 모델과 기기 이름. 바뀔 때만 저장한다.
        const capabilities = (Array.isArray(body.capabilities) ? body.capabilities : []).filter(id => Object.hasOwn(PROVIDER_NAMES, id));
        const devices = body.device ? (await storage.get('devices')) || {} : {};
        const info = {capabilities, name: body.device ? devices[body.device]?.name || '' : '기본 PC'};
        const previous = (await storage.get('agent:info')) || {};
        if (JSON.stringify(previous) !== JSON.stringify(info)) await storage.put('agent:info', info);
        const items = [...await storage.list({prefix: 'pending:'})]
          .filter(([, value]) => value?.mode === 'agent' && !value.claimedAt)
          .sort((a, b) => a[1].at - b[1].at);
        if (!items.length) return Response.json({job: null});
        const [key, value] = items[0];
        await storage.put(key, {...value, claimedAt: now});
        await this.scheduleAlarm(now + AGENT_WORK_TIMEOUT_MS);
        return Response.json({job: {update_id: Number(key.slice('pending:'.length)), text: value.text}});
      }
      if (op === 'agent-check') {
        const value = await storage.get(`pending:${body.update_id}`);
        return value?.mode === 'agent' && value.claimedAt ? Response.json({ok: true}) : Response.json({error: 'not_claimed'}, {status: 409});
      }
      if (op === 'agent-done') {
        await storage.delete(`pending:${body.update_id}`);
        await storage.put('agent:lastDone', Date.now());
        return Response.json({ok: true});
      }
      return Response.json({error: 'unknown_op'}, {status: 404});
    });
  }

  async scheduleAlarm(at) {
    const current = await this.ctx.storage.getAlarm?.();
    if (!current || current > at) await this.ctx.storage.setAlarm(at);
  }

  // 에이전트가 가져가지 않았거나 처리 중 멈춘 질문을 GitHub Actions(API)로 넘긴다.
  async alarm() {
    await this.ctx.blockConcurrencyWhile(async () => {
      const now = Date.now();
      let next = 0;
      for (const [key, value] of await this.ctx.storage.list({prefix: 'pending:'})) {
        if (value?.mode !== 'agent') continue;
        const deadline = value.claimedAt ? value.claimedAt + AGENT_WORK_TIMEOUT_MS : value.at + AGENT_CLAIM_TIMEOUT_MS;
        if (deadline > now) { next = next ? Math.min(next, deadline) : deadline; continue; }
        try {
          await dispatch(this.env, 'jarvis_general_query', {telegram_update_id: Number(key.slice('pending:'.length))});
          await this.ctx.storage.put(key, {text: value.text, at: value.at, mode: 'actions'});
          console.log(JSON.stringify({event: 'jarvis_agent_fallback', update_id: Number(key.slice('pending:'.length))}));
        } catch {
          next = next ? Math.min(next, now + 30000) : now + 30000;
        }
      }
      if (next) await this.ctx.storage.setAlarm(next);
    });
  }
}
