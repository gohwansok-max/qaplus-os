// Jarvis PC 에이전트: Worker에 쌓인 질문을 가져와 구독 모델(Claude Pro, ChatGPT Plus, Gemini Pro)로 답한다.
// PC가 꺼져 있으면 Worker가 60초 뒤 GitHub Actions(OpenAI API)로 자동 전환한다.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {
  LEARNING_INSTRUCTIONS, PROVIDER_LABELS, applyLearning, cleanForTelegram, conversationPrompt,
  isLimitError, learningPrompt, normalizeMemory, parseLearning, personaPrompt, route,
} from './lib.mjs';
import {makeProviders} from './providers.mjs';

export const HOME_DIR = path.join(process.env.LOCALAPPDATA || os.homedir(), 'JarvisAgent');

export function createApi({workerUrl, agentToken, fetchImpl = fetch}) {
  const call = async (method, pathName, body) => {
    const response = await fetchImpl(`${workerUrl}${pathName}`, {
      method,
      headers: {Authorization: `Bearer ${agentToken}`, 'Content-Type': 'application/json'},
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.timeout(20000),
    });
    const data = await response.json().catch(() => ({}));
    return {status: response.status, data};
  };
  return {
    poll: async capabilities => (await call('POST', '/agent/poll', {capabilities})).data.job || null,
    reply: async (updateId, text, done) => (await call('POST', '/agent/reply', {update_id: updateId, text, done})).status,
    loadMemory: async () => {
      const {status, data} = await call('GET', '/memory');
      if (status !== 200) throw new Error(`memory ${status}`);
      return normalizeMemory(data.doc);
    },
    saveMemory: async doc => {
      const {status, data} = await call('PUT', '/memory', {expected_rev: doc.rev, doc});
      if (status === 409) return false;
      if (status !== 200) throw new Error(`memory save ${status}`);
      doc.rev = data.rev;
      return true;
    },
  };
}

async function answerWith(providers, order, doc, query, log, fresh = false) {
  const errors = [];
  for (const id of order) {
    const started = Date.now();
    try {
      const webSearch = id === 'gemini' || (fresh && id === 'claude');
      const result = await providers[id]({system: personaPrompt(doc, {webSearch}), prompt: conversationPrompt(doc, query), webSearch});
      if (webSearch) result.webSearch = true;
      log({event: 'answered', provider: id, model: result.model, ms: Date.now() - started});
      return {...result, provider: id, errors};
    } catch (error) {
      const limit = isLimitError(error.message);
      const kind = /too long/i.test(error.message) ? 'prompt_too_long' : /timeout/.test(error.message) ? 'timeout' : /login|auth/i.test(error.message) ? 'auth' : 'other';
      log({event: 'provider_failed', provider: id, limit, kind, ms: Date.now() - started});
      errors.push(`${PROVIDER_LABELS[id]}: ${limit ? '사용 한도 도달' : '실패'}`);
    }
  }
  throw Object.assign(new Error('all providers failed'), {errors});
}

/** 질문 1건 처리. 외부 의존성은 주입받는다(테스트 가능). */
export async function processJob(job, {api, providers, log = () => {}, learnModel = 'haiku'}) {
  const available = Object.keys(providers);
  const plan = route(job.text, available);
  let doc;
  try { doc = await api.loadMemory(); } catch { doc = normalizeMemory(null); log({event: 'memory_load_failed'}); }

  let answerText;
  let learnedFrom;
  if (plan.mode === 'all') {
    const results = await Promise.allSettled(plan.order.map(id => answerWith(providers, [id], doc, plan.query, log)));
    const sections = results.map((r, i) => `[${PROVIDER_LABELS[plan.order[i]]}]\n${r.status === 'fulfilled' ? cleanForTelegram(r.value.text).slice(0, 1300) : '답변 실패'}`);
    answerText = `세 모델 비교\n\n${sections.join('\n\n')}`;
    learnedFrom = results.find(r => r.status === 'fulfilled')?.value.text || '';
  } else {
    try {
      const result = await answerWith(providers, plan.order, doc, plan.query, log, plan.fresh);
      const note = result.errors.length ? `\n(${result.errors.join(', ')} → 다음 모델로 전환)` : '';
      const web = result.webSearch && result.provider === 'claude' ? ' · 웹 검색' : '';
      answerText = `${cleanForTelegram(result.text)}\n\n— ${PROVIDER_LABELS[result.provider]} · ${result.model}${web}${note}`;
      learnedFrom = result.text;
    } catch (error) {
      await api.reply(job.update_id, `구독 모델이 모두 응답하지 못했습니다.\n${(error.errors || []).join('\n')}`, true);
      return {ok: false};
    }
  }

  const status = await api.reply(job.update_id, answerText, false);
  if (status === 409) { log({event: 'reply_rejected_fallback_took_over', update_id: job.update_id}); return {ok: false}; }

  let learning = {updates: {}};
  if (providers.claude || providers.codex) {
    try {
      const learner = providers.claude ? 'claude' : 'codex';
      const out = await providers[learner]({system: LEARNING_INSTRUCTIONS, prompt: learningPrompt(doc, plan.query, learnedFrom), model: learnModel, timeoutMs: 120000});
      learning = parseLearning(out.text);
    } catch (error) {
      // 원문 대신 실패 유형만 기록한다.
      const kind = /too long/i.test(error.message) ? 'prompt_too_long' : isLimitError(error.message) ? 'limit' : /timeout/.test(error.message) ? 'timeout' : 'other';
      log({event: 'learning_failed', kind});
    }
  }

  let added = [];
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const current = await api.loadMemory();
      added = applyLearning(current, plan.query, learnedFrom, learning);
      if (await api.saveMemory(current)) break;
    } catch { log({event: 'memory_save_failed'}); break; }
  }
  const done = added.length
    ? `새로 기억한 내용:\n${added.slice(0, 5).map(t => `- ${t}`).join('\n')}\n\n/memory 로 전체 확인, 틀린 내용은 '기억 수정: ...'으로 알려주세요.`
    : null;
  await api.reply(job.update_id, done || '', true);
  return {ok: true, added};
}

function makeLogger() {
  fs.mkdirSync(HOME_DIR, {recursive: true});
  const file = path.join(HOME_DIR, 'agent.log');
  return entry => {
    // 질문·답변 원문은 기록하지 않는다.
    const line = `${new Date().toISOString()} ${JSON.stringify(entry)}\n`;
    try {
      if (fs.existsSync(file) && fs.statSync(file).size > 2e6) fs.renameSync(file, `${file}.1`);
      fs.appendFileSync(file, line);
    } catch {}
  };
}

async function main() {
  const config = JSON.parse(fs.readFileSync(path.join(HOME_DIR, 'config.json'), 'utf8'));
  const workDir = path.join(HOME_DIR, 'work');
  fs.mkdirSync(workDir, {recursive: true});
  const log = makeLogger();
  const api = createApi(config);
  let providers = makeProviders({workDir, config});
  let refreshedAt = Date.now();
  log({event: 'started', providers: Object.keys(providers)});

  for (;;) {
    try {
      if (Date.now() - refreshedAt > 10 * 60 * 1000) {
        providers = makeProviders({workDir, config});  // Gemini 로그인 등 변경 반영
        refreshedAt = Date.now();
      }
      const job = await api.poll(Object.keys(providers));
      if (job) {
        log({event: 'job', update_id: job.update_id});
        await processJob(job, {api, providers, log, learnModel: config.learnModel || 'haiku'});
        continue;
      }
      await new Promise(resolve => setTimeout(resolve, config.pollMs || 3000));
    } catch (error) {
      log({event: 'loop_error', message: String(error.message).slice(0, 200)});
      await new Promise(resolve => setTimeout(resolve, 10000));
    }
  }
}

if (import.meta.url === pathToFileURL(process.argv[1] || '').href) main();
