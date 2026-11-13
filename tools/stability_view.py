"""Read-only local viewer and a final HTML report generated from the same database."""
import html
import json
import math
import statistics
import time
from collections import Counter
from datetime import datetime,timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from stability_core import PRIVATE,TARGETS
from stability_stats import BJ,BUCKET,ELIGIBLE,WEIGHTS,connect,exposure,master,period,quantile,ranking,run_config
from stability_chatgpt import LABELS


def stamp(t):
    return datetime.fromtimestamp(t,BJ).strftime('%m-%d %H:%M:%S') if t else '—'


def textcell(x):
    return html.escape(str(x))


def table(headers, rows):
    return '<table><thead><tr>'+''.join('<th>'+textcell(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join(
        '<tr>'+''.join('<td>'+textcell(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table>'


def fmt(x):
    return '—' if x is None else f'{100*x:.1f}%'


def rank_table(rows):
    return table(['节点','身份','Provider','版本','评分','归因有效样本','节点归因成功率','请求覆盖估计','归因有效覆盖','实际 Hz','忙 / 容量跳过','证据'],
        [(r['name'],r['id'],r['provider'],'当前' if r['active'] else '已退出',r['score'],r['n'],fmt(r['success']),fmt(r['request_coverage']),fmt(r['window_coverage']),r['hz'],
          f"{r['busy']} / {r['capacity']}",'达标' if r['eligible'] else '证据不足或未达标') for r in rows])


def planned_counts(db,r):
    """Integrate the plans over wall time including outages. Transition phase contributes <=1 slot/edge."""
    from collections import defaultdict
    end=min(time.time(),r['end'])
    changes=[]
    for at,kind,data in db.execute("""select at,kind,data from st_event where run=? and
            kind in ('CANDIDATES','RATE_CHANGED','SYSTEM_SUSPENDED') order by at,rowid""",(r['id'],)):
        changes.append((at,kind,json.loads(data)))
    counts=defaultdict(lambda:defaultdict(float))
    for node,a,b in db.execute('select node,start,end from st_active where run=?',(r['id'],)):
        stop=min(b or end,end)
        rates=(5,1)
        fast=False
        for at,kind,data in changes+[(stop,'END',{})]:
            while a<min(at,stop):
                edge=min(at,stop,(int(a)//3600+1)*3600)
                counts[node][period(a)]+=(edge-a)/rates[int(fast)]
                a=edge
            if a>=stop:
                break
            if kind=='RATE_CHANGED':
                rates=data['rates']
            elif kind=='CANDIDATES':
                fast=node in data['current']
            elif kind=='SYSTEM_SUSPENDED' and 'resumed' in data:
                rates=(5,1)
                fast=False
    return counts


def cycle_key(at):
    local=datetime.fromtimestamp(at,BJ)
    day=local.date()-timedelta(days=int(local.hour<2))
    return day.isoformat(),period(at)


def daily_gaps(db,r):
    # Only the closed-window report scans minute aggregates for every date and node.
    from collections import defaultdict
    durations=defaultdict(float)
    a=r['start']
    while a<r['end']:
        b=min(r['end'],(int(a)//3600+1)*3600)
        durations[cycle_key(a)]+=b-a
        a=b
    measured=defaultdict(float)
    for node,m,sec in db.execute('select node,m,sum(validsec) from st_min where run=? group by node,m',(r['id'],)):
        measured[node,cycle_key(m*60)]+=sec
    active=db.execute('''select a.node,n.name from st_active a join st_node n on n.id=a.node where a.run=?
                 and a.end is null and a.node not in (select node from st_excluded)''',(r['id'],))
    return [(n,name,day,band,seconds,min(1,measured[n,(day,band)]/seconds)) for n,name in active
            for (day,band),seconds in durations.items() if measured[n,(day,band)]<.75*seconds]


def rankings(db,r):
    result={s:ranking(db,r,s) for s in ('全部','白天','晚间','凌晨')}
    active={n[0] for n in db.execute('select node from st_active where run=? and end is null',(r['id'],))}
    providers={n[0]:n[1] for n in db.execute('select id,provider from st_node')}
    counts=planned_counts(db,r)
    for s,rows in result.items():
        for x in rows:
            x['active']=x['id'] in active
            x['provider']=providers[x['id']]
            x['eligible']=x['eligible'] and x['active']
            expected=sum(counts[x['id']].values()) if s=='全部' else counts[x['id']][s]
            x['expected']=round(expected)
            x['request_coverage']=min(1,x['actual']/max(1,expected))
            x['missed_estimate']=max(0,round(expected)-x['actual'])
    if r['phase']=='formal' and time.time()>=r['end']:
        by_band=[{x['id'] for x in result[s] if x['eligible']} for s in ('白天','晚间','凌晨')]
        for x in result['全部']:
            x['eligible'] = x['eligible'] and all(x['id'] in ids for ids in by_band)
        result['全部'].sort(key=lambda x:(x['eligible'],x['score']),reverse=True)
    return result


def node_details(db,run,node):
    series=[]
    rows=db.execute('''select m,hist,valid,ok,t from st_min where run=? and node=? order by m,t''',(run,node))
    # Downsample to ten-minute bins; each target retains its own latency distribution.
    bins={}
    for m,h,n,ok,t in rows:
        k=(m//10*10,t)
        a=bins.setdefault(k,[[0]*len(BUCKET),0,0])
        for i,x in enumerate(json.loads(h)):
            a[0][i]+=x
        a[1]+=n
        a[2]+=ok
    for (m,t),(h,n,ok) in bins.items():
        series.append(dict(at=m*60,t=t,p50=quantile(h,.5),p95=quantile(h,.95),n=n,ok=ok))
    failures=[list(r) for r in db.execute("""select slot,target,status,raw from st_sample
             where run=? and node=? and status in ('NODE_TIMEOUT','NODE_TEST_FAILED','UNKNOWN_ERROR',
             'TARGET_UNAVAILABLE','API_UNAVAILABLE','LOCAL_NETWORK_DOWN') order by slot desc limit 30""",(run,node))]
    transfers=[dict(start=r[0],end=r[1],data=json.loads(r[2])) for r in db.execute(
        'select start,end,data from st_transfer where run=? and node=? order by start desc limit 10',(run,node))]
    gpt=[]
    if db.execute("select 1 from sqlite_master where name='st_chatgpt'").fetchone():
        limit_column=gpt_limit_column(db)
        for row in db.execute(f"""select start,status,http,tls,elapsed,evidence,{limit_column} from st_chatgpt
                where run=? and node=? order by slot desc limit 30""",(run,node)):
            proof=json.loads(row[5] or '{}')
            gpt.append(dict(at=row[0],label=LABELS.get(row[1],row[1]),http=row[2],tls=bool(row[3]),
                elapsed=row[4],phase=proof.get('phase'),tls_limit=row[6],handshake_ms=proof.get('handshake_ms')))
    return dict(series=series,failures=failures,transfers=transfers,gpt=gpt)


def gpt_limit_column(db):
    columns={r[1] for r in db.execute('pragma table_info(st_chatgpt)')}
    return 'tls_limit_s' if 'tls_limit_s' in columns else '3'


def chatgpt_counts(db,rid):
    if not db.execute("select 1 from sqlite_master where name='st_chatgpt'").fetchone():
        return {}
    limit_column=gpt_limit_column(db)
    result={}
    for n,k,at in db.execute("""select node,status,start from st_chatgpt where id in
               (select max(id) from st_chatgpt where run=? group by node)""",(rid,)):
        # This table contains homepage observations only. No HTTP outcome is chat evidence.
        result[n]=dict(latest=LABELS.get(k,k),at=at,conditions={},conversation='UNVERIFIED')
    for row in db.execute(f"""select node,{limit_column} as policy,count(*),sum(tls),sum(http is not null),
            sum(case when http=200 then 1 else 0 end),
            sum(case when status='TRANSPORT_ERROR' and json_extract(evidence,'$.phase')='tls' and
                json_extract(evidence,'$.error')='ConnectionAbortedError' and elapsed between 2950 and 3300 then 1 else 0 end),
            sum(case when http=200 and json_extract(evidence,'$.handshake_ms')>3000 and
                json_extract(evidence,'$.handshake_ms')<=5000 then 1 else 0 end)
            from st_chatgpt where run=? and status not in ('IN_PROGRESS','UNKNOWN') group by node,policy""",(rid,)):
        n,policy,known,tls,http,ok,old_timeout,late=row
        result[n]['conditions'][policy]=dict(known=known,tls=tls,http=http,ok=ok,
            old_timeout=old_timeout if policy==3 else 0,late=late if policy==5 else 0,counts={})
    for n,policy,k,count in db.execute(f"""select node,{limit_column} as policy,status,count(*)
            from st_chatgpt where run=? group by node,policy,status""",(rid,)):
        entry=result[n]
        totals=entry.setdefault('counts',{})
        totals[k]=totals.get(k,0)+count
        part=entry['conditions'].setdefault(policy,dict(known=0,tls=0,http=0,ok=0,old_timeout=0,late=0,counts={}))
        part['counts'][k]=count
    for entry in result.values():
        parts=entry['conditions'].values()
        entry.update(tested=sum(v for k,v in entry['counts'].items() if k!='IN_PROGRESS'),
            known=sum(p['known'] for p in parts),verified_tls=sum(p['tls'] for p in parts),
            http_responses=sum(p['http'] for p in parts),http200=sum(p['ok'] for p in parts))
    return result


def guest_names(db,rid):
    event=db.execute("select at,data from st_event where run=? and kind='CHATGPT_GUEST_WINDOW' order by at desc limit 1",(rid,)).fetchone()
    if not event or not db.execute("select 1 from sqlite_master where name='st_guest'").fetchone():
        return {}
    cfg=json.loads(event[1])
    entries={}
    def make(name,provider):
        return entries.setdefault((name,provider),dict(name=name,provider=provider,ai=name in cfg['ai_names'],outcomes={},history={}))
    for name,provider,limit_s,count,ok in db.execute("""select n.name,n.provider,g.tls_limit_s,count(*),sum(case when http=200 then 1 else 0 end)
            from st_chatgpt g join st_node n on g.node=n.id where g.run=? and g.status not in ('UNKNOWN','IN_PROGRESS')
            group by n.name,n.provider,g.tls_limit_s""",(rid,)):
        make(name,provider)['history'][limit_s]=f'{ok}/{count}'
    for name,provider,status,count in db.execute("""select n.name,n.provider,g.status,count(*)
            from st_guest g join st_node n on g.node=n.id where g.run=? and g.start>=? group by n.name,n.provider,g.status""",(rid,event[0])):
        make(name,provider)['outcomes'][status]=count
    for item in entries.values():
        counts=item['outcomes']
        ok,ng=counts.get('GUEST_UI_OK',0),counts.get('REGION_NG',0)
        item['result']='结果冲突' if ok and ng else 'OK · 访客界面就绪' if ok else 'NG · 明确地区受限' if ng else '未确定' if counts else '未测'
    return dict(start=event[0],end=cfg['end'],rows=sorted(entries.values(),key=lambda x:(not x['ai'],x['name'],x['provider'])))


def gpt_comparison(counts):
    cohort=[v['conditions'] for v in counts.values() if v['conditions'].get(3,{}).get('old_timeout')]
    retested=[c for c in cohort if c.get(5,{}).get('known',0)>0]
    return dict(cohort=len(cohort),retested=len(retested),now200=sum(c[5]['ok']>0 for c in retested),
                late200=sum(c[5]['late']>0 for c in retested),
                first200=sum(not c[3]['ok'] and c[5]['ok']>0 for c in retested))


def streaks(db,r,n):
    """Separate targets. A missing/uncertain observation ends the observed sequence."""
    out=[]
    for t in (0,1):
        failures=episodes=longest=length=0
        span=0.
        first=last=None
        values=[]
        for x in db.execute('''select slot,interval,status,delay from st_sample
                   where run=? and node=? and target=? order by slot''',(r,n,t)):
            at,interval,status,delay=x
            if status=='SUCCESS':
                values.append(delay)
            if status not in ELIGIBLE[1:]:
                length=0
                continue
            if last is not None and at-last>2.5*interval:
                length=0
            if not length:
                episodes+=1
                first=at
            length+=1
            failures+=1
            longest=max(longest,length)
            span=max(span,at-first)
            last=at
        values.sort()
        def q(p):
            return values[math.ceil(len(values)*p)-1] if values else None
        out.append((len(values),failures,episodes,longest,round(span,2),q(.5),q(.95),q(.99),
                    (q(.75)-q(.25)) if values else None))
    return out


CSS="""body{font:15px/1.55 'Segoe UI','Microsoft YaHei',sans-serif;color:#18322f;background:#f5f8f5;margin:0}
main{max-width:1280px;margin:auto;padding:28px}h1,h2{letter-spacing:-.04em}h1{font-size:30px}
header{border-bottom:2px solid #146651;padding-bottom:12px}section{background:white;border:1px solid #d0ded7;border-radius:12px;padding:14px 18px;margin:14px 0;overflow:auto}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}th,td{border-bottom:1px solid #e0e9e4;text-align:left;padding:7px;white-space:nowrap}
th{color:#386454}button,select{font:inherit;padding:5px}p{margin:8px 0}svg{width:100%;max-height:220px}a{color:#135e4e}
@media(max-width:700px){main{padding:12px}h1{font-size:23px}}"""


def report(db,rid):
    r=db.execute('select * from st_run where id=?',(rid,)).fetchone()
    config=run_config(db,rid)
    ranks=rankings(db,r)
    gaps=daily_gaps(db,r) if r['phase']=='formal' and time.time()>=r['end'] else []
    headings={'running':'阶段性结果','failed':'压力验证未通过','complete':'日历窗口结束','passed':'压力验证通过',
              'incomplete':'日历窗口结束，数据完整性需复核'}
    body=[f"<h1>节点稳定性 · {headings.get(r['state'],r['state'])}</h1>",
          f"<p>订阅：{textcell(config.get('subscription','历史未标注'))} · 窗口 #{rid} · 正式时长 {config.get('formal_hours',72):g} 小时 · GPT 匿名首页：{'启用' if config.get('chatgpt_enabled',True) else '按用户要求取消'} · 测量来源：{textcell((config.get('source') or {}).get('kind','当时的客户端库存'))}</p>",
          f"<p>{stamp(r['start'])} 至 {stamp(r['end'])}（北京时间） · {textcell(r['phase'])}</p>",
          '<p>白天 08–18 时，晚间 18–次日 02 时，凌晨 02–08 时。旧节点归因排名仅含可归因请求，其覆盖是归因有效槽时长 / 身份存在时长，含停机时间。实际请求结果另列，包含责任不明但已知失败的同步超时；两个指标不能混用。有效样本存在时间相关性，Wilson 下界是原筛选指标。</p>',
          f"<p>评分权重：目标中较低的成功率 Wilson 下界 {WEIGHTS['success_lower_bound']:.0%}，有效覆盖 {WEIGHTS['valid_time_coverage']:.0%}，较差目标 P95 分桶上限的延迟分 {WEIGHTS['p95']:.0%}。每目标至少 50 个有效样本、下界至少 90%、有效覆盖至少 75%。</p>"]
    from stability_outcomes import summarize, LABELS as OUTCOME_LABELS
    outcomes=summarize(db,rid)
    total=outcomes.get(None)
    if total:
        body.extend(['<h2>实际请求结果：与节点责任归因分开</h2>',
            '<p>实际请求成功率 = 目标成功 /（目标成功 + 内核超时 + 内核明确探测失败）。即使多个节点同时超时、无法判定责任，也计入已观察到的请求失败。原 UNKNOWN_ERROR 可能只是责任不明，不表示成败未知。下方原排名的节点归因指标另保留，不当成实际连接成功率。</p>',
            table(['观测结果','次数'],[(OUTCOME_LABELS.get(k,k),v) for k,v in total['counts'].items()]),
            table(['节点','实际请求成功率','成功 / 已知结局','失败已知但责任不明','结局真正未确认'],
                [(node['name'],fmt(outcomes[node['id']]['request_success_pct']/100) if outcomes[node['id']]['request_success_pct'] is not None else '—',
                  f"{outcomes[node['id']]['success']} / {outcomes[node['id']]['known']}",
                  outcomes[node['id']]['known_failure_with_uncertain_cause'],outcomes[node['id']]['outcome_unknown'])
                 for node in ranks['全部'] if node['id'] in outcomes])])
    for s,rows in ranks.items():
        qualified=[x for x in rows if x['eligible']]
        body.extend([f'<h2>{s}节点归因排名 · {len(qualified)} 个达标节点</h2>',rank_table(qualified)])
    body.extend(['<h2>全部观测对象与补测依据</h2>',rank_table(ranks['全部'])])
    cg=chatgpt_counts(db,rid)
    comp=gpt_comparison(cg)
    gpt_rows=[]
    for node in ranks['全部']:
        for policy,counts in sorted(cg.get(node['id'],{}).get('conditions',{}).items()):
            gpt_rows.append((node['name'],node['id'],policy,5 if policy==3 else 7,counts['known'],counts['tls'],
                             counts['http'],counts['ok'],counts['old_timeout'] if policy==3 else '—',
                             counts['late'] if policy==5 else '—',
                             '，'.join(f'{LABELS.get(k,k)} {v}' for k,v in counts['counts'].items())))
    if config.get('chatgpt_enabled',True):
        body.extend(['<h2>ChatGPT 匿名新连接 · 按测试条件</h2>',
        '<p>8 KiB 历史按握手限时统计。半小时匿名浏览器检查按节点名称对照历史，OK 表示访客界面就绪，NG 表示明确地区限制。实际对话未验证。</p>',
        f"<p>旧条件疑似触及 3 秒握手门限的节点 {comp['cohort']} 个；已复测 {comp['retested']} 个，其中 {comp['now200']} 个收到过 HTTP 200，{comp['late200']} 个在同次 3–5 秒握手后收到 200。旧期从未收到 200、新期收到过的有 {comp['first200']} 个。</p>",
        '<p>旧期疑似超时按 TLS 阶段 ConnectionAbortedError 且总耗时 2.95–3.30 秒识别。新期握手耗时独立计时，区间为大于 3 秒且不超过 5 秒。HTTP 200 只验证匿名官网响应。</p>',
        table(['节点','身份','TLS 限时 s','总限时 s','已知结局','TLS 完成','收到 HTTP','HTTP 200','旧疑似超时','3–5 秒握手后 200','各结果次数'],gpt_rows)])
    guest=guest_names(db,rid)
    if guest:
        body.extend(['<h2>半小时匿名访客检查</h2>',table(['名称','Provider','访客地区判定','各结果次数','3 秒首页 200/已知','5 秒首页 200/已知'],
            [(n['name'],n['provider'],n['result'],str(n['outcomes']),n['history'].get(3,'—'),n['history'].get(5,'—')) for n in guest['rows']])])
    insufficient=[(x['name'],s,fmt(x['window_coverage']),x['n']) for s in ('白天','晚间','凌晨')
                  for x in ranks[s] if x['active'] and (x['window_coverage']<.75 or min(t['n'] for t in x['targets'])<50)]
    if r['phase']=='formal' and time.time()>=r['end']:
        for s in ('白天','晚间','凌晨'):
            present={x['id'] for x in ranks[s]}
            insufficient.extend((x['name'],s,'未观测',0) for x in ranks['全部'] if x['active'] and x['id'] not in present)
    body.extend(['<h2>建议补测的节点与时段</h2>',table(['节点','时段','覆盖','有效数'],insufficient)])
    if r['phase']=='formal' and time.time()>=r['end']:
        body.extend(['<h2>逐日有效覆盖不足</h2>',
            f'<p>逐日期、逐时段核对当前订阅身份，有 {len(gaps)} 个节点时段低于 75%，建议在对应时段补测。晚间 00–02 时计入前一天晚间，首尾按实际窗口相交时长计算。</p>',
            table(['节点','身份','日期','时段','窗口小时','有效覆盖'],[(name,n,day,band,round(seconds/3600,2),fmt(frac))
                 for n,name,day,band,seconds,frac in gaps])])
    comparisons=[]
    for s in ('白天','晚间','凌晨'):
        for row in ranks[s]:
            for t,target in enumerate(row['targets']):
                comparisons.append((row['name'],s,TARGETS[t],target['n'],target['ok'],
                    fmt(target['ok']/target['n'] if target['n'] else None),fmt(row['window_coverage']),
                    target['p50'],target['p95'],target['p99']))
    body.extend(['<h2>每节点分时段、分目标表现</h2>',
        table(['节点','时段','目标','有效请求','成功','成功率','时段有效覆盖','P50 ≤ ms','P95 ≤ ms','P99 ≤ ms'],comparisons)])
    results=[]
    active=exposure(db,rid,min(time.time(),r['end']))
    for row in ranks['全部']:
        for t,stats in enumerate(streaks(db,rid,row['id'])):
            exposure_hours=sum(active[row['id']].values())/3600
            results.append((row['name'],TARGETS[t],*stats,round(stats[2]/exposure_hours,3) if exposure_hours else None))
    body.extend(['<h2>按目标的原始样本统计</h2><p>失败观测跨度以秒计。延迟及四分位距以毫秒计。长连接专项仅描述同一 TLS 连接的短时复用。小对象吞吐包含请求往返时间。</p>',
        table(['节点','目标','成功','失败','失败段数','最长连续失败数','最大失败观测跨度','P50','P95','P99','四分位距','每身份观测小时失败段数'],results)])
    health=db.execute('select m,t,sum(valid),sum(actual),sum(ok) from st_min where run=? group by m,t order by m,t',(rid,))
    regional={}
    for m,t,valid,actual,ok in health:
        k=(datetime.fromtimestamp(m*60,BJ).strftime('%Y-%m-%d'),period(m*60),t)
        a=regional.setdefault(k,[0,0,0])
        a[0]+=valid
        a[1]+=actual
        a[2]+=ok
    body.extend(['<h2>逐日时段及目标</h2>',table(['北京日期','时段','目标','实际请求','有效样本','实际成功率'],
        [(day,band,TARGETS[t],actual,valid,fmt(ok/valid if valid else None)) for (day,band,t),(valid,actual,ok) in regional.items()])])
    counts=db.execute('select status,count(*) from st_sample where run=? group by status',(rid,))
    body.extend(['<h2>原始观测结局</h2>',table(['状态','数目'],counts)])
    affected=db.execute("""select cast(slot/600 as int)*600 bucket,target,status,count(*) from st_sample
                where run=? and status in ('TARGET_UNAVAILABLE','API_UNAVAILABLE','LOCAL_NETWORK_DOWN','UNKNOWN_ERROR')
                group by bucket,target,status order by bucket""",(rid,))
    body.extend(['<h2>环境事故及无法归因的十分钟窗口</h2>',table(['窗口开始','目标','归因','槽数'],
        [(stamp(a),TARGETS[t],k,v) for a,t,k,v in affected])])
    events=db.execute("select at,kind,data from st_event where run=? and kind in ('AUDIT','SYSTEM_SUSPENDED','RATE_CHANGED','WRITER_RECOVERED','CHATGPT_TEST_CONDITIONS','CHATGPT_CADENCE_CHANGED') order by at",(rid,))
    body.extend(['<h2>环境、缺口与验收</h2>',table(['时间','事件','记录'],[(stamp(a),k,d) for a,k,d in events])])
    transfers=db.execute('select n.name,t.start,t.data from st_transfer t join st_node n on n.id=t.node where t.run=? order by t.start',(rid,))
    body.extend(['<h2>候选小流量传输及同连接复用</h2>',table(['节点','开始时间','结果'],[(n,stamp(a),d) for n,a,d in transfers])])
    file=PRIVATE/f"report-{rid}.html"
    tmp=file.with_suffix('.tmp')
    tmp.write_text('<!doctype html><meta charset=utf-8><title>节点稳定性</title><style>'+CSS+'</style><main>'+''.join(body)+'</main>',encoding='utf8')
    tmp.replace(file)
    return file


def snapshot(db):
    r=db.execute('select * from st_run order by id desc limit 1').fetchone()
    if not r:
        return {'waiting':True}
    env=db.execute('select at,data from st_env where run=? order by id desc limit 1',(r['id'],)).fetchone()
    minute=int(time.time()-18)//60-1
    recent=db.execute('select sum(ok),sum(valid),sum(actual),sum(planned) from st_min where run=? and m=?',(r['id'],minute)).fetchone()
    ranks=rankings(db,r)
    recent_nodes=dict(db.execute('select node,sum(actual) from st_min where run=? and m=? group by node',(r['id'],minute)))
    for rows in ranks.values():
        for x in rows:
            x['recent_hz']=round(recent_nodes.get(x['id'],0)/60,3)
    cg=chatgpt_counts(db,r['id'])
    return dict(id=r['id'],phase=r['phase'],state=r['state'],start=r['start'],end=r['end'],config=run_config(db,r['id']),
                at=env[0] if env else None,env=json.loads(env[1]) if env else {},recent=list(recent),
                guest=guest_names(db,r['id']),recent_end=(minute+1)*60,ranks=ranks,gpt=cg,gpt_comparison=gpt_comparison(cg))


def serve():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass
        def do_GET(self):
            host=f'127.0.0.1:{self.server.server_port}'
            if self.headers.get('Host')!=host:
                return self.send_error(403)
            url=urlsplit(self.path)
            try:
                if url.path=='/':
                    data=(Path(__file__).with_name('stability_view.html')).read_text(encoding='utf8').replace('/*STYLE*/',CSS)
                    mime='text/html'
                elif url.path in ('/state','/node'):
                    with connect(master()) as db:
                        if url.path=='/state':
                            result=snapshot(db)
                        else:
                            q=parse_qs(url.query)
                            result=node_details(db,int(q['run'][0]),int(q['id'][0]))
                        data=json.dumps(result,ensure_ascii=False,allow_nan=False)
                    mime='application/json'
                else:
                    return self.send_error(404)
            except (KeyError,ValueError):
                return self.send_error(400)
            payload=data.encode()
            self.send_response(200)
            self.send_header('Content-Type',mime+'; charset=utf-8')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Cache-Control','no-store')
            self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'")
            self.send_header('Content-Length',str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
    with HTTPServer(('127.0.0.1',18762),Handler) as srv:
        srv.timeout=2
        srv.serve_forever()
