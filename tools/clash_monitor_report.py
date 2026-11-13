"""Offline, local-only report for passive Clash usage. No remote assets or uploads."""
import csv
from datetime import datetime, timedelta, timezone
import html
import hashlib
import json
from pathlib import Path
import sqlite3

TZ=timezone(timedelta(hours=8))

def render(folder):
    folder=Path(folder);session=json.loads((folder/'session.json').read_text(encoding='utf-8'))
    db=sqlite3.connect(folder/'monitor.sqlite');db.row_factory=sqlite3.Row
    minutes=[dict(r) for r in db.execute('SELECT * FROM minutes ORDER BY minute')]
    coverage=[dict(r) for r in db.execute('SELECT * FROM coverage ORDER BY minute')]
    health=[dict(r) for r in db.execute('SELECT * FROM health ORDER BY at')]
    events=[{'at':r['at'],'kind':r['kind'],**json.loads(r['payload'])}
            for r in db.execute("SELECT * FROM events WHERE kind != 'dial_error' ORDER BY at")]
    db.close()
    contexts={}
    context_events=[]
    for e in events:
        if e['kind']=='context':
            meta={k:v for k,v in e.items() if k not in ('at','kind','epoch','context')}
            e['context']=e.get('context') or hashlib.sha256(json.dumps([meta,e['epoch']],sort_keys=True).encode()).hexdigest()[:20]
            context_events.append(e)
    next_context=0
    for r in health:
        while next_context<len(context_events) and context_events[next_context]['at']<=r['at']:
            event=context_events[next_context]
            contexts[event['epoch']]=event['context']
            next_context+=1
        r['context']=contexts.get(r['epoch'],'unknown')
    for rows,field in [(minutes,'minute'),(coverage,'minute'),(health,'at')]:
        for r in rows:
            d=datetime.fromtimestamp(r[field],TZ);r['date']=d.strftime('%Y-%m-%d');r['hour']=d.hour
    switches=[r for r in events if r['kind'] in ('node_switch','route_change')]
    for name,rows in [('minutes.csv',minutes),('health.csv',health),('switches.csv',switches)]:
        keys=list(dict.fromkeys(k for r in rows for k in r))
        with (folder/name).open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader()
            for row in rows:
                safe={k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()}
                safe={k:"'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v for k,v in safe.items()}
                writer.writerow(safe)
    data=json.dumps({'minutes':minutes,'coverage':coverage,'health':health,'events':events},ensure_ascii=False).replace('<','\\u003c')
    lifecycle=[e for e in events if e['kind'] in ('recorder_start','recorder_stop')]
    start_at=next((e['at'] for e in lifecycle if e['kind']=='recorder_start'),session['start'])
    stopped=bool(lifecycle and lifecycle[-1]['kind']=='recorder_stop')
    end_at=lifecycle[-1]['at'] if stopped else session['end']
    started=datetime.fromtimestamp(start_at,TZ).strftime('%m月%d日 %H:%M')
    until=('采集已停止于 ' if stopped else '计划截止 ')+datetime.fromtimestamp(end_at,TZ).strftime('%m月%d日 %H:%M')
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'">
<title>Clash 实际使用观察</title><style>
body{font:15px/1.65 system-ui,sans-serif;background:#f4f6fa;color:#1e293b;margin:0;padding:24px;max-width:1500px;margin:auto}h1{margin-bottom:4px}p{max-width:1050px}.card{background:white;border:1px solid #dce2eb;border-radius:12px;padding:20px;margin:18px 0;overflow:auto}.muted{color:#64748b}select{padding:7px 12px;margin:0 15px 8px 3px}table{border-collapse:collapse;width:100%;white-space:nowrap}td,th{text-align:left;padding:9px;border-bottom:1px solid #e5e7eb}th{font-weight:600;color:#475569}.bar{height:8px;background:#4396db;border-radius:3px}.warn{color:#b45309}code{background:#eff3f8;padding:2px 5px}a{color:#1266ab}
</style><h1>Clash 实际使用观察</h1>
<p class="muted">北京时间 UTC+8 · START 起 · END · 被动记录，运行时每5秒采样，每5分钟更新报告</p>
<p>关注实际经过的节点及 AI 组。204探测延迟来自内核已有检查，<b>不是 AI 回答耗时、下载带宽或完整请求成功率</b>。流量只是采样窗口内观察到的数据；连接在两次采样间结束时会漏记最后一段流量。长连接可在切换后继续经过旧节点。</p>
<div class="card"><label>范围 <select id="scope"><option>AI</option><option>其他代理</option><option>全部</option></select></label><label>节点 <select id="node"></select></label><label>日期 <select id="date"></select></label><label>网络/配置上下文 <select id="context"></select></label><p id="summary"></p><div id="hours"></div></div>
<div class="card"><h2>当前选择与记录覆盖</h2><div id="state"></div><p class="muted">无样本的小时不代表正常；睡眠、关机、采集器或内核不可用期间均可能缺测。日志覆盖按订阅流在线状态估算，不能证明日志零丢失。不同日期、节点和网络上下文不要直接混成高低峰结论。</p></div>
<div class="card"><h2>节点切换与触发线索</h2><p>“已观测”表示确认了成员或选择变化；“推断/相关”不等于内核已确认的切换原因。每次切换约有5秒采样时间误差。同一自动池变化可能映射到多个业务组，多行不等于多次独立切换。</p><div id="switches"></div></div>
<div class="card"><h2>体验标记与缺测事件</h2><div id="markers"></div></div>
<p class="muted">数据只保存在本机。完整导出：<a href="minutes.csv">分钟数据</a> · <a href="health.csv">探测样本</a> · <a href="switches.csv">切换事件</a>。本页无外部资源、遥测或网络请求。数据结束后重新运行 report 命令可刷新。</p>
<script>const D=DATA;
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=x=>new Date(x*1000).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',hour12:false});
const q=(a,p)=>{if(!a.length)return null;const b=[...a].sort((x,y)=>x-y);return b[Math.ceil(p*b.length)-1]};
const table=(heads,rows)=>'<table><thead><tr>'+heads.map(x=>'<th>'+esc(x)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(c=>'<td>'+c+'</td>').join('')+'</tr>').join('')+'</tbody></table>';
const opts=(id,a)=>document.getElementById(id).innerHTML=['全部',...a].map(x=>'<option>'+esc(x)+'</option>').join('');
opts('node',[...new Set(D.minutes.map(r=>r.node))].sort());opts('date',[...new Set(D.coverage.map(r=>r.date))].sort());
document.getElementById('context').innerHTML='<option value="全部">全部</option>'+D.events.filter(r=>r.kind==='context').map(r=>'<option value="'+esc(r.context)+'">'+esc(r.profile+' · '+(r.network?.types||[]).join('/')+' · '+r.epoch.slice(0,6))+'</option>').join('');
function draw(){let s=document.getElementById('scope').value,n=document.getElementById('node').value,d=document.getElementById('date').value,x=document.getElementById('context').value;
let filter=r=>(s==='全部'||r.scope===s)&&(n==='全部'||r.node===n)&&(d==='全部'||r.date===d)&&(x==='全部'||r.context===x),M=D.minutes.filter(filter),H=D.health.filter(filter),C=D.coverage.filter(r=>d==='全部'||r.date===d);
if(s==='全部')H=[...new Map(H.map(r=>[[r.epoch,r.node,r.probe_at].join('|'),r])).values()];
let rows=[],rank=[];for(let h=0;h<24;h++){let m=M.filter(r=>r.hour===h),p=H.filter(r=>r.hour===h),c=C.filter(r=>r.hour===h),delays=p.filter(r=>r.alive&&r.delay>0).map(r=>r.delay),med=q(delays,.5),p95=q(delays,.95),sum=k=>m.reduce((v,r)=>v+(r[k]||0),0),cov=c.reduce((v,r)=>v+r.api_s,0);
if(!m.length&&!p.length&&!c.length)continue;if(delays.length>=6)rank.push({h,p95,n:delays.length,days:new Set(p.map(r=>r.date)).size});
rows.push([h.toString().padStart(2,'0')+':00–'+((h+1)%24).toString().padStart(2,'0')+':00',cov?(cov/60).toFixed(1)+'分钟':'缺测',(sum('active_s')/60).toFixed(1),(sum('selected_s')/60).toFixed(1),sum('opens'),sum('errors'),p.length,p.filter(r=>!r.alive||!r.delay).length,med===null?'—':Math.round(med)+'ms',p95===null?'—':Math.round(p95)+'ms<div class="bar" style="width:'+Math.min(150,p95/5)+'px"></div>',(sum('down')/1e6).toFixed(1)]);}
document.getElementById('hours').innerHTML=rows.length?table(['小时','该日期全局采集覆盖','节点活跃分钟*','AI选中分钟','建连记录','建连错误†','探测样本','探测失败','延迟P50','延迟P95','观察下行MB'],rows):'<p>尚无匹配数据，等待实际使用及下一次内置探测。</p>';
rank.sort((a,b)=>a.p95-b.p95);let conclusion='尚无足够探测样本比较时段。';if(rank.length>=2){let a=rank[0],b=rank[rank.length-1];conclusion='当前样本中较低探测延迟时段 '+a.h+':00（P95 '+Math.round(a.p95)+'ms，'+a.n+'样本），较高时段 '+b.h+':00（P95 '+Math.round(b.p95)+'ms，'+b.n+'样本）。仅描述已有样本，至少多天同节点对照后再判断固定高低峰。';}
document.getElementById('summary').textContent=conclusion+' *同一节点有连接时按窗口累计，多节点可重叠。†错误按日志时附近选择归因，可能与实际失败节点不同；不是完整AI请求失败率。';
}
for(let id of ['scope','node','date','context'])document.getElementById(id).onchange=draw;draw();
const contexts=D.events.filter(r=>r.kind==='context'),base=D.events.filter(r=>r.kind==='selection_baseline'),last=contexts.at(-1);
document.getElementById('state').innerHTML='<p>'+ (last?'最近上下文 '+esc(fmt(last.at))+' · 配置 '+esc(last.profile)+' · 模式 '+esc(last.mode)+' · '+esc((last.network?.types||[]).join('/')):'等待内核')+'</p><p>记录覆盖 '+(D.coverage.reduce((v,r)=>v+r.api_s,0)/3600).toFixed(2)+' 小时；日志流覆盖估计 '+(D.coverage.reduce((v,r)=>v+r.log_s,0)/3600).toFixed(2)+' 小时。</p>'+table(['上下文变更时间','配置','模式','接入类型','上下文编号'],contexts.slice(-30).map(r=>[esc(fmt(r.at)),esc(r.profile),esc(r.mode),esc((r.network?.types||[]).join('/')),esc(r.epoch)]));
const probe=h=>!h||(!h.probe_at&&h.delay_ms==null)?'未记录':esc(h.alive===false?'探测失败':h.delay_ms==null?'无延迟值':h.delay_ms+'ms')+'<br><small>'+esc(h.probe_at||'探测时间未记录')+'</small>';
let sw=D.events.filter(r=>['node_switch','route_change'].includes(r.kind));document.getElementById('switches').innerHTML=sw.length?table(['首次观察切换','组','原路径','新路径','原节点最近探测','新节点最近探测','证据等级','原因','状态补证'],sw.slice(-300).reverse().map(r=>[esc(fmt(r.at)),esc(r.group),esc(r.old_path.join(' → ')),esc(r.new_path.join(' → ')),probe(r.old_health||r.state_evidence?.old_health_after),probe(r.new_health||r.state_evidence?.new_health_after),esc(r.certainty),esc(r.detail),r.state_evidence?'<details><summary>池内位置/固定状态</summary><pre>'+esc(JSON.stringify(r.state_evidence,null,2))+'</pre></details>':'旧样本未保存'])):'<p>尚未观察到切换。初始选择：'+base.slice(-8).map(r=>esc(r.group+': '+r.path.join(' → '))).join('<br>')+'</p>';
let markers=D.events.filter(r=>['user_experience','coverage_gap','core_unavailable','core_available_again','log_queue_overflow','storage_limit','recorder_start','recorder_stop'].includes(r.kind));document.getElementById('markers').innerHTML=table(['时间','事件','信息'],markers.slice(-100).reverse().map(r=>[esc(fmt(r.at)),esc(r.kind),esc(r.experience||r.reason||r.error_type||r.deadline||'')]));
</script></html>'''
    page=page.replace('START',started).replace('END',until).replace('DATA',data)
    tmp=folder/'report.html.tmp';tmp.write_text(page,encoding='utf-8');tmp.replace(folder/'report.html')
