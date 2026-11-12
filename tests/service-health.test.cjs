const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../scripts/service-health.js'), 'utf8');
const GPT = 'GPT 服务优选', TT = 'TikTok 服务检测组', SG = '新加坡 A', TW_E = '台湾 E', TW_D = '台湾 D';
const chat = 'https://chatgpt.com/', tik = 'https://www.tiktok.com/foryou';
function setup() {
  const g = {'海外AI': {now:GPT}, 'TikTok':{now:TT},
    'AI组':{now:SG,all:['REJECT',SG,TW_E,TW_D]}, 'AI最速组':{now:SG,all:['REJECT',SG,TW_E,TW_D,'日本 A']},
    [GPT]:{now:'AI组',all:['AI组',SG,TW_E,TW_D,'无关']}, [TT]:{now:'AI最速组',all:['AI最速组',SG,TW_E,TW_D,'日本 A']}};
  const f = {g, mode:'rule', now:1600000000000, secret:'fixture-only', stored:{}, writes:[], calls:[], wire:[], logs:[], response:()=>({status:200})};
  class Clock extends Date { static now() { return f.now; } }
  async function run(step=60000) {
    f.now += step;
    await new Promise((done,reject) => {
      const http = Object.fromEntries(['get','head','put'].map(method=>[method,(opts,cb)=>{
        const parsed = new URL(opts.url);
        f.wire.push({method,opts});
        if (parsed.hostname==='127.0.0.1') {
          if (parsed.pathname==='/configs') return cb(null,{status:200},JSON.stringify({mode:f.mode}));
          if (parsed.pathname==='/proxies') return cb(null,{status:200},JSON.stringify({proxies:g}));
          if (method==='put') {
            const group=decodeURIComponent(parsed.pathname.substring('/proxies/'.length)), member=JSON.parse(opts.body).name;
            f.writes.push([group,member]); g[group].now=member;
            return cb(null,{status:204},'');
          }
        }
        const node=decodeURIComponent(opts.headers['X-Stash-Selected-Proxy']), url=opts.url;
        f.calls.push([url,node]);
        const r=f.response(url,node);
        cb(r.error || null,{status:r.status,headers:{'Content-Type':'text/html; charset=utf-8',...r.headers}},'');
      }]));
      try { vm.runInNewContext(source,{$httpClient:http,$argument:JSON.stringify({port:9090,secret:f.secret}),
        $persistentStore:{read:k=>f.stored[k],write:(v,k)=>{f.stored[k]=v;return true;}},
        Date:Clock, console:{log:s=>f.logs.push(s)}, $done:done}); }
      catch(e){reject(e);}
    });
  }
  return Object.assign(f,{run});
}

test('shared exit fails only GPT; second independent tick selects a verified backup and keeps authorization on loopback', async()=>{
  const f=setup(); f.response=(u,n)=>({status:u===chat && n===SG?503:200});
  await f.run(); await f.run(1000); assert.deepEqual(f.writes,[]);
  await f.run(); assert.deepEqual(f.writes,[[GPT,TW_E]]);
  assert.ok(f.calls.some(([u,n])=>u===tik && n===SG));
  assert.ok(!f.calls.some(([u,n])=>u===tik && n===TW_E));
  assert.ok(f.wire.every(({opts})=>opts['auto-redirect']===false && opts['auto-cookie']===false));
  for (const {method,opts} of f.wire) {
    assert.match(opts.headers['Cache-Control'],/no-cache/);
    if(opts.url.startsWith('http://127.0.0.1:9090/')) assert.equal(opts.headers.Authorization,'Bearer fixture-only');
    else {assert.equal(method,'head'); assert.ok([chat,tik].includes(opts.url)); assert.equal(opts.headers.Authorization,undefined);}
  }
  f.g['AI组'].now=TW_E; await f.run(300000);
  assert.deepEqual(f.writes,[[GPT,TW_E],[GPT,'AI组']]);
});
test('TikTok can switch independently while GPT stays on the same exit',async()=>{
  const f=setup();f.response=(u,n)=>({error:u===tik && n===SG?'timed out':null,status:u===tik && n===SG?0:200});
  await f.run(); await f.run();
  assert.deepEqual(f.writes,[[TT,TW_E]]); assert.equal(f.g[GPT].now,'AI组');
});
test('all unsuccessful candidates keep original; alternate checks are bounded and rotate',async()=>{
  const f=setup(); f.response=()=>({status:503});
  await f.run();await f.run();await f.run();
  assert.deepEqual(f.writes,[]); assert.ok(f.calls.some(([u,n])=>u===tik && n==='日本 A'));
  assert.ok(!f.calls.some(([,n])=>['REJECT','DIRECT','无关'].includes(n)));
  assert.equal(f.calls.filter(([u])=>u===tik).length,7);
});
test('challenge, redirects, wrong content and rate limits do not rotate exits',async()=>{
  for (const response of [{status:403},{status:301},{status:200,headers:{'cf-mitigated':'challenge'}},{status:200,headers:{'Content-Type':'application/json'}}]){
    const f=setup(); f.response=()=>response; await f.run();await f.run();assert.deepEqual(f.writes,[]);assert.equal(f.calls.length,4);
  }
  const f=setup();f.response=(u)=>u===chat?{status:429,headers:{'Retry-After':'600'}}:{status:200};
  await f.run(); await f.run(300000); assert.equal(f.calls.filter(([u])=>u===chat).length,1);
  assert.deepEqual(f.writes,[]); await f.run(301000); assert.equal(f.calls.filter(([u])=>u===chat).length,2);
});
test('manual parent selection, rule mode, stale samples and in-flight user changes are respected', async()=>{
  let f=setup();f.g['海外AI'].now='手动节点';await f.run();assert.ok(f.calls.every(([u])=>u===tik));
  f=setup();f.mode='global';await f.run();assert.deepEqual(f.calls,[]);
  f=setup();f.secret='REPLACE_ON_IPHONE';await f.run();assert.deepEqual(f.wire,[]);
  f=setup();f.response=(u,n)=>{
    if(u===chat && n===TW_E) f.g['海外AI'].now='手动节点';
    return {status:u===chat && n===SG ? 502 : 200};
  };
  await f.run();await f.run(160000);assert.equal(f.calls.filter(([u,n])=>u===chat && n===TW_E).length,0);
  await f.run();assert.deepEqual(f.writes,[]);assert.equal(f.g['海外AI'].now,'手动节点');
  f=setup();f.response=(u,n)=>{if(u===chat && n===TW_E) f.mode='global';return {status:u===chat && n===SG?502:200};};
  await f.run();await f.run();assert.deepEqual(f.writes,[]);
});

test('a stored iPhone compatibility choice uses the current AI pool and leaves default TikTok alone', async()=>{
  const f=setup();
  f.g.ai={now:'AI组',all:['AI组',SG,TW_E,TW_D]};
  f.g[GPT].all.push('ai');
  f.g[GPT].now='ai';
  f.g.TikTok.now='总代理';
  await f.run(); await f.run();
  assert.deepEqual(f.calls,[[chat,SG],[chat,SG]]);
  assert.deepEqual(f.writes,[]);
});
