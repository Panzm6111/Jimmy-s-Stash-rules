'use strict';
// Fixtures below reconstruct field shapes from pinned upstream code. They are
// NOT captured current App responses and do not establish native Stash success.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
function run(id,url,body,extra={}) {
  const done=[],logs=[];
  const ctx={
    $argument:'diagnostic=1',
    $request:{method:'GET',url,headers:{Cookie:'PRIVATE_SENTINEL'},body:'PRIVATE_SENTINEL'},
    $response:{status:200,body:typeof body==='string'?body:JSON.stringify(body)},
    console:{log:x=>logs.push(x)},$done:x=>done.push(x),
    $httpClient:new Proxy({},{get(){throw Error('FORBIDDEN_NETWORK');}}),
    $persistentStore:new Proxy({},{get(){throw Error('FORBIDDEN_STORAGE');}}),
    ...extra
  };
  vm.runInNewContext(fs.readFileSync(path.join(root,'scripts/ads',id+'.js'),'utf8'),ctx,{timeout:1000});
  assert.equal(done.length,1);
  assert.doesNotMatch(logs.join('\n'),/PRIVATE_SENTINEL|https:|Cookie|Authorization|token|FORBIDDEN/);
  return {out:JSON.parse(JSON.stringify(done[0])),logs};
}
const xhs='https://edith.xiaohongshu.com/api/sns/';
const wb='https://api.weibo.cn/2/';
test('XHS config removes only splash; theme/store/loading and coupon fields survive',()=>{
  const keep={app_theme:{name:'normal'},store:{coupon:7},loading_img:'normal-image'};
  const a=run('xiaohongshu',xhs+'v1/system_service/config/?token=EXAMPLE_NOT_A_SECRET',{code:'0',data:{splash:{ads:[1]},...keep}});
  assert.deepEqual(JSON.parse(a.out.body).data,keep);
  assert.match(a.logs[0],/AD-20261020\.1\] changed$/);
});
test('XHS v6 sponsored items only; shopping notes, live, icons, null and empty markers stay',()=>{
  const keep=[{model_type:'live_v2'},{note_attributes:['goods']},{card_icon:'normal'},{ads_info:null},{ads_info:{}},null];
  const a=run('xiaohongshu',xhs+'v6/homefeed?x=1',{success:true,code:0,data:[{ads_info:{ad_id:'simulated'}},...keep],other:7});
  assert.deepEqual(JSON.parse(a.out.body),{success:true,code:0,data:keep,other:7});
  assert.deepEqual(run('xiaohongshu',xhs+'v6/homefeed',a.out.body).out,{});
});
test('XHS unknown versions and near paths remain unchanged',()=>{
  for(const p of ['v7/homefeed','v6/homefeedExtra','v1/system_service/configExtra','v6/note/feed'])
    assert.deepEqual(run('xiaohongshu',xhs+p,{data:[{ads_info:{ad_id:1}}]}).out,{});
});
test('Weibo topic/search use explicit labels only; preserve business fields and child lists',()=>{
  const keep={data:{is_ad:0,mblogtypename:'ordinary',id:7}};
  for(const p of ['searchall','statuses/container_timeline_topic','statuses/container_timeline_topicpage']) {
    const a=run('weibo',wb+p+'/',{items:[{data:{mblogtypename:'广告'}},{data:{is_ad:1}},{data:{ad_state:1}},keep,null],user:{id:'PRIVATE_SENTINEL'}});
    assert.deepEqual(JSON.parse(a.out.body).items,[keep,null]);
    assert.deepEqual(JSON.parse(a.out.body).user,{id:'PRIVATE_SENTINEL'});
  }
});
test('Weibo search nested ads removed without deleting ordinary recommendation data',()=>{
  const a=run('weibo',wb+'searchall',{items:[{items:[{data:{ad_state:1}},{data:{id:1}}]}]});
  assert.deepEqual(JSON.parse(a.out.body),{items:[{items:[{data:{id:1}}]}]});
});
test('JD flat and nested images use ad controls; orders/coupons/countdown preserved',()=>{
  for(const images of [[{showTimes:'2',time:'5',onlineTime:'2026-10-01 00:00:00'}],[[{showTimes:2,time:5}]]]) {
    const a=run('jingdong','https://api.m.jd.com/client.action?client=ios&functionId=start',{code:'0',images,showTimesDaily:2,countdown:100,orders:[1],coupons:[2]});
    const o=JSON.parse(a.out.body);assert.deepEqual(o.orders,[1]);assert.deepEqual(o.coupons,[2]);assert.equal(o.countdown,100);
    assert.ok([0,'0'].includes(o.images.flat()[0].showTimes));assert.equal(o.showTimesDaily,0);
    assert.deepEqual(run('jingdong','https://api.m.jd.com/client.action?functionId=start',a.out.body).out,{});
  }
});
test('JD unknown control types and duplicated function IDs are not treated as supported ads',()=>{
  const u='https://api.m.jd.com/client.action?functionId=start';
  assert.deepEqual(run('jingdong',u,{images:[{showTimes:{unknown:true}}],showTimesDaily:5}).out,{});
  for(const suffix of ['&functionId=myOrderInfo','&functionId=start']) assert.deepEqual(run('jingdong',u+suffix,{images:[{showTimes:2}]}).out,{});
});
test('response runtime distinguishes null/empty/binary body instead of fabricating JSON',()=>{
  for(const resp of [null,{}, {status:200,body:new Uint8Array([1,2])}]) {
    const a=run('xiaohongshu',xhs+'v1/system_service/splash_config',null,{$response:resp});
    assert.deepEqual(a.out,{});assert.match(a.logs[0],/body-unavailable$/);
  }
});
test('diagnostic statuses separate malformed JSON, nonJSON, unknown schema and known no-op',()=>{
  const u=xhs+'v1/system_service/splash_config';
  for(const [body,state] of [['<html>no</html>','non-json'],['{broken','parse-error'],[{},'unsupported-schema'],[{code:0,data:{ads_groups:[]}},'unchanged']]) {
    const a=run('xiaohongshu',u,body);assert.deepEqual(a.out,{});assert.ok(a.logs[0].endsWith(' '+state));
  }
});
test('UTF8 size limit catches multi-byte payload below the old character limit',()=>{
  const u=xhs+'v1/system_service/splash_config';
  const a=run('xiaohongshu',u,{data:{ads_groups:[{id:'ad'}]},padding:'中'.repeat(750000)});
  assert.deepEqual(a.out,{});assert.match(a.logs[0],/body-too-large$/);
});
test('diagnostics default off, malformed arguments do not enable logging',()=>{
  for(const arg of [undefined,'diagnostic=0','diagnostic=10','xdiagnostic=1','Cookie=PRIVATE_SENTINEL']) {
    const a=run('xiaohongshu',xhs+'v1/system_service/splash_config',{data:{ads_groups:[{id:'ad'}]}},{$argument:arg});
    assert.equal(typeof a.out.body,'string');assert.deepEqual(a.logs,[]);
  }
});
test('exceptions and broken logging still call done exactly once without data leakage',()=>{
  const req={get url(){throw Error('PRIVATE_SENTINEL');}};
  const a=run('xiaohongshu','',null,{$request:req});assert.deepEqual(a.out,{});assert.match(a.logs[0],/exception$/);
  const b=run('xiaohongshu',xhs+'v1/system_service/splash_config',{data:{ads_groups:[{id:'ad'}]}},{console:{log(){throw Error('PRIVATE_SENTINEL');}}});
  assert.equal(typeof b.out.body,'string');
});
test('passive probe observes known matches and near-path misses; never changes a request',()=>{
  for(const [url,state] of [[xhs+'v1/system_service/splash_config?token=EXAMPLE_NOT_A_SECRET','request-url-matched'],[xhs+'v1/login?token=EXAMPLE_NOT_A_SECRET','request-url-unmatched']]) {
    const a=run('probe',url,null);assert.deepEqual(a.out,{});assert.ok(a.logs[0].endsWith(state));
  }
});
