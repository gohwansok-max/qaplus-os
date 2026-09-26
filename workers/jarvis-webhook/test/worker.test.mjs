import test from 'node:test';
import assert from 'node:assert/strict';
import worker, {classify, JarvisMemory, JarvisUpdate, memoryToken, sha256Hex, verifyDraftCallback} from '../src/index.mjs';

const baseEnv = {
  JARVIS_TELEGRAM_CHAT_ID: '42',
  JARVIS_TELEGRAM_BOT_TOKEN: 'test-token',
  JARVIS_DISPATCH_TOKEN: 'test-dispatch',
  JARVIS_WEBHOOK_SECRET: 'test_secret',
  GITHUB_REPOSITORY: 'owner/repo',
};
const textUpdate = text => ({update_id: 1, message: {chat: {id: 42}, text}});

function base64Url(bytes) {
  return Buffer.from(bytes).toString('base64url');
}

async function signedCallback(messageId = '18abc123def45678', now = Date.now()) {
  const expires = Math.floor((now + 60 * 60 * 1000) / 60000).toString(36);
  const payload = `d:${messageId}:${expires}`;
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(baseEnv.JARVIS_WEBHOOK_SECRET), {name: 'HMAC', hash: 'SHA-256'}, false, ['sign']);
  const digest = new Uint8Array(await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(payload))).slice(0, 12);
  return `${payload}:${base64Url(digest)}`;
}

test('개인 명령, 음성, 허용 chat_id만 분류한다', () => {
  assert.deepEqual(classify(textUpdate('최근 중요 메일 브리핑해줘'), '42'), {kind: 'command', command: 'briefing'});
  assert.deepEqual(classify(textUpdate('오늘 할 일 보여줘'), '42'), {kind: 'command', command: 'today_tasks'});
  assert.equal(classify(textUpdate('/help'), '42').kind, 'help');
  assert.equal(classify(textUpdate('최근 중요 메일 브리핑해줘'), '99').kind, 'forbidden');
  assert.deepEqual(classify({update_id: 2, message: {chat: {id: 42}, voice: {file_id: 'voice-1', duration: 9, file_size: 2000}}}, '42'), {kind: 'voice', file_id: 'voice-1', duration: 9});
  assert.equal(classify({update_id: 3, message: {chat: {id: 42}, voice: {file_id: 'voice-2', duration: 301}}}, '42').kind, 'voice_too_large');
});

test('서명되고 만료되지 않은 답장 초안 callback만 승인한다', async () => {
  const now = Date.now();
  const data = await signedCallback('18abc123def45678', now);
  const action = classify({update_id: 4, callback_query: {id: 'cb-1', data, message: {chat: {id: 42}}}}, '42');
  assert.equal(action.kind, 'draft_callback');
  assert.equal(await verifyDraftCallback(action, baseEnv.JARVIS_WEBHOOK_SECRET, now), true);
  assert.equal(await verifyDraftCallback({...action, signature: 'AAAAAAAAAAAAAAAA'}, baseEnv.JARVIS_WEBHOOK_SECRET, now), false);
  assert.equal(await verifyDraftCallback(action, baseEnv.JARVIS_WEBHOOK_SECRET, now + 2 * 60 * 60 * 1000), false);

  const pythonCallback = 'd:18abc123def45678:gvcd1:TA-pQcn1TW-8YnQI';
  const pythonAction = classify({update_id: 5, callback_query: {id: 'cb-2', data: pythonCallback, message: {chat: {id: 42}}}}, '42');
  assert.equal(await verifyDraftCallback(pythonAction, baseEnv.JARVIS_WEBHOOK_SECRET, 1_700_000_000_000), true);
});

test('같은 승인 버튼을 새 callback ID로 다시 눌러도 dispatch는 한 번만 실행한다', async () => {
  const originalFetch = globalThis.fetch;
  let dispatches = 0;
  let dispatchBody;
  globalThis.fetch = async (url, options = {}) => {
    if (String(url).includes('api.github.com')) {
      dispatches += 1;
      dispatchBody = JSON.parse(options.body);
      return new Response(null, {status: 204});
    }
    return Response.json({ok: true});
  };
  try {
    const objects = new Map();
    const env = {
      ...baseEnv,
      JARVIS_MEMORY: memoryNamespace(),
      JARVIS_UPDATES: {
        getByName: key => {
          if (!objects.has(key)) {
            const object = durableObject(baseEnv);
            objects.set(key, {fetch: (url, options) => object.fetch(new Request(url, options))});
          }
          return objects.get(key);
        },
      },
    };
    const data = await signedCallback();
    const request = callbackId => new Request('https://test/telegram', {
      method: 'POST',
      headers: {'X-Telegram-Bot-Api-Secret-Token': baseEnv.JARVIS_WEBHOOK_SECRET},
      body: JSON.stringify({update_id: callbackId === 'cb-a' ? 10 : 11, callback_query: {id: callbackId, data, message: {chat: {id: 42}}}}),
    });
    assert.equal((await worker.fetch(request('cb-a'), env)).status, 200);
    assert.equal((await worker.fetch(request('cb-b'), env)).status, 200);
    assert.equal(dispatches, 1);
    assert.equal(dispatchBody.event_type, 'jarvis_create_draft');
    assert.equal(dispatchBody.client_payload.approval, data);
    assert.match(dispatchBody.client_payload.approval_id, /^[0-9a-f]{24}$/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('Webhook secret 검증을 우회할 수 없다', async () => {
  const env = {...baseEnv, JARVIS_UPDATES: {}, JARVIS_MEMORY: {}};
  const response = await worker.fetch(new Request('https://test/telegram', {method: 'POST', body: '{}'}), env);
  assert.equal(response.status, 403);
});

function fakeStorage() {
  const data = new Map();
  return {
    get: async key => structuredClone(data.get(key)),
    put: async (key, value) => { data.set(key, structuredClone(value)); },
    delete: async key => data.delete(key),
    list: async ({prefix}) => new Map([...data].filter(([key]) => key.startsWith(prefix))),
    setAlarm: async at => { data.set('__alarm', at); },
    getAlarm: async () => data.get('__alarm') ?? null,
    deleteAll: async () => data.clear(),
  };
}

function serialCtx(storage) {
  let chain = Promise.resolve();
  return {
    storage,
    blockConcurrencyWhile: fn => {
      const result = chain.then(fn);
      chain = result.catch(() => {});
      return result;
    },
  };
}

function memoryNamespace(env = baseEnv) {
  const object = new JarvisMemory(serialCtx(fakeStorage()), env);
  return {object, getByName: () => ({fetch: (url, options) => object.fetch(new Request(url, options))})};
}

function fullEnv(extra = {}) {
  const objects = new Map();
  const env = {
    ...baseEnv,
    ...extra,
    JARVIS_UPDATES: {
      getByName: key => {
        if (!objects.has(key)) {
          const object = new JarvisUpdate(serialCtx(fakeStorage()), env);
          objects.set(key, {fetch: (url, options) => object.fetch(new Request(url, options))});
        }
        return objects.get(key);
      },
    },
  };
  env.JARVIS_MEMORY = memoryNamespace(env);
  return env;
}

const AGENT_TOKEN = 'a'.repeat(48);

async function agentApi(env, path, body, token = AGENT_TOKEN) {
  return worker.fetch(new Request(`https://test${path}`, {
    method: 'POST', headers: {Authorization: `Bearer ${token}`}, body: JSON.stringify(body ?? {}),
  }), env);
}

function captureFetch() {
  const calls = {github: [], telegram: [], telegramBodies: []};
  const original = globalThis.fetch;
  globalThis.fetch = async (url, options = {}) => {
    if (String(url).includes('api.github.com')) { calls.github.push(JSON.parse(options.body)); return new Response(null, {status: 204}); }
    if (String(url).includes('api.telegram.org')) { const body = JSON.parse(options.body); calls.telegram.push(body.text); calls.telegramBodies.push(body); }
    return Response.json({ok: true});
  };
  calls.restore = () => { globalThis.fetch = original; };
  return calls;
}

test('PC 에이전트가 켜져 있으면 질문을 구독 모델 에이전트가 처리하고 GitHub Actions는 부르지 않는다', async () => {
  const calls = captureFetch();
  try {
    const env = fullEnv({JARVIS_AGENT_TOKEN: AGENT_TOKEN});
    assert.deepEqual(await (await agentApi(env, '/agent/poll')).json(), {job: null});
    await worker.fetch(telegramRequest(701, 'HACCP 검증 주기 알려줘'), env);
    assert.equal(calls.github.length, 0);

    const job = (await (await agentApi(env, '/agent/poll')).json()).job;
    assert.deepEqual(job, {update_id: 701, text: 'HACCP 검증 주기 알려줘'});
    assert.deepEqual(await (await agentApi(env, '/agent/poll')).json(), {job: null});

    const take = await memoryApi(env, '/memory/pending/take', {method: 'POST', body: JSON.stringify({update_id: 701})});
    assert.equal(take.status, 404);

    assert.equal((await agentApi(env, '/agent/reply', {update_id: 701, text: '연 1회 이상입니다.', done: true})).status, 200);
    assert.equal(calls.telegram.at(-1), '연 1회 이상입니다.');
    assert.equal((await agentApi(env, '/agent/reply', {update_id: 701, text: '중복'})).status, 409);
  } finally {
    calls.restore();
  }
});

test('에이전트가 꺼져 있거나 제한 시간 안에 가져가지 않으면 GitHub Actions(API)로 넘긴다', async () => {
  const calls = captureFetch();
  const realNow = Date.now;
  try {
    const offline = fullEnv({JARVIS_AGENT_TOKEN: AGENT_TOKEN});
    await worker.fetch(telegramRequest(801, '질문 하나'), offline);
    assert.equal(calls.github.length, 1);

    const env = fullEnv({JARVIS_AGENT_TOKEN: AGENT_TOKEN});
    await agentApi(env, '/agent/poll');
    await worker.fetch(telegramRequest(802, '질문 둘'), env);
    assert.equal(calls.github.length, 1);

    const start = realNow();
    Date.now = () => start + 61 * 1000;
    await env.JARVIS_MEMORY.object.alarm();
    assert.equal(calls.github.length, 2);
    assert.deepEqual(calls.github.at(-1).client_payload, {telegram_update_id: 802});
    Date.now = realNow;

    const take = await memoryApi(env, '/memory/pending/take', {method: 'POST', body: JSON.stringify({update_id: 802})});
    assert.equal((await take.json()).text, '질문 둘');
  } finally {
    Date.now = realNow;
    calls.restore();
  }
});

test('페어링 승인 전 PC는 차단되고, Telegram 코드 승인 뒤에만 에이전트·기억 API에 접근한다', async () => {
  const calls = captureFetch();
  try {
    const env = fullEnv({JARVIS_AGENT_TOKEN: AGENT_TOKEN});
    const deviceToken = 'c'.repeat(48);
    const hash = await sha256Hex(deviceToken);
    assert.equal((await agentApi(env, '/agent/poll', {}, deviceToken)).status, 403);

    const pair = await worker.fetch(new Request('https://test/agent/pair', {method: 'POST', body: JSON.stringify({token_hash: hash, name: '회사 PC'})}), env);
    const request = await pair.json();
    assert.match(request.code, /^\d{6}$/);
    assert.match(calls.telegram.at(-1), /회사 PC/);

    const callback = calls.telegramBodies.at(-1).reply_markup.inline_keyboard[0][0].callback_data;
    const approve = new Request('https://test/telegram', {method: 'POST', headers: {'X-Telegram-Bot-Api-Secret-Token': baseEnv.JARVIS_WEBHOOK_SECRET}, body: JSON.stringify({update_id: 88, callback_query: {id: 'pair-cb', data: callback, message: {chat: {id: 42}}}})});
    assert.equal((await worker.fetch(approve, env)).status, 200);
    assert.deepEqual(await (await worker.fetch(new Request('https://test/agent/pair/status', {method: 'POST', body: JSON.stringify({token_hash: hash})}), env)).json(), {approved: true});
    assert.equal((await agentApi(env, '/agent/poll', {}, deviceToken)).status, 200);
    assert.equal((await memoryApi(env, '/memory', {}, deviceToken)).status, 200);

    await worker.fetch(telegramRequest(89, '/devices'), env);
    assert.match(calls.telegram.at(-1), /회사 PC/);
  } finally { calls.restore(); }
});

test('에이전트 API는 에이전트 토큰 또는 승인된 페어링 기기만 허용한다', async () => {
  const env = fullEnv({JARVIS_AGENT_TOKEN: AGENT_TOKEN});
  assert.equal((await agentApi(env, '/agent/poll', {}, 'b'.repeat(48))).status, 403);
  assert.equal((await agentApi(env, '/agent/poll', {}, await memoryToken(baseEnv.JARVIS_WEBHOOK_SECRET))).status, 403);
  assert.equal((await memoryApi(env, '/memory', {}, AGENT_TOKEN)).status, 200);
  const noToken = fullEnv();
  assert.equal((await agentApi(noToken, '/agent/poll')).status, 403);
});

function telegramRequest(updateId, text) {
  return new Request('https://test/telegram', {
    method: 'POST',
    headers: {'X-Telegram-Bot-Api-Secret-Token': baseEnv.JARVIS_WEBHOOK_SECRET},
    body: JSON.stringify({update_id: updateId, message: {chat: {id: 42}, text}}),
  });
}

async function memoryApi(env, path, init = {}, token) {
  const auth = token ?? await memoryToken(baseEnv.JARVIS_WEBHOOK_SECRET);
  return worker.fetch(new Request(`https://test${path}`, {...init, headers: {Authorization: `Bearer ${auth}`, ...(init.headers || {})}}), env);
}

test('띄어쓰기·슬래시 명령과 자유 질문, 기억 명령을 구분한다', () => {
  const kind = text => classify(textUpdate(text), '42');
  assert.deepEqual(kind('/briefing'), {kind: 'command', command: 'briefing'});
  assert.deepEqual(kind('/today_tasks@gohwansok_jarvis_bot'), {kind: 'command', command: 'today_tasks'});
  assert.deepEqual(kind('메일브리핑 해줘'), {kind: 'command', command: 'briefing'});
  assert.deepEqual(kind('오늘할일'), {kind: 'command', command: 'today_tasks'});
  assert.equal(kind('임원 브리핑 자료에 넣을 HACCP 개선 포인트 정리해줘').kind, 'general_query');
  assert.deepEqual(kind('내일 감사 준비 체크리스트 만들어줘'), {kind: 'general_query', text: '내일 감사 준비 체크리스트 만들어줘'});
  assert.deepEqual(kind('기억해: 보고서는 결론부터 써줘'), {kind: 'memory_note', items: [{section: 'facts', text: '보고서는 결론부터 써줘'}]});
  assert.deepEqual(kind('기억 수정: [개인사] 경력은 20년차'), {kind: 'memory_note', items: [{section: 'personal_history', text: '정정: 경력은 20년차'}]});
  assert.deepEqual(kind('기억해:\n[품질] 식품 QA 20년차\n- [AI] 바이브 코딩으로 업무 웹앱 제작\n보고서는 결론부터').items, [
    {section: 'qa_expertise', text: '식품 QA 20년차'},
    {section: 'ai_capability', text: '바이브 코딩으로 업무 웹앱 제작'},
    {section: 'facts', text: '보고서는 결론부터'},
  ]);
  assert.equal(kind('기억해: [없는분류] 내용').kind, 'memory_note_invalid');
  assert.equal(kind('/memory').kind, 'memory_show');
  assert.equal(kind('/forget_all').kind, 'memory_reset');
  assert.equal(kind('가'.repeat(2001)).kind, 'query_too_long');
});

test('Worker와 Python의 메모리 API 토큰이 같다', async () => {
  assert.equal(await memoryToken('test_secret'), '6e7f206b2f78493abc24347c6b65e6df125acfdac1aa756a34c05eea1b8d6afe');
});

test('자유 질문 원문은 공개 dispatch 페이로드에 싣지 않고 인증된 메모리 API로 한 번만 꺼낸다', async () => {
  const originalFetch = globalThis.fetch;
  const bodies = [];
  globalThis.fetch = async (url, options = {}) => {
    if (String(url).includes('api.github.com')) { bodies.push(options.body); return new Response(null, {status: 204}); }
    return Response.json({ok: true});
  };
  try {
    const env = fullEnv();
    const secretQuestion = '우리 회사 클레임 대응 전략 알려줘';
    assert.equal((await worker.fetch(telegramRequest(501, secretQuestion), env)).status, 200);
    assert.equal(bodies.length, 1);
    const payload = JSON.parse(bodies[0]);
    assert.equal(payload.event_type, 'jarvis_general_query');
    assert.deepEqual(payload.client_payload, {telegram_update_id: 501});
    assert.ok(!bodies[0].includes('클레임'));

    const take = token => memoryApi(env, '/memory/pending/take', {method: 'POST', body: JSON.stringify({update_id: 501})}, token);
    assert.equal((await take('wrong-token')).status, 403);
    const first = await take();
    assert.equal(first.status, 200);
    assert.equal((await first.json()).text, secretQuestion);
    assert.equal((await take()).status, 404);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('메모리 저장은 rev가 맞을 때만 성공하고 기억 명령은 표시·초기화된다', async () => {
  const originalFetch = globalThis.fetch;
  const sent = [];
  globalThis.fetch = async (url, options = {}) => {
    if (String(url).includes('api.telegram.org')) sent.push(JSON.parse(options.body).text);
    return Response.json({ok: true});
  };
  try {
    const env = fullEnv();
    assert.equal((await memoryApi(env, '/memory')).status, 200);
    assert.equal((await memoryApi(env, '/memory', {method: 'GET'}, 'bad')).status, 403);

    const put = rev => memoryApi(env, '/memory', {method: 'PUT', body: JSON.stringify({expected_rev: rev, doc: {profile: {tone_manner: [{text: '짧은 지시형 문장', count: 1}]}, turns: [], stats: {}}})});
    const ok = await put(0);
    assert.equal(ok.status, 200);
    assert.equal((await ok.json()).rev, 1);
    assert.equal((await put(0)).status, 409);

    await worker.fetch(telegramRequest(601, '기억해:\n보고서는 결론부터\n[품질] 식품 QA 20년차'), env);
    assert.match(sent.at(-1), /기억했습니다 \(2건\)/);
    await worker.fetch(telegramRequest(602, '/memory'), env);
    assert.match(sent.at(-1), /보고서는 결론부터 \(직접 기억\)/);
    assert.match(sent.at(-1), /\[품질관리 전문성\]\n- 식품 QA 20년차/);
    assert.match(sent.at(-1), /짧은 지시형 문장/);

    await worker.fetch(telegramRequest(603, '/forget_all'), env);
    await worker.fetch(telegramRequest(604, '/memory'), env);
    assert.match(sent.at(-1), /아직 기억한 내용이 없습니다/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

function durableObject(env = baseEnv) {
  const data = new Map();
  let chain = Promise.resolve();
  const ctx = {
    storage: {
      get: async key => data.get(key),
      put: async (key, value) => data.set(key, value),
      setAlarm: async () => {},
      deleteAll: async () => data.clear(),
    },
    blockConcurrencyWhile: fn => {
      const result = chain.then(fn);
      chain = result.catch(() => {});
      return result;
    },
  };
  return new JarvisUpdate(ctx, env);
}

test('동시 중복 명령도 GitHub dispatch는 한 번만 실행한다', async () => {
  const originalFetch = globalThis.fetch;
  let dispatches = 0;
  globalThis.fetch = async url => {
    if (String(url).includes('api.github.com')) {
      dispatches += 1;
      return new Response(null, {status: 204});
    }
    return Response.json({ok: true});
  };
  try {
    const object = durableObject();
    const request = () => new Request('https://internal', {method: 'POST', body: JSON.stringify({kind: 'command', command: 'briefing', update_id: 7})});
    const responses = await Promise.all([object.fetch(request()), object.fetch(request()), object.fetch(request())]);
    assert.equal(dispatches, 1);
    assert.ok((await responses[1].json()).duplicate);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('GitHub 실패는 재시도하고 성공한 dispatch는 ACK 실패에도 반복하지 않는다', async () => {
  const originalFetch = globalThis.fetch;
  let dispatches = 0;
  globalThis.fetch = async url => {
    if (String(url).includes('api.github.com')) {
      dispatches += 1;
      return new Response(null, {status: dispatches === 1 ? 503 : 204});
    }
    throw new Error('telegram unavailable');
  };
  try {
    const object = durableObject();
    const request = () => new Request('https://internal', {method: 'POST', body: JSON.stringify({kind: 'voice', file_id: 'voice-1', duration: 5, update_id: 8})});
    assert.equal((await object.fetch(request())).status, 503);
    assert.equal((await object.fetch(request())).status, 200);
    assert.ok((await (await object.fetch(request())).json()).duplicate);
    assert.equal(dispatches, 2);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('작업 기준 명령을 분류하고 형식이 틀리면 안내한다', () => {
  assert.deepEqual(classify(textUpdate('기준 저장: 협찬 거절\n감사 인사 → 어려운 이유 → 다음 기회'), '42'),
    {kind: 'standard_save', name: '협찬 거절', body: '감사 인사 → 어려운 이유 → 다음 기회'});
  assert.deepEqual(classify(textUpdate('기준 저장: 보고서 / 결론 → 근거 3개'), '42'), {kind: 'standard_save', name: '보고서', body: '결론 → 근거 3개'});
  assert.equal(classify(textUpdate('기준 저장: 이름만'), '42').kind, 'standard_invalid');
  assert.equal(classify(textUpdate(`기준 저장: 긴 본문\n${'가'.repeat(1501)}`), '42').kind, 'standard_invalid');
  assert.equal(classify(textUpdate('/standards'), '42').kind, 'standard_list');
  assert.equal(classify(textUpdate('기준 목록'), '42').kind, 'standard_list');
  assert.deepEqual(classify(textUpdate('기준 보기: #협찬 거절'), '42'), {kind: 'standard_show', name: '협찬 거절'});
  assert.deepEqual(classify(textUpdate('기준 삭제: 보고서'), '42'), {kind: 'standard_delete', name: '보고서'});
  assert.equal(classify(textUpdate('협찬 거절 기준으로 답장 써줘'), '42').kind, 'general_query');
});

test('작업 기준은 저장·덮어쓰기·조회·삭제되고 /forget_all 후에도 유지되며 인증된 API로만 읽힌다', async () => {
  const calls = captureFetch();
  try {
    const env = fullEnv();
    await worker.fetch(telegramRequest(901, '기준 저장: 협찬 거절\n감사 → 이유 → 다음 기회'), env);
    assert.match(calls.telegram.at(-1), /"협찬 거절"을 저장했습니다/);
    await worker.fetch(telegramRequest(902, '기준 저장: 협찬거절\n세 문장, 담백하게'), env);
    assert.match(calls.telegram.at(-1), /덮어썼습니다/);
    await worker.fetch(telegramRequest(903, '/standards'), env);
    assert.match(calls.telegram.at(-1), /저장된 작업 기준 1개/);
    await worker.fetch(telegramRequest(904, '기준 보기: 협찬 거절'), env);
    assert.match(calls.telegram.at(-1), /세 문장, 담백하게/);

    await worker.fetch(telegramRequest(905, '/forget_all'), env);
    const api = await memoryApi(env, '/memory/standards', {method: 'GET'});
    assert.equal(api.status, 200);
    assert.equal((await api.json()).standards[0].body, '세 문장, 담백하게');
    assert.equal((await memoryApi(env, '/memory/standards', {method: 'GET'}, 'bad')).status, 403);

    await worker.fetch(telegramRequest(906, '기준 삭제: 협찬 거절'), env);
    assert.match(calls.telegram.at(-1), /삭제했습니다/);
    await worker.fetch(telegramRequest(907, '기준 보기: 협찬 거절'), env);
    assert.match(calls.telegram.at(-1), /기준이 없습니다/);
    assert.equal(calls.github.length, 0);
  } finally {
    calls.restore();
  }
});

test('작업 기준은 최대 30개까지 저장한다', async () => {
  const {object} = memoryNamespace();
  const op = (name, body) => object.fetch(new Request(`https://internal/${name}`, {method: 'POST', body: JSON.stringify(body)}));
  for (let i = 0; i < 30; i += 1) assert.equal((await op('standard-put', {name: `기준${i}`, body: '본문입니다'})).status, 200);
  assert.equal((await op('standard-put', {name: '기준30', body: '본문입니다'})).status, 409);
  assert.equal((await op('standard-put', {name: '기준0', body: '덮어쓰기는 허용'})).status, 200);
  assert.equal((await op('standard-put', {name: '<script>', body: '본문입니다'})).status, 400);
});
