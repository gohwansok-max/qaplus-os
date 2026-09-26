import test from 'node:test';
import assert from 'node:assert/strict';
import {processJob} from '../agent.mjs';
import {addItems, applyLearning, cleanForTelegram, normalizeMemory, parseLearning, personaPrompt, redactSecrets, route} from '../lib.mjs';
import {makeProviders, subscriptionEnv} from '../providers.mjs';

const ALL = ['claude', 'codex', 'gemini'];

test('질문 성격에 따라 구독 모델을 고르고 직접 지정도 된다', () => {
  assert.deepEqual(route('HACCP 내부심사 체크리스트 만들어줘', ALL).order, ['claude', 'codex', 'gemini']);
  assert.equal(route('파이썬으로 엑셀 합치는 코드 짜줘', ALL).order[0], 'codex');
  assert.equal(route('이번 주 식약처 고시 개정 내용 알려줘', ALL).order[0], 'gemini');
  const explicit = route('@gemini 오늘 날씨', ALL);
  assert.deepEqual([explicit.order[0], explicit.query], ['gemini', '오늘 날씨']);
  assert.equal(route('@gpt 요약해줘', ALL).order[0], 'codex');
  assert.deepEqual(route('@all 이 전략 어때?', ALL), {mode: 'all', query: '이 전략 어때?', order: ALL});
  // Gemini 미로그인 시 최신 정보 질문도 사용 가능한 모델로 간다
  assert.deepEqual(route('최신 뉴스 알려줘', ['claude', 'codex']).order, ['claude', 'codex']);
  assert.equal(route('최신 뉴스 알려줘', ['claude', 'codex']).fresh, true);
  assert.equal(route('HACCP 7원칙 설명해줘', ALL).fresh, false);
});

test('텔레그램에서 깨지는 마크다운을 정리하되 코드 블록은 유지한다', () => {
  assert.equal(cleanForTelegram('## 결론\n**핵심**은 __이것__\n* 항목'), '결론\n핵심은 이것\n- 항목');
  assert.equal(cleanForTelegram('```py\nx = **2\n```'), '```py\nx = **2\n```');
  assert.equal(cleanForTelegram('- [식약처](https://www.mfds.go.kr/a)'), '- 식약처 (https://www.mfds.go.kr/a)');
});

test('비밀값을 가리고 학습 병합은 중복을 합친다', () => {
  assert.ok(!redactSecrets('키는 sk-abcdefghijklmnop12 야').includes('sk-abc'));
  const doc = normalizeMemory(null);
  assert.deepEqual(addItems(doc, 'preferences', ['표로 정리']), ['표로 정리']);
  assert.deepEqual(addItems(doc, 'preferences', ['표로  정리.']), []);
  assert.equal(doc.profile.preferences[0].count, 2);
  assert.deepEqual(addItems(doc, 'nope', ['x']), []);
  assert.deepEqual(parseLearning('설명 {"updates": {"skills": ["감사 준비"]}} 끝').updates.skills, ['감사 준비']);
  assert.deepEqual(parseLearning('JSON 아님'), {updates: {}});
  const added = applyLearning(doc, '질문', '답', {updates: {skills: ['감사 준비'], hacker: ['x']}});
  assert.deepEqual(added, ['감사 준비']);
  assert.equal(doc.stats.conversations, 1);
  assert.match(personaPrompt(doc), /표로 정리/);
  assert.match(personaPrompt(doc, {webSearch: true}), /웹 검색을 사용/);
});

test('구독 CLI 자식 프로세스에서 API 키 환경변수를 제거한다', () => {
  const env = subscriptionEnv({OPENAI_API_KEY: 'x', ANTHROPIC_API_KEY: 'y', ANTHROPIC_MODEL: 'opus', GEMINI_API_KEY: 'z', PATH: 'p'});
  assert.deepEqual(env, {PATH: 'p'});
});

test('CLI 출력 형식을 해석하고 도구 사용을 막는 인자를 넘긴다', async () => {
  const calls = [];
  const runner = async ({command, args, input}) => {
    calls.push({command, args, input});
    if (command === 'claude.exe') return {stdout: JSON.stringify({result: '클로드 답', is_error: false, modelUsage: {'claude-haiku-4-5': {outputTokens: 12}, 'claude-sonnet-5': {outputTokens: 300}}})};
    if (args.includes('exec')) return {stdout: `{"type":"thread.started"}\n{"type":"item.completed","item":{"type":"agent_message","text":"코덱스 답"}}\n`};
    return {stdout: `잡음\n${JSON.stringify({response: '제미나이 답', stats: {models: {'gemini-2.5-pro': {}}}})}`};
  };
  const commands = {
    claude: {command: 'claude.exe', prefix: []},
    codex: {command: 'node', prefix: ['codex.js']},
    gemini: {command: 'node', prefix: ['gemini.js']},
  };
  const providers = makeProviders({commands, runner, workDir: '.'});
  assert.deepEqual(await providers.claude({system: 'S', prompt: 'P'}), {text: '클로드 답', model: 'claude-sonnet-5'});
  assert.deepEqual(await providers.codex({system: 'S', prompt: 'P'}), {text: '코덱스 답', model: 'ChatGPT/Codex'});
  assert.deepEqual(await providers.gemini({system: 'S', prompt: 'P'}), {text: '제미나이 답', model: 'gemini-2.5-pro'});
  const claudeArgs = calls[0].args;
  assert.equal(claudeArgs[claudeArgs.indexOf('--tools') + 1], '');
  assert.equal(claudeArgs[claudeArgs.indexOf('--model') + 1], 'sonnet');
  assert.equal(claudeArgs[claudeArgs.indexOf('--setting-sources') + 1], 'project,local');
  assert.ok(claudeArgs.includes('--strict-mcp-config') && claudeArgs.includes('--disable-slash-commands'));
  assert.ok(!claudeArgs.includes('--bare'));
  assert.ok(!claudeArgs.includes('WebSearch'));

  await providers.claude({system: 'S', prompt: 'P', webSearch: true});
  const webArgs = calls.at(-1).args;
  assert.equal(webArgs[webArgs.indexOf('--tools') + 1], 'WebSearch,WebFetch');
  assert.equal(webArgs[webArgs.indexOf('--max-turns') + 1], '8');
  assert.ok(!webArgs.join(' ').match(/Bash|Write|Edit|Read\b/));
  assert.ok(calls[1].args.includes('read-only'));
  assert.ok(calls[2].args.includes('plan'));
  assert.equal(calls[0].input, 'P');
});

function fakeApi(doc = normalizeMemory(null)) {
  const state = {doc: structuredClone(doc), replies: [], saves: 0};
  return {
    state,
    loadMemory: async () => normalizeMemory(structuredClone(state.doc)),
    saveMemory: async next => { if (next.rev !== state.doc.rev) return false; state.doc = {...structuredClone(next), rev: next.rev + 1}; state.saves += 1; return true; },
    reply: async (id, text, done) => { state.replies.push({id, text, done}); return 200; },
  };
}

test('한 모델이 사용 한도에 걸리면 다음 구독 모델로 넘어가고 학습 결과를 저장한다', async () => {
  const api = fakeApi();
  const seen = [];
  const providers = {
    claude: async ({model, system}) => {
      if (system.startsWith('너는 개인 비서의 학습 모듈')) {
        assert.equal(model, 'haiku');
        return {text: '{"updates":{"preferences":["결론 먼저"]}}', model: 'haiku'};
      }
      seen.push('claude');
      throw new Error('Claude usage limit reached');
    },
    codex: async () => { seen.push('codex'); return {text: '**결론**: 가능', model: 'gpt'}; },
  };
  const result = await processJob({update_id: 5, text: '이 일정 가능해?'}, {api, providers});
  assert.equal(result.ok, true);
  assert.deepEqual(seen, ['claude', 'codex']);
  const answer = api.state.replies[0];
  assert.match(answer.text, /^결론: 가능/);
  assert.match(answer.text, /ChatGPT·Codex\(구독\)/);
  assert.match(answer.text, /사용 한도 도달/);
  assert.equal(answer.done, false);
  assert.match(api.state.replies.at(-1).text, /결론 먼저/);
  assert.equal(api.state.replies.at(-1).done, true);
  assert.equal(api.state.doc.profile.preferences[0].text, '결론 먼저');
  assert.equal(api.state.doc.turns.at(-1).q, '이 일정 가능해?');
});

test('@all은 세 모델 답을 모아 비교하고, 새로 배운 게 없으면 알림 없이 완료만 처리한다', async () => {
  const api = fakeApi();
  const providers = {
    claude: async ({system}) => system.startsWith('너는 개인 비서의 학습') ? {text: '{"updates":{}}', model: 'h'} : {text: 'C답', model: 'c'},
    codex: async () => ({text: 'G답', model: 'g'}),
    gemini: async () => { throw new Error('quota exceeded'); },
  };
  await processJob({update_id: 6, text: '@all 전략 평가'}, {api, providers});
  assert.match(api.state.replies[0].text, /\[Claude\(구독\)\]\nC답/);
  assert.match(api.state.replies[0].text, /\[Gemini\(구독, 웹 검색\)\]\n답변 실패/);
  assert.deepEqual(api.state.replies.at(-1), {id: 6, text: '', done: true});
  assert.equal(api.state.replies.length, 2);
});

test('Gemini가 없으면 최신 정보 질문에 Claude가 웹 검색을 켜고, 일반 질문은 끄고 답한다', async () => {
  const flags = [];
  const providers = {claude: async ({webSearch, system}) => {
    if (system.startsWith('너는 개인 비서의 학습')) return {text: '{"updates":{}}', model: 'h'};
    flags.push({webSearch: Boolean(webSearch), prompt: system.includes('웹 검색을 사용')});
    return {text: '답', model: 'claude-sonnet-5'};
  }};
  const api1 = fakeApi();
  await processJob({update_id: 8, text: '이번 주 식약처 보도자료 알려줘'}, {api: api1, providers});
  await processJob({update_id: 9, text: 'HACCP 7원칙 정리'}, {api: fakeApi(), providers});
  assert.deepEqual(flags, [{webSearch: true, prompt: true}, {webSearch: false, prompt: false}]);
  assert.match(api1.state.replies[0].text, /Claude\(구독\) · claude-sonnet-5 · 웹 검색/);
});

test('Worker가 이미 Actions로 넘겼으면(409) 중복 답변을 보내지 않는다', async () => {
  const api = fakeApi();
  api.reply = async (id, text) => { api.state.replies.push(text); return 409; };
  const providers = {claude: async () => ({text: '늦은 답', model: 'c'})};
  assert.deepEqual(await processJob({update_id: 7, text: '질문'}, {api, providers}), {ok: false});
  assert.equal(api.state.replies.length, 1);
  assert.equal(api.state.saves, 0);
});
