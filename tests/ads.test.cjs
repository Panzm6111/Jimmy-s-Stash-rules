'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
function execute(moduleName, url, body, method = 'GET', status = 200, logCapture = null, requestOnly = false) {
  const code = fs.readFileSync(path.join(root, 'scripts/ads', moduleName + '.js'), 'utf8');
  let calls = 0, output;
  const logs = [];
  const context = {
    $argument: logCapture ? 'diagnostic=1' : 'diagnostic=0',
    $request: {url, method, headers: {Cookie: 'TEST_ONLY_NEVER_LOG'}},
    $response: {body: typeof body === 'string' ? body : JSON.stringify(body), status, headers: {'Set-Cookie': 'TEST_RESPONSE_COOKIE_NEVER_LOG'}},
    $done: value => { calls++; output = JSON.parse(JSON.stringify(value)); },
    console: {log: (...values) => logs.push(values)},
    $notification: new Proxy({}, {get() {throw new Error('notifications forbidden');}}),
    $httpClient: new Proxy({}, {get() {throw new Error('network forbidden');}}),
    $persistentStore: new Proxy({}, {get() {throw new Error('storage forbidden');}})
  };
  if (requestOnly) delete context.$response;
  vm.runInNewContext(code, context, {timeout: 1000});
  assert.equal(calls, 1);
  for (const values of logs) {
    assert.equal(values.length, 1);
    assert.match(values[0], /^\[JimmyAds\]\[[a-z0-9-]+\]\[AD-20261020\.5\] [a-z-]+$/);
  }
  if (logCapture) logCapture.push(...logs.map(values=>values[0]));
  return output;
}
const bili = 'https://app.bilibili.com/x/v2/';
const tieba = 'https://tiebac.baidu.com/c/f/ad/getSplashAd';
test('B站开屏：删除广告展示，保留账号和业务字段', () => {
  const out = execute('bilibili', bili+'splash/list?x=1', {code:0,data:{show:[{ad:true}],list:[1],other:'unchanged'}});
  assert.deepEqual(JSON.parse(out.body), {code:0,data:{list:[1],other:'unchanged'}});
});
test('B站推荐：仅删除明确广告，保留正常视频、游戏与非广告banner', () => {
  const normal = {card_type:'small_cover_v10',card_goto:'game',id:7};
  const out = execute('bilibili', bili+'feed/index?x=1', {code:0,data:{items:[normal,{card_type:'cm_v2',card_goto:'ad_av'},{card_type:'banner_v8',card_goto:'banner',banner_item:[{type:'ad'},{type:'video',id:9}]},null]}});
  const items=JSON.parse(out.body).data.items;
  assert.equal(items.length,3); assert.deepEqual(items[0],normal);
  assert.deepEqual(items[1].banner_item,[{type:'video',id:9}]); assert.equal(items[2],null);
});
test('登录失效、空内容、非JSON、未知数据、服务错误均原样放行', () => {
  for (const body of ['', '<html>error</html>', {code:-101,data:{show:[1]}}, {code:0,data:null}, {code:0,data:[]}, {message:'new schema'}]) {
    assert.deepEqual(execute('bilibili',bili+'splash/list',body),{});
  }
  assert.deepEqual(execute('bilibili',bili+'splash/list',{code:0,data:{show:[1]}},'GET',500),{});
});
test('域名和路径严格匹配：不触碰登录、支付、签到、正文或伪装域名', () => {
  for (const url of [bili+'splash/listFake',bili+'account/login',bili+'pay',bili+'sign','https://app.bilibili.com.evil.example/x/v2/splash/list']) {
    assert.deepEqual(execute('bilibili',url,{code:0,data:{show:[1]}}),{});
  }
  assert.deepEqual(execute('bilibili',bili+'splash/list',{code:0,data:{show:[1]}},'POST'),{});
});
test('贴吧：只处理成功的开屏响应，保留其他字段', () => {
  const out=execute('tieba',tieba,{error_code:0,data:{ad:[1]},other:5});
  assert.deepEqual(JSON.parse(out.body),{error_code:2230209,data:null,other:5});
  for(const body of ['broken',{error_code:3,data:{}},{unexpected:true}]) assert.deepEqual(execute('tieba',tieba,body),{});
});
test('重复执行：已经处理的内容不再修改业务内容', () => {
  const first=execute('bilibili',bili+'splash/show',{code:0,data:{show:[1],x:2}});
  assert.deepEqual(execute('bilibili',bili+'splash/show',first.body),{});
  const second=execute('tieba',tieba,{error_code:0,data:{ad:[1]}});
  assert.deepEqual(execute('tieba',tieba,second.body),{});
});
test('大响应跳过，避免无上限处理', () => {
  assert.deepEqual(execute('bilibili',bili+'splash/list','x'.repeat(2*1024*1024+1)),{});
  assert.deepEqual(execute('tieba',tieba,'x'.repeat(1024*1024+1)),{});
});
test('缺少运行对象时仍恰好完成一次', () => {
  for(const name of ['bilibili','tieba']) {
    let count=0;
    vm.runInNewContext(fs.readFileSync(path.join(root,'scripts/ads',name+'.js'),'utf8'),{$done:()=>count++},{timeout:1000});
    assert.equal(count,1);
  }
});

const xhs = 'https://edith.xiaohongshu.com/api/sns/v1/system_service/splash_config';
const tb = 'https://guide-acs.m.taobao.com/gw/mtop.taobao.wireless.home.splash.awesome.get/1.0/';
const wb = 'https://bootrealtime.uve.weibo.com/v1/ad/realtime';
function taobaoPayload() {
  return {api:'mtop.taobao.wireless.home.splash.awesome.get',ret:['SUCCESS::调用成功'],
    data:{coupons:{count:2},containers:{normal_home:{items:[{product:123}]},splash_home_base:{base:{sections:[
      {bizData:{'normal-content':{data:[{times:'3',imgUrl:'keep-product-image'}]}}},
      {bizData:{'taobao-splash':{data:[{times:'3',waitTime:'5',coldStart:'true',hotStart:'true',startTime:'1',endTime:'2',imgUrl:'example-ad',videoUrl:'example-ad-video',other:'keep'}]}}}
    ]}}}}};
}
test('小红书：只推迟明确的开屏广告窗口，保留普通配置', () => {
  const original={success:true,code:0,data:{normal:{watermark:true,download:false,account:'keep'},ads_groups:[{start_time:1,end_time:2,placement:'splash',ads:[{start_time:'1',end_time:'2',image:'keep-ad-metadata'}]}]}};
  const out=execute('xiaohongshu',xhs+'?x=1',original);
  const obj=JSON.parse(out.body);
  assert.equal(obj.data.ads_groups[0].start_time,3818332800);
  assert.equal(obj.data.ads_groups[0].ads[0].end_time,'3818419199');
  assert.deepEqual(obj.data.normal,original.data.normal);
  assert.equal(obj.data.ads_groups[0].placement,'splash');
  assert.equal(obj.data.ads_groups[0].ads[0].image,'keep-ad-metadata');
});
test('小红书：笔记、下载、登录、同名伪装域名不触碰', () => {
  const body={success:true,code:0,data:{ads_groups:[{start_time:1,end_time:2}]}};
  for(const url of [xhs+'Extra','https://edith.xiaohongshu.com/api/sns/v1/note/feed?x=1','https://edith.xiaohongshu.com/api/sns/v1/system_service/config?x=1','https://edith.xiaohongshu.com/api/sns/v1/login','https://edith.xiaohongshu.com.evil.example/api/sns/v1/system_service/splash_config']) {
    assert.deepEqual(execute('xiaohongshu',url,body),{});
  }
});
test('小红书：登录失败、未知时间格式与空广告原样放行', () => {
  for(const body of [{success:false,code:-1,data:{ads_groups:[{start_time:1}]}},{code:0,data:{ads_groups:[]}},{code:0,data:{ads_groups:[{start_time:{unexpected:true}}]}},'<html>error</html>']) {
    assert.deepEqual(execute('xiaohongshu',xhs,body),{});
  }
});
test('小红书：专用广告记录缺时间字段时补齐上游禁用窗口', () => {
  const body={code:0,data:{normal:{theme:'keep'},ads_groups:[{id:'group',ads:[{id:'ad',image:'keep'}]},{start_time:'1',ads:[]}]}};
  const out=execute('xiaohongshu',xhs,body);
  const obj=JSON.parse(out.body);
  assert.equal(obj.data.ads_groups[0].start_time,3818332800);
  assert.equal(obj.data.ads_groups[0].end_time,3818419199);
  assert.equal(obj.data.ads_groups[0].ads[0].start_time,3818332800);
  assert.equal(obj.data.ads_groups[0].ads[0].end_time,3818419199);
  assert.equal(obj.data.ads_groups[1].start_time,'3818332800');
  assert.equal(obj.data.ads_groups[1].end_time,3818419199);
  assert.deepEqual(obj.data.normal,body.data.normal);
  assert.equal(obj.data.ads_groups[0].ads[0].image,'keep');
  assert.deepEqual(execute('xiaohongshu',xhs,out.body),{});
});
test('淘宝：只改 taobao-splash 条目，保留MTOP结果和商品/优惠券', () => {
  const before=taobaoPayload();
  const obj=JSON.parse(execute('taobao',tb+'?x=1',before,'POST').body);
  const ad=obj.data.containers.splash_home_base.base.sections[1].bizData['taobao-splash'].data[0];
  assert.equal(ad.times,'0');assert.equal(ad.waitTime,'0');assert.equal(ad.coldStart,'false');
  assert.equal(ad.imgUrl,'');assert.equal(ad.videoUrl,'');assert.equal(ad.other,'keep');
  assert.deepEqual(obj.ret,before.ret);assert.equal(obj.api,before.api);
  assert.deepEqual(obj.data.coupons,before.data.coupons);
  assert.deepEqual(obj.data.containers.normal_home,before.data.containers.normal_home);
  assert.deepEqual(obj.data.containers.splash_home_base.base.sections[0],before.data.containers.splash_home_base.base.sections[0]);
});
test('淘宝：整包首页、普通视频、弹层、支付和领券均不匹配', () => {
  for(const api of ['mtop.taobao.wireless.home.newface.awesome.get','mtop.taobao.cloudvideo.video.query','mtop.taobao.trade.order.create','mtop.taobao.coupon.get','mtop.tmall.home.get']) {
    assert.deepEqual(execute('taobao','https://guide-acs.m.taobao.com/gw/'+api+'/1.0/?x=1',taobaoPayload()),{});
  }
  for(const url of [tb.replace('guide-acs.m.taobao.com','guide-acs.m.taobao.com.evil.example'),tb.replace('.get/1.0/','.get_extra/1.0/'),'https://poplayer.template.alibaba.com/promotion.json']) {
    assert.deepEqual(execute('taobao',url,taobaoPayload()),{});
  }
});
test('淘宝：补齐明确开屏条目控制字段，兼容数字/布尔值且不动普通商品', () => {
  const before=taobaoPayload();
  const ads=before.data.containers.splash_home_base.base.sections[1].bizData['taobao-splash'];
  ads.data=[{imgUrl:'ad-image',times:3,waitTime:5,coldStart:true,hotStart:true,other:'keep'},null,{}];
  const out=execute('taobao',tb,before);
  const obj=JSON.parse(out.body);
  const ad=obj.data.containers.splash_home_base.base.sections[1].bizData['taobao-splash'].data[0];
  assert.equal(ad.times,0);assert.equal(ad.waitTime,0);
  assert.equal(ad.coldStart,false);assert.equal(ad.hotStart,false);
  assert.equal(ad.startTime,'3818332800000');assert.equal(ad.endTime,'3818419199000');
  assert.equal(ad.imgUrl,'');assert.equal(ad.other,'keep');
  assert.deepEqual(obj.data.containers.splash_home_base.base.sections[0],before.data.containers.splash_home_base.base.sections[0]);
  assert.deepEqual(obj.data.coupons,before.data.coupons);
  assert.deepEqual(execute('taobao',tb,out.body),{});
});
test('淘宝：过期、失败、混合失败、JSONP和未知结构不改', () => {
  for(const ret of [['FAIL_SYS_SESSION_EXPIRED::session expired'],['SUCCESS::ok','FAIL_SYS::failed'],[]]) {
    const body=taobaoPayload();body.ret=ret;
    assert.deepEqual(execute('taobao',tb,body),{});
  }
  for(const body of ['callback({"data":{}})',{data:{}},null]) assert.deepEqual(execute('taobao',tb,body),{});
  const mismatch=taobaoPayload();mismatch.api='mtop.taobao.other.get';
  assert.deepEqual(execute('taobao',tb,mismatch),{});
});
test('微博：旧请求JS不再参与开屏，原生重写独立处理；脚本只改明确广告项', () => {
  assert.deepEqual(execute('weibo',wb,{ads:[1]}),{});
  const u='https://api.weibo.cn/2/statuses/container_timeline_topicpage?x=1';
  const keep={data:{mblogtypename:'normal',id:7}};
  const out=execute('weibo',u,{items:[{data:{mblogtypename:'广告'}},keep]});
  assert.deepEqual(JSON.parse(out.body),{items:[keep]});
  for(const path of ['messageflow','account/login','statuses/friends_timeline','checkin/show']) assert.deepEqual(execute('weibo','https://api.weibo.cn/2/'+path,{items:[{data:{is_ad:1}}]}),{});
});
test('新增三模块：处理幂等，不在每次重载继续改变数据', () => {
  const cases=[['xiaohongshu',xhs,{code:0,data:{ads_groups:[{start_time:1,end_time:2}]}}],['taobao',tb,taobaoPayload()],['weibo','https://api.weibo.cn/2/searchall',{items:[{data:{is_ad:1}}]}]];
  for(const [name,url,body] of cases) {
    const out=execute(name,url,body);assert.equal(typeof out.body,'string');
    assert.deepEqual(execute(name,url,out.body),{});
  }
});
test('新增三模块：非成功HTTP、非GET/POST与缺失环境安全结束', () => {
  for(const [name,url,body] of [['xiaohongshu',xhs,{code:0,data:{ads_groups:[{start_time:1}]}}],['taobao',tb,taobaoPayload()],['weibo','https://api.weibo.cn/2/searchall',{items:[{data:{is_ad:1}}]}]]) {
    assert.deepEqual(execute(name,url,body,'GET',503),{});
    if(name!=='weibo') assert.deepEqual(execute(name,url,'x'.repeat(2*1024*1024+1)),{});
    assert.deepEqual(execute(name,url,body,'HEAD'),{});
    let count=0;
    vm.runInNewContext(fs.readFileSync(path.join(root,'scripts/ads',name+'.js'),'utf8'),{$done:()=>count++},{timeout:1000});
    assert.equal(count,1);
  }
});
test('淘宝/小红书诊断：固定状态区分处理、空广告、未知结构、非JSON及HTTP错误', () => {
  const cases=[
    ['taobao',tb,taobaoPayload(),{data:{containers:{splash_home_base:{base:{sections:[]}}}}}],
    ['xiaohongshu',xhs,{code:0,data:{ads_groups:[{id:'ad'}]}},{code:0,data:{ads_groups:[]}}]
  ];
  for(const [name,url,body,empty] of cases) {
    const logs=[];
    const out=execute(name,url+'?token=EXAMPLE_NOT_A_SECRET',{...body,private:'TEST_BODY_NEVER_LOG'},'GET','200',logs);
    assert.deepEqual(logs,[`[JimmyAds][${name}][AD-20261020.5] changed`]);
    logs.length=0;
    assert.deepEqual(execute(name,url,out.body,'GET',200,logs),{});
    assert.deepEqual(logs,[`[JimmyAds][${name}][AD-20261020.5] unchanged`]);
    for(const [payload,status,expected] of [[empty,200,'unchanged'],[{unknown:'TEST_SCHEMA_NEVER_LOG'},200,'unsupported-schema'],['TEST_PARSE_EXCEPTION_NEVER_LOG',200,'non-json'],[body,503,'http-error']]) {
      logs.length=0;
      assert.deepEqual(execute(name,url,payload,'GET',status,logs),{});
      assert.deepEqual(logs,[`[JimmyAds][${name}][AD-20261020.5] ${expected}`]);
    }
  }
});
test('三模块诊断：未知路径不记录，URL/请求头/响应头/响应体内容不出现在日志', () => {
  for(const [name,url,body] of [['taobao',tb,taobaoPayload()],['xiaohongshu',xhs,{code:0,data:{ads_groups:[{id:'TEST_BODY_NEVER_LOG'}]}}],['weibo','https://api.weibo.cn/2/searchall','TEST_BODY_NEVER_LOG']]) {
    const logs=[];
    execute(name,url+'?token=EXAMPLE_NOT_A_SECRET',{...body,account:'TEST_ACCOUNT_NEVER_LOG'},'GET',200,logs);
    assert.equal(logs.length,1);
    assert.doesNotMatch(logs.join('\n'),/TEST_|EXAMPLE_NOT_A_SECRET|https:|Cookie|token|account/);
    logs.length=0;
    execute(name,'https://unrelated.example/login?token=EXAMPLE_NOT_A_SECRET',body,'GET',200,logs);
    assert.deepEqual(logs,[`[JimmyAds][${name}][AD-20261020.5] url-unmatched`]);
  }
});
test('三模块诊断：日志设施异常不影响完成一次，也不猜测完整HTTP状态行', () => {
  for(const [name,url,body] of [['taobao',tb,taobaoPayload()],['xiaohongshu',xhs,{code:0,data:{ads_groups:[{id:'ad'}]}}],['weibo','https://api.weibo.cn/2/searchall',{items:[{data:{is_ad:1}}]}]]) {
    const logs=[];
    assert.deepEqual(execute(name,url,body,'GET','HTTP/1.1 200 OK',logs),{});
    assert.deepEqual(logs,[`[JimmyAds][${name}][AD-20261020.5] http-error`]);
    for(const logger of [undefined,{log:()=>{throw new Error('TEST_LOG_EXCEPTION_NEVER_LOG');}}]) {
      let calls=0,output;
      vm.runInNewContext(fs.readFileSync(path.join(root,'scripts/ads',name+'.js'),'utf8'),{
        $request:{url,method:'GET'},$response:{status:200,body:typeof body==='string'?body:JSON.stringify(body)},
        console:logger,$done:value=>{calls++;output=value;}
      },{timeout:1000});
      assert.equal(calls,1);assert.equal(typeof output.body,'string');
    }
  }
});

const added = [
  {name:'alipan', url:'https://member.alipan.com/v1/users/onboard_list?x=1',
   body:{result:[{anchor:'home_top_banner'},{anchor:'resource_top_banner'},{anchor:'mainBackup'},{anchor:'signIn'},{anchor:'home_bulletin_board'},{anchor:'backup_list_under_mydevice_banner'},null],normal:{backup:true}},
   verify:o=>{assert.deepEqual(o.result.map(x=>x&&x.anchor),['mainBackup','signIn','home_bulletin_board','backup_list_under_mydevice_banner',null]);assert.deepEqual(o.normal,{backup:true});},
   business:['https://member.alipan.com/v2/activity/sign_in_luckyBottle','https://api.alipan.com/apps/v2/users/home/widgets']},
  {name:'cainiao', url:'https://cn-acs.m.cainiao.com/gw/mtop.cainiao.guoguo.nbnetflow.ads.show.cn/1.0/?x=1',
   body:{ret:['SUCCESS::ok'],data:{result:[{id:'ad',materialContentMapper:{adItemDetail:{id:1}}},{id:'29339',materialContentMapper:{group_id:'interests',coupon:'keep'}},{id:'logistics'},null],points:50}},
   verify:o=>{assert.deepEqual(o.data.result.map(x=>x&&x.id),['29339','logistics',null]);assert.equal(o.data.points,50);assert.equal(o.data.result[0].materialContentMapper.coupon,'keep');},
   business:['https://cn-acs.m.cainiao.com/gw/mtop.nbfriend.message.conversation.list.cn/1.0/','https://cn-acs.m.cainiao.com/gw/mtop.cainiao.guoguo.nbnetflow.ads.mshow.cn/1.0/']},
  {name:'jingdong', url:'https://api.m.jd.com/client.action?client=ios&functionId=start&x=1',
   body:{code:'0',images:[[{showTimes:4,time:'5',product:'keep',onlineTime:'keep'},{normal:'keep'}]],showTimesDaily:3,orders:[1],coupons:[2],countdown:100},
   verify:o=>{assert.equal(o.images[0][0].showTimes,0);assert.equal(o.images[0][0].time,'0');assert.equal(o.images[0][0].onlineTime,'keep');assert.deepEqual(o.images[0][1],{normal:'keep'});assert.deepEqual(o.orders,[1]);assert.deepEqual(o.coupons,[2]);assert.equal(o.countdown,100);},
   business:['https://api.m.jd.com/client.action?functionId=myOrderInfo','https://api.m.jd.com/client.action?functionId=startExtra','https://api.m.jd.com/client.action?functionId=start&functionId=order']},
  {name:'meituan', url:'https://wmapi.meituan.com/api/v7/loadInfo?x=1',
   body:{code:0,data:{startpicture:{ad:[1],mk:[2],normal:'keep'},coupons:[3],location:'keep'}},
   verify:o=>{assert.deepEqual(o.data.startpicture,{ad:[],mk:[],normal:'keep'});assert.deepEqual(o.data.coupons,[3]);assert.equal(o.data.location,'keep');},
   business:['https://wmapi.meituan.com/api/v7/coupon/list','https://wmapi.meituan.com/api/v7/loadInfoExtra']},
  {name:'luckin', url:'https://capi.lkcoffee.com/resource/m/sys/app/adposNew?x=1',
   body:{status:'SUCCESS',data:{ads:[1]}},verify:o=>assert.deepEqual(o,{status:'SUCCESS'}),
   business:['https://capi.lkcoffee.com/resource/m/eorder/product/popAppTagProductList','https://m.lkcoffee.com/ecapi/resource/m/member/exchange/page']},
  {name:'wechat-articles', url:'https://mp.weixin.qq.com/mp/getappmsgad?x=1',
   body:{base_resp:{ret:0},advertisement_num:1,advertisement_info:[1],appid:'TEST_PUBLIC_APPID',article:{content:'keep'}},
   verify:o=>{assert.equal(o.advertisement_num,0);assert.deepEqual(o.advertisement_info,[]);assert.equal(o.appid,'TEST_PUBLIC_APPID');assert.deepEqual(o.article,{content:'keep'});},
   business:['https://mp.weixin.qq.com/s/article','https://mp.weixin.qq.com/mp/cps_product_info?action=1','https://weixin.qq.com/chat']}
];
for (const item of added) {
  test(item.name+'：限定广告处理，保留已知正常字段',()=>{
    const out=execute(item.name,item.url,item.body);
    assert.equal(typeof out.body,'string');item.verify(JSON.parse(out.body));
  });
  test(item.name+'：业务URL与伪装域名原样放行',()=>{
    const host=new URL(item.url).host;
    for(const url of [...item.business,item.url.replace(host,host+'.evil.example')]) {
      assert.deepEqual(execute(item.name,url,item.body),{});
    }
  });
  test(item.name+'：服务错误、异常、登录失败、超限与未知结构不修改',()=>{
    for(const body of ['',null,[],'<html>error</html>',{unknown:true},{...item.body,error:'expired'},{...item.body,success:false}]) {
      assert.deepEqual(execute(item.name,item.url,body),{});
    }
    assert.deepEqual(execute(item.name,item.url,item.body,'GET',503),{});
    assert.deepEqual(execute(item.name,item.url,item.body,'DELETE'),{});
    assert.deepEqual(execute(item.name,item.url,'x'.repeat(2*1024*1024+1)),{});
  });
  test(item.name+'：幂等、缺失环境恰好结束一次',()=>{
    const once=execute(item.name,item.url,item.body);
    assert.deepEqual(execute(item.name,item.url,once.body),{});
    let calls=0;
    vm.runInNewContext(fs.readFileSync(path.join(root,'scripts/ads',item.name+'.js'),'utf8'),{$done:()=>calls++},{timeout:1000});
    assert.equal(calls,1);
  });
}
test('新增响应：保留平台原生失败状态和未知schema',()=>{
  assert.deepEqual(execute('cainiao',added[1].url,{...added[1].body,ret:['FAIL_SYS_SESSION_EXPIRED::expired']}),{});
  assert.deepEqual(execute('jingdong',added[2].url,{...added[2].body,code:'3'}),{});
  assert.deepEqual(execute('jingdong',added[2].url,{...added[2].body,images:{unknown:1}}),{});
  assert.deepEqual(execute('meituan',added[3].url,{code:0,data:{startpicture:{ad:{newSchema:1},other:'keep'}}}),{});
  assert.deepEqual(execute('luckin',added[4].url,{status:'FAIL',message:'expired'}),{});
  assert.deepEqual(execute('wechat-articles',added[5].url,{...added[5].body,base_resp:{ret:-1}}),{});
});
