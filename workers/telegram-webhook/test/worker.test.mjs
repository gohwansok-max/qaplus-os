import test from 'node:test';
import assert from 'node:assert/strict';
import worker, {classify, TelegramUpdate} from '../src/index.mjs';

const env = {TELEGRAM_CHAT_ID:'42', TELEGRAM_BOT_TOKEN:'test', QA_DISPATCH_TOKEN:'test', WEBHOOK_SECRET:'test', GITHUB_REPOSITORY:'owner/repo'};
const update = text => ({update_id:1, message:{chat:{id:42}, text}});
test('명령과 콜백을 정확히 분류하고 다른 대화방은 차단', () => {
  for (const text of ['/help', '/start@bot', '/make']) assert.equal(classify(update(text), '42').kind, 'help');
  for (const text of ['/daily', '/daily@bot']) assert.deepEqual(classify(update(text), '42'), {kind:'video', topic:''});
  assert.deepEqual(classify(update('/make@bot 테스트 주제'), '42'), {kind:'video', topic:'테스트 주제'});
  assert.equal(classify(update('/makeevil'), '42').kind, 'unknown');
  assert.equal(classify(update('/help'), '43').kind, 'forbidden');
  assert.equal(classify({update_id:1,callback_query:{id:'x',data:'blog_publish:123',message:{chat:{id:42}}}},'42').kind,'blog_publish');
});
test('Secret 검증을 우회할 수 없음', async () => {
  const response = await worker.fetch(new Request('https://test/telegram',{method:'POST',body:'{}'}),env);
  assert.equal(response.status,403);
});
function object() {
  const data = new Map(); let chain = Promise.resolve();
  const ctx = {storage:{get:async k=>data.get(k),put:async(k,v)=>data.set(k,v),setAlarm:async()=>{},deleteAll:async()=>data.clear()},
    blockConcurrencyWhile:fn=>{const result=chain.then(fn);chain=result.catch(()=>{});return result;}};
  return new TelegramUpdate(ctx,env);
}
test('동시 중복 요청도 GitHub dispatch 한 번', async () => {
  const original=globalThis.fetch; let dispatches=0;
  globalThis.fetch=async url=>{if(url.includes('github')){dispatches++;return new Response(null,{status:204});}return Response.json({ok:true});};
  try {
    const obj=object(); const req=()=>new Request('https://internal',{method:'POST',body:JSON.stringify({kind:'blog_publish',post_id:'123',callback_id:'x',update_id:1})});
    const responses=await Promise.all([obj.fetch(req()),obj.fetch(req()),obj.fetch(req())]);
    assert.equal(dispatches,1); assert.ok((await responses[1].json()).duplicate);
  } finally {globalThis.fetch=original;}
});
test('GitHub 실패는 503으로 재전송 허용, 성공 후 ACK 실패는 재실행 금지',async()=>{
  const original=globalThis.fetch;let dispatches=0;
  globalThis.fetch=async url=>{if(url.includes('github')){dispatches++;return new Response(null,{status:dispatches===1?503:204});}throw new Error('network');};
  try{
    const obj=object();const req=()=>new Request('https://internal',{method:'POST',body:JSON.stringify({kind:'video',topic:'test',update_id:2})});
    assert.equal((await obj.fetch(req())).status,503);
    assert.equal((await obj.fetch(req())).status,200);
    assert.ok((await (await obj.fetch(req())).json()).duplicate);
    assert.equal(dispatches,2);
  }finally{globalThis.fetch=original;}
});
