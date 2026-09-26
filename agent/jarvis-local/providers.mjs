// 구독 CLI 호출부. 각 CLI는 사용자 PC의 OAuth 로그인 세션만 사용한다(API 키 환경변수 제거).
import {spawn} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const IS_WINDOWS = process.platform === 'win32';
const APPDATA_NPM = process.env.APPDATA ? path.join(process.env.APPDATA, 'npm', 'node_modules') : '';
const BLOCKED_ENV = [
  'OPENAI_API_KEY', 'OPENAI_BASE_URL', 'CODEX_API_KEY', 'ANTHROPIC_API_KEY', 'ANTHROPIC_BASE_URL',
  'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_MODEL', 'ANTHROPIC_CUSTOM_HEADERS', 'CLAUDE_CODE_USE_BEDROCK',
  'CLAUDE_CODE_USE_VERTEX', 'GEMINI_API_KEY', 'GOOGLE_API_KEY', 'GOOGLE_GENAI_USE_VERTEXAI',
];

export function subscriptionEnv(base = process.env) {
  const env = {...base};
  for (const key of BLOCKED_ENV) delete env[key];
  return env;
}

export function resolveCommands() {
  const home = os.homedir();
  const claudeExe = [path.join(home, '.local', 'bin', IS_WINDOWS ? 'claude.exe' : 'claude')].find(p => fs.existsSync(p));
  const codexJs = APPDATA_NPM && path.join(APPDATA_NPM, '@openai', 'codex', 'bin', 'codex.js');
  const geminiJs = APPDATA_NPM && path.join(APPDATA_NPM, '@google', 'gemini-cli', 'bundle', 'gemini.js');
  return {
    claude: claudeExe ? {command: claudeExe, prefix: []} : null,
    codex: codexJs && fs.existsSync(codexJs) ? {command: process.execPath, prefix: [codexJs]} : null,
    // Gemini는 Google 로그인(oauth_creds.json)이 끝난 경우에만 사용한다.
    gemini: geminiJs && fs.existsSync(geminiJs) && fs.existsSync(path.join(home, '.gemini', 'oauth_creds.json'))
      ? {command: process.execPath, prefix: [geminiJs]} : null,
  };
}

export function runCli({command, args, input, timeoutMs, cwd}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {cwd, env: subscriptionEnv(), stdio: ['pipe', 'pipe', 'pipe'], windowsHide: true});
    let stdout = '';
    let stderr = '';
    const timer = setTimeout(() => {
      if (IS_WINDOWS && child.pid) spawn('taskkill', ['/pid', String(child.pid), '/T', '/F'], {windowsHide: true});
      else child.kill('SIGTERM');
      reject(new Error('timeout'));
    }, timeoutMs);
    child.stdout.on('data', chunk => { stdout += chunk; if (stdout.length > 8e6) child.kill(); });
    child.stderr.on('data', chunk => { stderr += chunk; if (stderr.length > 1e6) stderr = stderr.slice(-2e5); });
    child.on('error', error => { clearTimeout(timer); reject(error); });
    child.on('close', code => {
      clearTimeout(timer);
      if (code === 0) resolve({stdout, stderr});
      else reject(new Error(`exit ${code}: ${(stderr || stdout).slice(-600)}`));
    });
    child.stdin.end(input ?? '');
  });
}

export function makeProviders({commands = resolveCommands(), runner = runCli, workDir, config = {}}) {
  const cwd = workDir;
  const providers = {};

  if (commands.claude) {
    providers.claude = async ({system, prompt, model, timeoutMs = 180000}) => {
      const args = [
        ...commands.claude.prefix, '-p', '--output-format', 'json', '--max-turns', '1',
        '--model', model || config.claudeModel || 'sonnet', '--tools', '', '--system-prompt', system,
        // 사용자 전역 설정(~/.claude/settings.json)의 모델 별칭 재지정·훅을 적용하지 않는다.
        // 전역 설정은 sonnet→opus, haiku→크레딧 필요 모델로 바꿔 Pro 한도를 빨리 소모하거나 429를 낸다.
        '--setting-sources', 'project,local',
      ];
      const {stdout} = await runner({command: commands.claude.command, args, input: prompt, timeoutMs, cwd});
      const data = JSON.parse(stdout.slice(stdout.indexOf('{')));
      if (data.is_error || !String(data.result || '').trim()) throw new Error(`claude: ${String(data.result || data.subtype || 'empty').slice(0, 300)}`);
      const usage = Object.entries(data.modelUsage || {});
      usage.sort((a, b) => (Number(b[1]?.outputTokens) || 0) - (Number(a[1]?.outputTokens) || 0));
      const used = usage[0]?.[0] || model || 'claude';
      return {text: String(data.result).trim(), model: used};
    };
  }

  if (commands.codex) {
    providers.codex = async ({system, prompt, timeoutMs = 180000}) => {
      const args = [
        ...commands.codex.prefix, 'exec', '-', '--sandbox', 'read-only', '--skip-git-repo-check', '--json',
        '-c', `model_reasoning_effort="${config.codexEffort || 'low'}"`,
      ];
      const {stdout} = await runner({command: commands.codex.command, args, input: `${system}\n\n---\n\n${prompt}`, timeoutMs, cwd});
      let text = '';
      for (const line of stdout.split('\n')) {
        try {
          const event = JSON.parse(line.trim());
          if (event.type === 'item.completed' && event.item?.type === 'agent_message') text = String(event.item.text || '').trim();
        } catch {}
      }
      if (!text) throw new Error('codex: empty');
      return {text, model: 'ChatGPT/Codex'};
    };
  }

  if (commands.gemini) {
    providers.gemini = async ({system, prompt, timeoutMs = 180000}) => {
      const args = [
        ...commands.gemini.prefix, '-o', 'json', '--approval-mode', 'plan',
        '-p', '위 지시와 질문에 답하라. 최신 정보가 필요하면 웹 검색을 사용하라.',
      ];
      const {stdout} = await runner({command: commands.gemini.command, args, input: `${system}\n\n---\n\n${prompt}`, timeoutMs, cwd});
      const data = JSON.parse(stdout.slice(stdout.indexOf('{')));
      const text = String(data.response || '').trim();
      if (!text) throw new Error(`gemini: ${JSON.stringify(data.error || 'empty').slice(0, 300)}`);
      const models = Object.keys(data.stats?.models || {});
      return {text, model: models[0] || 'gemini'};
    };
  }

  return providers;
}
