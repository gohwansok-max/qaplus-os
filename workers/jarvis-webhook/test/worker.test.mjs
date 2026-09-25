import test from 'node:test';
import assert from 'node:assert/strict';
import worker, {classify, JarvisUpdate, verifyDraftCallback} from '../src/index.mjs';

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
  const env = {...baseEnv, JARVIS_UPDATES: {}};
  const response = await worker.fetch(new Request('https://test/telegram', {method: 'POST', body: '{}'}), env);
  assert.equal(response.status, 403);
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
