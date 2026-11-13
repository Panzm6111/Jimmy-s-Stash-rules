"""Local CLI. Run without a Windows service or scheduler installation."""
import argparse
import asyncio
import json
import os
import secrets
import sqlite3
import statistics
import sys
import time
from pathlib import Path

from stability_core import PRIVATE, TARGETS, Sidecar, inventory, physical_interface, profile_source
from stability_runner import Runner, DISK_FLOOR
from stability_stats import connect, exposure, master, ranking, run_config


def capture_quality(db,run):
    rid=run['id']
    spans=exposure(db,rid,min(time.time(),run['end']))
    # Only an actual return from the targeted core endpoint is evidence of acquisition.
    # Preserve its original status even when cross-node attribution is inconclusive.
    measured=dict(db.execute("""select node,sum(interval) from st_sample where run=? and
        start is not null and end is not null and elapsed is not null and raw in
        ('SUCCESS/200/204','NODE_TIMEOUT/504','NODE_TEST_FAILED/503','UNKNOWN_ERROR/204-not-confirmed')
        group by node""",(rid,)))
    coverage={n:min(1,measured.get(n,0)/max(1,sum(times.values()))) for n,times in spans.items()}
    intervals="""select node,start,end from st_sample where run=? and start is not null and end is not null
                 union all select node,start,end from st_chatgpt where run=? and end is not null"""
    overlaps=db.execute(f'''with probes as ({intervals}), compared as
         (select start,max(end) over(partition by node order by start,end rows between unbounded preceding
         and 1 preceding) previous from probes) select count(*) from compared where start<previous''',(rid,rid)).fetchone()[0]
    peak=db.execute(f'''with probes as ({intervals}), edges as
         (select start t,1 delta from probes union all select end,-1 from probes), counts as
         (select sum(delta) over(order by t,delta rows unbounded preceding) n from edges) select max(n) from counts''',
         (rid,rid)).fetchone()[0]
    return dict(min_captured_time_coverage=min(coverage.values(),default=0),overlaps=overlaps,
                actual_peak=peak or 0)


def audit(db,run):
    rid = run['id']
    rows = ranking(db,run)
    env = [json.loads(r[0]) for r in db.execute('select data from st_env where run=?',(rid,))]
    pending = db.execute("select count(*) from st_sample where run=? and status='PENDING'",(rid,)).fetchone()[0]
    integrity = db.execute('pragma quick_check').fetchone()[0]
    aggregate_n = db.execute('select coalesce(sum(planned),0) from st_min where run=?',(rid,)).fetchone()[0]
    raw_n = db.execute('select count(*) from st_sample where run=?',(rid,)).fetchone()[0]
    valid_samples = sum(r['n'] for r in rows)
    actual = sum(r['actual'] for r in rows)
    counts = dict(db.execute('select status,count(*) from st_sample where run=? group by status',(rid,)))
    elapsed = min(time.time(),run['end'])-run['start']
    reasons = []
    if integrity!='ok' or pending or aggregate_n!=raw_n:
        reasons.append('database consistency')
    if elapsed<1799 or not env or len(env)<100:
        reasons.append('pressure window incomplete')
    beats=[run['start']]+[row[0] for row in db.execute('select at from st_env where run=? order by at',(rid,))]+[min(time.time(),run['end'])]
    if max((b-a for a,b in zip(beats,beats[1:])),default=elapsed)>50:
        reasons.append('pressure heartbeat gap')
    if not rows or min((r['actual']/max(1,r['planned']) for r in rows),default=0)<.80:
        reasons.append('per-node admission coverage')
    if min((r['planned'] for r in rows),default=0)<90:
        reasons.append('insufficient scheduled observations')
    capture=capture_quality(db,run)
    if capture['min_captured_time_coverage']<.95:
        reasons.append('per-node completed measurement coverage')
    if capture['overlaps'] or capture['actual_peak']>30:
        reasons.append('actual single-flight or concurrency bounds')
    if sum(row['eligible'] for row in rows)<min(3,len(rows)):
        reasons.append('insufficient independent qualified reference nodes')
    if len(env)>1:
        ram = [e['rss']+e['core_rss'] for e in env]
        if max(ram)>512*2**20 or statistics.median(ram[-10:])-statistics.median(ram[:10])>100*2**20:
            reasons.append('resident memory')
        if max(e['threads'] for e in env)>30 or max(e['peak'] for e in env)>30:
            reasons.append('task bounds')
        if min(e['disk_free'] for e in env)<DISK_FLOOR:
            reasons.append('disk headroom')
        if statistics.median(e['cpu'] for e in env)>80 or statistics.median(e['net_Bps'] for e in env)>4*2**20:
            reasons.append('host load')
        if min(sum(r['targets'][t]['ok'] for r in rows) for t in (0,1))==0:
            reasons.append('unverified target')
        baseline = db.execute("select data from st_event where run=? and kind='PREFLIGHT' order by at limit 1",(rid,)).fetchone()
        if not baseline:
            reasons.append('missing unloaded control')
        else:
            baseline=json.loads(baseline[0])['direct']
            for t in range(2):
                idle=[e[t][1] for e in baseline if e[t][0]==204]
                loaded=[e['direct'][t][1] for e in env if e['direct'][t][0]==204]
                if len(idle)<2 or len(loaded)<.75*len(env):
                    reasons.append(f'control availability {t}')
                elif statistics.median(loaded)>max(500,3*statistics.median(idle)+150):
                    reasons.append(f'control latency {t}')
        if max(e['handles'] for e in env[-10:])-min(e['handles'] for e in env[:10])>150:
            reasons.append('collector handles')
        if max(e['core_handles'] for e in env[-10:])-min(e['core_handles'] for e in env[:10])>350:
            reasons.append('core handles')
    return dict(pass_gate=not reasons,reasons=reasons,nodes=len(rows),rows=raw_n,aggregate=aggregate_n,
                actual=actual,eligible=valid_samples,counts=counts,elapsed=elapsed,integrity=integrity,
                capture=capture,attributable_fraction=valid_samples/max(1,actual),
                min_coverage=min((r['coverage'] for r in rows),default=0),
                peak=max((e['peak'] for e in env),default=0),max_heartbeat_gap=max(b-a for a,b in zip(beats,beats[1:])),
                resources={k:[min(e[k] for e in env),statistics.median(e[k] for e in env),max(e[k] for e in env)]
                           for k in ('cpu','rss','core_rss','threads','handles','core_handles','net_Bps') if env},
                physical_interface_bytes=(max(0,env[-1]['net_total']-env[0]['net_total']) if env else None))


def final_audit(db,run):
    from stability_view import rankings
    rid=run['id']
    ranks=rankings(db,run)
    raw_n=db.execute('select count(*) from st_sample where run=?',(rid,)).fetchone()[0]
    aggregate_n=db.execute('select coalesce(sum(planned),0) from st_min where run=?',(rid,)).fetchone()[0]
    unsettled=db.execute("select count(*) from st_sample where run=? and status in ('PENDING','ADJUDICATE')",(rid,)).fetchone()[0]
    integrity=db.execute('pragma quick_check').fetchone()[0]
    return dict(calendar_elapsed=time.time()>=run['end'],raw_rows=raw_n,aggregate_rows=aggregate_n,
        database_ok=integrity=='ok' and raw_n==aggregate_n and not unsettled,
        eligible_by_band={s:sum(x['eligible'] for x in rows) for s,rows in ranks.items()},
        coverage_below_75pct={s:sum(x['window_coverage']<.75 for x in rows) for s,rows in ranks.items()})


async def preflight(source=None):
    nodes = await asyncio.to_thread(inventory,secrets.token_bytes(32),source)
    if not nodes:
        raise RuntimeError('no unambiguous nodes to validate')
    interface = await asyncio.to_thread(physical_interface)
    core = Sidecar(nodes,interface)
    await core.start()
    try:
        baseline = []
        for _ in range(4):
            baseline.append(await asyncio.gather(*(core.direct(t) for t in (0,1))))
        tests = []
        seen = set()
        for n in nodes:
            pair = []
            for t in (0,1):
                start, tick = time.time(),time.monotonic()
                outcome = await core.probe(n.key,t)
                pair.append(dict(key=n.key,provider=n.provider,name=n.name,kind=n.kind,target=TARGETS[t],start=start,end=time.time(),
                                 elapsed=(time.monotonic()-tick)*1000,outcome=outcome))
                if outcome[3]:
                    await asyncio.sleep(3.25)
            tests.append(pair)
            seen.update(t for t,r in enumerate(pair) if r['outcome'][0]=='SUCCESS')
            if len(seen)==2:
                break
        return dict(nodes=len(nodes),direct=baseline,tests=tests,ok=len(seen)==2,
                    isolated_version=(await core.get('/version'))[1]['version'],interface=interface)
    finally:
        await core.close()


def create(db,phase,salt,config=None):
    now = time.time()
    hours = (config or {}).get('formal_hours',72)
    key = db.execute('insert into st_run(phase,start,end,state,salt) values(?,?,?,?,?)',
            (phase,now,now+(1800 if phase=='pressure' else hours*3600),'running',salt)).lastrowid
    if config is not None:
        db.execute('insert into st_run_config values(?,?)',(key,json.dumps(config,ensure_ascii=False)))
        db.execute('insert into st_event values(?,?,?,?)',
                   (key,now,'EXPERIMENT_SCOPE',json.dumps(config,ensure_ascii=False)))
    db.commit()
    return db.execute('select * from st_run where id=?',(key,)).fetchone()


def locked():
    import msvcrt
    PRIVATE.mkdir(parents=True,exist_ok=True)
    lock = (PRIVATE/'collector.lock').open('a+b')
    lock.seek(0)
    msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    return lock


def run_all():
    with locked(), connect(master(),True) as db:
        row = db.execute('select * from st_run order by id desc limit 1').fetchone()
        if row and row['state'] in ('complete','failed','incomplete'):
            if not (PRIVATE/f"report-{row['id']}.html").exists():
                from stability_view import report
                report(db,row['id'])
            print('Window closed. Review the recorded result before starting a new pressure window.')
            return
        if row is None:
            proof = asyncio.run(preflight())
            if not proof['ok']:
                raise RuntimeError('204 preflight failed')
            row = create(db,'pressure',secrets.token_bytes(32))
            db.execute('insert into st_event values(?,?,?,?)',(row['id'],time.time(),'PREFLIGHT',json.dumps(proof)))
            db.commit()
        while row:
            if row['state']=='passed' and row['phase']=='pressure':
                row = create(db,'formal',row['salt'],run_config(db,row['id']) or None)
            asyncio.run(Runner(db,row).run_loop())
            if (PRIVATE/'stop').exists():
                return
            if row['phase']=='pressure':
                result = audit(db,row)
                state = 'passed' if result['pass_gate'] else 'failed'
            else:
                result = final_audit(db,row)
                state = 'complete' if result['database_ok'] else 'incomplete'
            with db:
                db.execute('update st_run set state=? where id=?',(state,row['id']))
                db.execute('insert into st_event values(?,?,?,?)',(row['id'],time.time(),'AUDIT',json.dumps(result)))
            if state!='passed':
                from stability_view import report
                report(db,row['id'])
                return
            row = db.execute('select * from st_run where id=?',(row['id'],)).fetchone()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('action',choices=['prepare','preflight','run','stop','resume','status','view','report','retry','supersede'])
    p.add_argument('--profile',help='exact name of the already imported subscription')
    p.add_argument('--hours',type=float,default=72)
    p.add_argument('--no-chatgpt',action='store_true')
    p.add_argument('--history-subscription',help='user-confirmed label for unlabelled historical windows')
    args = p.parse_args()
    a = args.action
    PRIVATE.mkdir(parents=True,exist_ok=True)
    if a=='prepare':
        if not args.profile or not 0 < args.hours <= 720:
            p.error('prepare requires --profile and a positive duration of at most 720 hours')
        if not (PRIVATE/'stop').exists():
            raise RuntimeError('stop the previous collector before preparing a new experiment')
        # The supervisor denies file sharing while alive, even during restart backoff.
        with (PRIVATE/'supervisor.lock').open('a+b'), locked(), connect(master(),True) as db:
            last=db.execute('select * from st_run order by id desc limit 1').fetchone()
            if last and run_config(db,last['id']).get('source') and last['state']=='running' and time.time()<last['end']:
                raise RuntimeError('a bound experiment already exists; resume or explicitly close it')
            source=profile_source(args.profile)
            proof=asyncio.run(preflight(source))
            if not proof['ok']:
                raise RuntimeError('204 preflight failed')
            if args.history_subscription:
                for old in db.execute('select id from st_run where id not in (select run from st_run_config)').fetchall():
                    label={'subscription':args.history_subscription,'experiment_id':'legacy-'+args.history_subscription,
                           'history_label_user_confirmed':True,'formal_hours':72,'chatgpt_enabled':True}
                    db.execute('insert into st_run_config values(?,?)',(old[0],json.dumps(label)))
                    db.execute('insert into st_event values(?,?,?,?)',
                        (old[0],time.time(),'SUBSCRIPTION_LABEL_CONFIRMED',json.dumps(label)))
            config={'experiment_id':secrets.token_hex(12),'subscription':args.profile,'source':source,
                    'formal_hours':args.hours,'chatgpt_enabled':not args.no_chatgpt,'guest_enabled':False,
                    'initial_nodes':proof['nodes'],'pressure_seconds':1800,
                    'chatgpt_disabled_reason':'user requested; anonymous homepage does not establish usable chat' if args.no_chatgpt else None}
            row=create(db,'pressure',secrets.token_bytes(32),config)
            db.execute('insert into st_event values(?,?,?,?)',
                       (row['id'],time.time(),'PREFLIGHT',json.dumps(proof)))
            db.commit()
            print(json.dumps({'prepared_run':row['id'],'subscription':args.profile,'nodes':proof['nodes'],
                              'formal_hours':args.hours,'chatgpt_enabled':not args.no_chatgpt,'preflight_ok':True}))
    elif a=='preflight':
        print(json.dumps(asyncio.run(preflight(profile_source(args.profile) if args.profile else None))))
    elif a=='stop':
        (PRIVATE/'stop').touch()
    elif a=='supersede':
        with locked(),connect(master(),True) as db:
            r=db.execute('select * from st_run order by id desc limit 1').fetchone()
            if not r or r['state']!='running' or r['phase']!='pressure' or not (PRIVATE/'stop').exists():
                raise RuntimeError('only a stopped pressure window can be superseded')
            db.execute("update st_run set state='failed' where id=?",(r['id'],))
            db.execute('insert into st_event values(?,?,?,?)',(r['id'],time.time(),'SUPERSEDED',
                       json.dumps({'reason':'collector change; full new pressure window required'})))
    elif a in ('run','resume','retry'):
        if a=='retry':
            with locked(),connect(master(),True) as db:
                last = db.execute('select * from st_run order by id desc limit 1').fetchone()
                if not last or last['phase']!='pressure' or last['state']!='failed':
                    raise RuntimeError('retry requires a failed pressure run')
                config=run_config(db,last['id'])
                proof=asyncio.run(preflight(config.get('source')))
                if not proof['ok']:
                    raise RuntimeError('204 preflight failed')
                new=create(db,'pressure',last['salt'],config or None)
                db.execute('insert into st_event values(?,?,?,?)',(new['id'],time.time(),'PREFLIGHT',json.dumps(proof)))
        if a in ('resume','retry'):
            (PRIVATE/'stop').unlink(missing_ok=True)
        run_all()
    elif a=='view':
        from stability_view import serve
        serve()
    else:
        with connect(master()) as db:
            r = db.execute('select * from st_run order by id desc limit 1').fetchone()
            if a=='report':
                from stability_view import report
                report(db,r['id'])
            else:
                e=db.execute('select at,data from st_env where run=? order by id desc limit 1',(r['id'],)).fetchone()
                print(json.dumps(dict(id=r['id'],phase=r['phase'],state=r['state'],start=r['start'],end=r['end'],
                    config=run_config(db,r['id']),heartbeat=e[0] if e else None,env=json.loads(e[1]) if e else None)))


if __name__=='__main__':
    try:
        main()
    except Exception as exc:
        PRIVATE.mkdir(parents=True,exist_ok=True)
        # Exception strings from providers or transport may contain credentials.
        import traceback
        stack=[(Path(f.filename).name,f.lineno,f.name) for f in traceback.extract_tb(exc.__traceback__)]
        (PRIVATE/'alert.txt').write_text(json.dumps([time.time(),type(exc).__name__,stack]),encoding='utf8')
        print(type(exc).__name__,stack,file=sys.stderr)
        sys.exit(1)
