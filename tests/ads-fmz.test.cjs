'use strict';
// Synthetic fixtures reconstructed from fmz200's pinned branches, NOT captures.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
function run(id,url,body) {
  const calls=[],logs=[];
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../scripts/ads',id+'.js'),'utf8'),{
    $argument:'diagnostic=1',$request:{url,method:'GET'},
    $response:{status:200,body:JSON.stringify(body)},$done:v=>calls.push(v),
    console:{log:v=>logs.push(v)}
  },{timeout:1000});
  assert.equal(calls.length,1);
  assert.doesNotMatch(logs.join('\n'),/https?:|EXAMPLE_NOT_A_SECRET|private-user/);
  return {body:calls[0].body ? JSON.parse(calls[0].body) : body,changed:!!calls[0].body};
}
test('XHS sponsored v6 feed on three upstream hosts, HTTP and HTTPS; normal shopping/media intact',()=>{
  const keep=[{model_type:'live_v2'},{card_icon:'shop',media_save_config:{disable_save:true}},{ads_info:{}},null];
  for(const host of ['edith','rec','www']) for(const scheme of ['http','https']) {
    const out=run('xiaohongshu',`${scheme}://${host}.xiaohongshu.com/api/sns/v6/homefeed?token=EXAMPLE_NOT_A_SECRET`,{code:0,data:[{ads_info:{id:'ad'}},...keep]});
    assert.deepEqual(out.body.data,keep);assert.ok(out.changed);
  }
});
test('XHS does not interpret arbitrary followfeed versions, spoofed hosts or normal note feeds',()=>{
  const body={code:0,data:[{ads_info:{id:1}}]};
  for(const url of ['https://rec.xiaohongshu.com/api/sns/v7/homefeed','https://rec.xiaohongshu.com/api/sns/v4/followfeed','https://rec.xiaohongshu.com.evil.invalid/api/sns/v6/homefeed','https://www.xiaohongshu.com/api/sns/v2/note/feed'])
    assert.equal(run('xiaohongshu',url,body).changed,false);
});
test('Weibo hotsearch page strips populated promotion only; other cards and empty flags retained',()=>{
  const keep=[{title:'normal'},{promotion:null},{promotion:{}},{promotion:false},null];
  const body={cards:[{card_group:[{promotion:{ad:1}},...keep]},{card_group:[{promotion:{unrelated:1}}]}],user:'private-user'};
  for(const host of ['api.weibo.cn','mapi.weibo.cn','api.weibo.com','mapi.weibo.com']) {
    const u=`https://${host}/2/page?token=EXAMPLE_NOT_A_SECRET`;
    const out=run('weibo',u,body);
    assert.deepEqual(out.body.cards[0].card_group,keep);
    assert.deepEqual(out.body.cards[1],body.cards[1]);assert.equal(out.body.user,body.user);
    assert.equal(run('weibo',u,out.body).changed,false);
  }
});
test('Weibo flowpage keeps header and region content, removes explicit commercial marker only',()=>{
  const keep=[{data:{itemid:'region_data'}},{data:{itemid:'c_type:510'}},{data:{itemid:'ordinary'}},null];
  const body={pageHeader:{image:'normal'},items:[{items:[{data:{promotion:{ad:1}}},{data:{itemid:'c_type:51'}},...keep]}]};
  const out=run('weibo','http://mapi.weibo.com/2/flowpage',body);
  assert.deepEqual(out.body.items[0].items,keep);assert.deepEqual(out.body.pageHeader,body.pageHeader);
});
test('Weibo comments only remove explicit ad rows; trend, mentions and ordinary replies retained',()=>{
  let out=run('weibo','https://api.weibo.cn/2/comments/mix_comments',{datas:[{adType:'广告'},{adType:'普通',text:'reply'},null]});
  assert.deepEqual(out.body.datas,[{adType:'普通',text:'reply'},null]);
  for(const p of ['comment','mix']) {
    const keep=[{type:'trend'},{commentAdType:0},{commentAdType:false},{commentAdType:{}},{text:'reply'},null];
    out=run('weibo',`https://api.weibo.cn/2/statuses/container_detail_${p}`,{items:[{commentAdType:'ad'},...keep]});
    assert.deepEqual(out.body.items,keep);
  }
});
test('New Weibo branches fail open on error, unknown or missing structures and near paths',()=>{
  for(const endpoint of ['page','flowpage','comments/mix_comments','statuses/container_detail_mix']) {
    for(const body of [{},{error:'failure',items:[],datas:[]},{cards:{},items:{},datas:{}},{code:403,items:[{commentAdType:1}]}])
      assert.equal(run('weibo',`https://api.weibo.cn/2/${endpoint}`,body).changed,false);
    assert.equal(run('weibo',`https://api.weibo.cn/2/${endpoint}Extra`,{cards:[{card_group:[{promotion:{ad:1}}]}],items:[{commentAdType:1}],datas:[{adType:'广告'}]}).changed,false);
  }
});
test('Taobao original splash transform now handles HTTP without touching generic videos',()=>{
  const body={data:{containers:{splash_home_base:{base:{sections:[{bizData:{'taobao-splash':{data:[{times:'3'}]}}}]}}}}};
  assert.equal(run('taobao','http://guide-acs.m.taobao.com/gw/mtop.taobao.wireless.home.splash.awesome.get/1.0/',body).changed,true);
  assert.equal(run('taobao','https://guide-acs.m.taobao.com/gw/mtop.taobao.cloudvideo.video.query/1.0/',body).changed,false);
});
