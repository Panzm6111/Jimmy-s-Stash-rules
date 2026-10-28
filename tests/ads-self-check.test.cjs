'use strict';
// Local host-API simulations, not native Stash or iPhone execution evidence.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const generated = JSON.parse(execFileSync(process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3'), ['-X','utf8','-c', 'import sys,json;sys.path.insert(0,"tools");from build_ad_diagnostics import self_check_rendered;print(json.dumps(self_check_rendered()))'], {cwd: root}));
const script = generated['scripts/ads/self-check.js'];
const now = 1792500000000;
const key = 'jimmy.ads.diag.session.v1';
const moduleKey = 'jimmy.ads.diag.taobao.v1';
const base = 'https://example.com/jimmy-stash-check';
function run(url=base, options={}) {
  const data = options.data instanceof Map ? options.data : new Map(Object.entries(options.data || {}));
  const reads=[], writes=[], done=[];
  const store = {
    read(k) { reads.push(k); if(options.readFail) throw Error('PRIVATE_SENTINEL'); return data.get(k) ?? null; },
    write(v,k) { writes.push([k,v]); if(options.writeFail) return false; data.set(k,v); return true; }
  };
  class FakeDate extends Date { static now() { return options.now ?? now; } }
  const req = {method: options.method || 'GET', url};
  Object.defineProperties(req, {
    headers: {get() {throw Error('PRIVATE_SENTINEL');}},
    body: {get() {throw Error('PRIVATE_SENTINEL');}}
  });
  const context = {$request:req, Date:FakeDate, $done:v=>done.push(v), $persistentStore:store,
    $httpClient:new Proxy({}, {get(){throw Error('FORBIDDEN_NETWORK');}}),
    console:{log(){throw Error('FORBIDDEN_LOG');}}};
  if(options.noStorage) delete context.$persistentStore;
  vm.runInNewContext(script, context, {timeout:1000});
  assert.equal(done.length,1);
  const out=JSON.parse(JSON.stringify(done[0]));
  assert.doesNotMatch(JSON.stringify(out), /PRIVATE_SENTINEL|FORBIDDEN_NETWORK|FORBIDDEN_LOG/);
  return {out,data,reads,writes,store};
}
function session(until=now+900000) { return JSON.stringify({id:now,until}); }
function record(extra={}) { return JSON.stringify({sessionId:now,version:'AD-20261020.5',last:now,counts:{changed:2},...extra}); }
test('manual page returns native response envelope once, actual protocol and no-store',()=>{
  for(const protocol of ['http','https']) {
    const {out,reads,writes}=run(protocol+'://example.com/jimmy-stash-check');
    assert.equal(out.response.status,200);
    assert.equal(out.response.headers['Content-Type'],'text/html; charset=utf-8');
    assert.equal(out.response.headers['Cache-Control'],'no-store');
    assert.match(out.response.body,new RegExp('<strong>'+protocol+'</strong>'));
    assert.match(out.response.body,/AD-20261020\.5/);
    assert.match(out.response.body,/这不证明淘宝等App已命中/);
    assert.match(out.response.body,/尚未开始诊断/);
    assert.deepEqual(writes,[]);
    assert.deepEqual(reads,[key]);
    assert.doesNotMatch(out.response.body,/<script|(?:src|href)="https?:\/\//i);
  }
});
test('near URLs, other query parameters and methods pass through without reading storage',()=>{
  for(const url of [
    'https://example.com.evil.invalid/jimmy-stash-check',
    'https://www.example.com/jimmy-stash-check',
    'https://example.com:8443/jimmy-stash-check',
    base+'Extra',base+'//',base+'?',base+'?start=0',base+'?start=1&stop=1',
    base+'?token=EXAMPLE_NOT_A_SECRET',base+'?%73tart=1',base+'#fragment'
  ]) {
    const r=run(url);assert.deepEqual(r.out,{});assert.deepEqual(r.reads,[]);assert.deepEqual(r.writes,[]);
  }
  for(const method of ['POST','HEAD','get']) {
    const r=run(base,{method});assert.deepEqual(r.out,{});assert.deepEqual(r.reads,[]);
  }
});
test('explicit supported ports and trailing slash are accepted',()=>{
  for(const url of ['http://example.com:80/jimmy-stash-check/','https://example.com:443/jimmy-stash-check/'])
    assert.equal(run(url).out.response.status,200);
});
test('start writes only a 15-minute session; result refresh does not reset it',()=>{
  const start=run(base+'?start=1');
  assert.deepEqual(start.writes,[[key,session()]]);
  assert.match(start.out.response.body,/返回结果页/);
  assert.match(start.out.response.body,/避免刷新带开始参数/);
  const refresh=run(base,{data:Object.fromEntries(start.data),now:now+5000});
  assert.deepEqual(refresh.writes,[]);
  assert.equal(refresh.data.get(key),session());
  assert.match(refresh.out.response.body,/记录中/);
});
test('stop preserves the session ID and results without starting a session implicitly',()=>{
  const r=run(base+'?stop=1',{data:{[key]:session(),[moduleKey]:record()}});
  assert.deepEqual(JSON.parse(r.data.get(key)),{id:now,until:0});
  assert.match(r.out.response.body,/已手动停止/);
  assert.match(r.out.response.body,/实际产生修改：2/);
  const absent=run(base+'?stop=1');
  assert.deepEqual(absent.writes,[]);
  assert.match(absent.out.response.body,/没有可停止的有效诊断会话/);
});
test('only current-session whitelisted state counts and validated version/time are displayed',()=>{
  const r=run(base,{data:{
    [key]:session(),
    [moduleKey]:record({counts:{changed:2,'unsupported-schema':3,unchanged:0}}),
    'jimmy.ads.diag.weibo.v1':record({sessionId:now-1,counts:{changed:999}})
  }});
  assert.match(r.out.response.body,/实际产生修改：2/);
  assert.match(r.out.response.body,/响应结构未支持：3/);
  assert.doesNotMatch(r.out.response.body,/实际产生修改：999/);
  assert.match(r.out.response.body,/北京时间/);
  assert.equal(r.reads.length,12);
  assert.deepEqual(r.writes,[]);
});
test('expired session shows retained results but reports automatic recording stop',()=>{
  const r=run(base,{now:now+900001,data:{[key]:session(),[moduleKey]:record()}});
  assert.match(r.out.response.body,/15分钟已结束/);
  assert.match(r.out.response.body,/实际产生修改：2/);
  assert.doesNotMatch(r.out.response.body,/记录中/);
  assert.deepEqual(r.writes,[]);
});
test('missing, throwing or damaged storage leaves self-check usable and declares recording unavailable',()=>{
  for(const options of [
    {noStorage:true},{readFail:true},{data:{[key]:'not-json'}},
    {data:{[key]:JSON.stringify({id:now+1,until:now+900000})}},
    {data:{[key]:JSON.stringify({id:now,until:now+900001})}}
  ]) {
    const r=run(base,options);assert.equal(r.out.response.status,200);
    assert.match(r.out.response.body,/无法可靠记录/);
    assert.match(r.out.response.body,/这不能直接证明MITM失败/);
  }
  const fail=run(base+'?start=1',{writeFail:true});
  assert.match(fail.out.response.body,/写入失败/);
  assert.doesNotMatch(fail.out.response.body,/记录中/);
  const unreadable=run(base+'?start=1',{readFail:true});
  assert.match(unreadable.out.response.body,/读回核对失败/);
  assert.doesNotMatch(unreadable.out.response.body,/已开始15分钟诊断|记录中/);
});
test('malicious stored fields and counts cannot inject HTML or leak storage strings',()=>{
  for(const candidate of [
    {version:'<script>PRIVATE_SENTINEL</script>'},
    {last:'PRIVATE_SENTINEL'},
    {last:now+1},
    {counts:{changed:'PRIVATE_SENTINEL'}},
    {counts:{changed:-1}},
    {counts:{changed:1.5}},
    {counts:{changed:10000}},
    {counts:{changed:Number.MAX_SAFE_INTEGER+1}},
    {counts:{'<script>PRIVATE_SENTINEL</script>':1}},
    {counts:JSON.parse('{"__proto__":1}')},
    {counts:[]}
  ]) {
    const r=run(base,{data:{[key]:session(),[moduleKey]:record(candidate)}});
    assert.match(r.out.response.body,/本机记录损坏或读取失败/);
    assert.doesNotMatch(r.out.response.body,/<script/i);
  }
});
test('no observations does not claim MITM failure or actual advertisement removal',()=>{
  const r=run(base,{data:{[key]:session()}});
  assert.match(r.out.response.body,/可能尚未发出新请求、URL未匹配、脚本资源未更新、使用缓存或流量没有进入HTTP引擎/);
  assert.match(r.out.response.body,/原生URL拒绝和域名拦截不经过这些脚本/);
  assert.match(r.out.response.body,/仅在设备保存/);
  assert.match(r.out.response.body,/只新增example\.com这个精确解密主机/);
});
test('start, actual generated ad handler, result page and stop share one device observation session',()=>{
  const start=run(base+'?start=1');
  assert.match(start.out.response.body,/已开始15分钟诊断/);
  const adScript=fs.readFileSync(path.join(root,'scripts/ads/xiaohongshu.js'),'utf8');
  assert.match(adScript,/version AD-20261020\.5/);
  const observedKey='jimmy.ads.diag.xiaohongshu.v1';
  function executeAd(clock) {
    const done=[],logs=[];
    class FakeDate extends Date { static now() { return clock; } }
    vm.runInNewContext(adScript,{
      Date:FakeDate,$argument:'diagnostic=0',$persistentStore:start.store,
      $request:{
        method:'GET',
        url:'https://edith.xiaohongshu.com/api/sns/v1/system_service/config?token=EXAMPLE_NOT_A_SECRET',
        headers:{Cookie:'PRIVATE_SENTINEL',Authorization:'PRIVATE_SENTINEL'},
        body:'PRIVATE_SENTINEL'
      },
      $response:{
        status:200,headers:{'Set-Cookie':'PRIVATE_SENTINEL'},
        body:JSON.stringify({code:0,data:{splash:{ads:[{id:'simulated-ad'}]},
          app_theme:{name:'normal'},coupons:{count:2}},account:'PRIVATE_SENTINEL'})
      },
      console:{log:value=>logs.push(value)},$done:value=>done.push(value)
    },{timeout:1000});
    assert.equal(done.length,1);
    assert.deepEqual(JSON.parse(done[0].body),{
      code:0,data:{app_theme:{name:'normal'},coupons:{count:2}},account:'PRIVATE_SENTINEL'
    });
    assert.deepEqual(logs,[]);
    assert.doesNotMatch(JSON.stringify(start.writes),/PRIVATE_SENTINEL|EXAMPLE_NOT_A_SECRET|https:|simulated-ad|Cookie|Authorization/);
  }
  executeAd(now+1000);
  assert.deepEqual(JSON.parse(start.data.get(observedKey)),{
    sessionId:now,version:'AD-20261020.5',last:now+1000,counts:{changed:1}
  });
  const result=run(base,{data:start.data,now:now+2000});
  assert.equal(result.data,start.data);
  assert.match(result.out.response.body,/小红书开屏广告处理/);
  assert.match(result.out.response.body,/实际产生修改：1/);
  assert.match(result.out.response.body,/AD-20261020\.5/);
  assert.deepEqual(result.writes,[]);
  const stop=run(base+'?stop=1',{data:start.data,now:now+3000});
  assert.deepEqual(JSON.parse(start.data.get(key)),{id:now,until:0});
  assert.match(stop.out.response.body,/已手动停止/);
  const before=start.data.get(observedKey),writeCount=start.writes.length;
  executeAd(now+4000);
  assert.equal(start.data.get(observedKey),before);
  assert.equal(start.writes.length,writeCount);
  const stopped=run(base,{data:start.data,now:now+5000});
  assert.match(stopped.out.response.body,/实际产生修改：1/);
  assert.match(stopped.out.response.body,/已手动停止/);
});
