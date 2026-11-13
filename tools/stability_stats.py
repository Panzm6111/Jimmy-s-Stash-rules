"""Storage, minute aggregates, coverage and ranking for the private SQLite master."""
import json
import math
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

from stability_core import BASE

BJ = timezone(timedelta(hours=8), 'Asia/Shanghai')
ELIGIBLE = ('SUCCESS', 'NODE_TIMEOUT', 'NODE_TEST_FAILED')
BUCKET = (50, 100, 150, 200, 300, 450, 650, 900, 1300, 1800, 2400, 3000, 65535)
WEIGHTS = {'success_lower_bound': .70, 'valid_time_coverage': .25, 'p95': .05}
DDL = """
CREATE TABLE IF NOT EXISTS st_run(id INTEGER PRIMARY KEY,phase TEXT,start REAL,end REAL,state TEXT,salt BLOB);
CREATE TABLE IF NOT EXISTS st_run_config(run INTEGER PRIMARY KEY,data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS st_node(id INTEGER PRIMARY KEY,key TEXT UNIQUE,provider TEXT,name TEXT,kind TEXT);
CREATE TABLE IF NOT EXISTS st_excluded(node INTEGER PRIMARY KEY,reason TEXT);
CREATE TABLE IF NOT EXISTS st_active(run INTEGER,node INTEGER,start REAL,end REAL,PRIMARY KEY(run,node,start));
CREATE TABLE IF NOT EXISTS st_event(run INTEGER,at REAL,kind TEXT,data TEXT);
CREATE INDEX IF NOT EXISTS st_events ON st_event(run,at);
CREATE TABLE IF NOT EXISTS st_env(id INTEGER PRIMARY KEY,run INTEGER,at REAL,data TEXT);
CREATE INDEX IF NOT EXISTS st_env_run ON st_env(run,at);
CREATE TABLE IF NOT EXISTS st_sample(id INTEGER PRIMARY KEY,run INTEGER,node INTEGER,slot REAL,start REAL,
 end REAL,target INTEGER,elapsed REAL,delay INTEGER,status TEXT,raw TEXT,interval REAL,env INTEGER,
 UNIQUE(run,node,slot));
CREATE INDEX IF NOT EXISTS st_detail ON st_sample(run,node,slot);
CREATE INDEX IF NOT EXISTS st_fail ON st_sample(run,node,slot)
 WHERE status in ('NODE_TIMEOUT','NODE_TEST_FAILED','UNKNOWN_ERROR','TARGET_UNAVAILABLE','API_UNAVAILABLE','LOCAL_NETWORK_DOWN');
CREATE TABLE IF NOT EXISTS st_min(run INTEGER,node INTEGER,m INTEGER,t INTEGER,planned INTEGER,actual INTEGER,
 valid INTEGER,ok INTEGER,validsec REAL,hist TEXT,busy INTEGER,capacity INTEGER,PRIMARY KEY(run,node,m,t)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS st_transfer(run INTEGER,node INTEGER,start REAL,end REAL,data TEXT);
CREATE TABLE IF NOT EXISTS st_period(run INTEGER,node INTEGER,m TEXT,t INTEGER,planned INTEGER,actual INTEGER,
 valid INTEGER,ok INTEGER,validsec REAL,hist TEXT,busy INTEGER,capacity INTEGER,PRIMARY KEY(run,node,m,t)) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS st_min_time ON st_min(run,m);
CREATE TABLE IF NOT EXISTS st_weight(run INTEGER,node INTEGER,band TEXT,t INTEGER,oksec REAL,
 PRIMARY KEY(run,node,band,t)) WITHOUT ROWID;
"""


def master():
    path = BASE / '.local' / 'clash-monitor'
    current = json.loads((path / 'current.json').read_text(encoding='utf-8-sig'))
    db = Path(current['session']).resolve().with_name('monitor.sqlite')
    if not db.is_relative_to(path.resolve()) or not db.is_file():
        raise RuntimeError('existing monitoring database unavailable')
    return db


def run_config(db, run):
    """Persist scope per window so a restart cannot select another subscription."""
    try:
        row = db.execute('select data from st_run_config where run=?',(run,)).fetchone()
    except sqlite3.OperationalError as exc:
        if 'no such table' not in str(exc):
            raise
        row = None
    return json.loads(row[0]) if row else {}


def connect(path, write=False):
    db = sqlite3.connect(path.as_uri() + ('?mode=rw' if write else '?mode=ro'), uri=True, timeout=1)
    db.row_factory = sqlite3.Row
    if write:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA synchronous=FULL')
        db.executescript(DDL)
    return db


def period(t):
    h = datetime.fromtimestamp(t, BJ).hour
    return '白天' if 8 <= h < 18 else '凌晨' if 2 <= h < 8 else '晚间'


def exposure(db, run, now):
    out = defaultdict(lambda: defaultdict(float))
    for n,a,b in db.execute('''select node,start,end from st_active where run=?
                        and node not in (select node from st_excluded)''',(run,)):
        end = min(now, b or now)
        while a < end:
            edge = min(end, (int(a)//3600+1)*3600)
            out[n][period(a)] += edge-a
            a = edge
    return out


def histogram(delays):
    h = [0]*len(BUCKET)
    for d in delays:
        h[next(i for i,x in enumerate(BUCKET) if d <= x)] += 1
    return h


def quantile(h, p):
    count = sum(h)
    if not count:
        return None
    threshold = math.ceil(count*p)
    for x,v in zip(BUCKET,h):
        threshold -= v
        if threshold <= 0:
            return x


def lower(ok, n):
    if n == 0:
        return 0.
    z = 1.96
    p = ok/n
    return (p+z*z/(2*n)-z*math.sqrt((p*(1-p)+z*z/(4*n))/n))/(1+z*z/n)


def classify(raw, peers, env, t):
    if raw not in ('NODE_TIMEOUT','NODE_TEST_FAILED'):
        return raw
    if not env.get('api'):
        return 'API_UNAVAILABLE'
    if env.get('uplink') is False:
        return 'LOCAL_NETWORK_DOWN'
    observed, failed = peers[t]
    if observed < 3 or failed / observed >= .5:
        if (observed >= 3 and env['direct'][t][0] not in (0,204)
                and env['direct'][1-t][0] == 204):
            return 'TARGET_UNAVAILABLE'
        return 'UNKNOWN_ERROR'
    return raw


def aggregate(db, run, rows):
    """Rows have already been adjudicated. Commit the bucket with the raw outcomes."""
    groups = defaultdict(list)
    for r in rows:
        groups[r['node'],int(r['slot'])//60,r['target']].append(r)
    for (node,m,t), group in groups.items():
        h = histogram(r['delay'] for r in group if r['status']=='SUCCESS')
        k = (run,node,m,t)
        values = (len(group),sum(r['start'] is not None for r in group),
                  sum(r['status'] in ELIGIBLE for r in group),sum(r['status']=='SUCCESS' for r in group),
                  sum(r['interval'] for r in group if r['status'] in ELIGIBLE),json.dumps(h),
                  sum(r['status']=='SKIPPED_BUSY' for r in group),
                  sum(r['status']=='SKIPPED_CAPACITY' for r in group))
        db.execute('''insert into st_weight values(?,?,?,?,?) on conflict(run,node,band,t)
                      do update set oksec=oksec+excluded.oksec''',
                   (run,node,period(m*60),t,sum(r['interval'] for r in group if r['status']=='SUCCESS')))
        for table,time_key in [('st_min',m),('st_period',period(m*60))]:
            k = (run,node,time_key,t)
            old = db.execute(f'select hist from {table} where run=? and node=? and m=? and t=?', k).fetchone()
            combined = [a+b for a,b in zip(h,json.loads(old[0]))] if old else h
            db.execute(f'''insert into {table} values(?,?,?,?,?,?,?,?,?,?,?,?)
          on conflict(run,node,m,t) do update set planned=planned+excluded.planned,actual=actual+excluded.actual,
          valid=valid+excluded.valid,ok=ok+excluded.ok,validsec=validsec+excluded.validsec,hist=excluded.hist,
          busy=busy+excluded.busy,capacity=capacity+excluded.capacity''',
                       k+values[:5]+(json.dumps(combined),)+values[6:])


def ranking(db, run, selected='全部', now=None, warmup=False):
    now = min(now or time.time(),run['end'])
    durations = exposure(db,run['id'],now)
    calendar = defaultdict(float)
    a = run['start']
    while a < now:
        edge = min(now,(int(a)//3600+1)*3600)
        calendar[period(a)] += edge-a
        a = edge
    span = sum(calendar.values()) if selected=='全部' else calendar[selected]
    weighted = defaultdict(float)
    for n,s,t,sec in db.execute('select node,band,t,oksec from st_weight where run=?',(run['id'],)):
        if selected=='全部' or s==selected:
            weighted[n,t]+=sec
    # Aggregate hours/minutes, never raw observations, on the dashboard.
    sums = defaultdict(lambda: [[0]*7 + [[0]*len(BUCKET)] for _ in range(2)])
    for r in db.execute('select * from st_period where run=?',(run['id'],)):
        if selected != '全部' and r['m'] != selected:
            continue
        a = sums[r['node']][r['t']]
        for i,k in enumerate(('planned','actual','valid','ok','validsec','busy','capacity')):
            a[i] += r[k]
        for i,x in enumerate(json.loads(r['hist'])):
            a[7][i] += x
    names = {r['id']:r['name'] for r in db.execute('select id,name from st_node')}
    out = []
    for n,sections in durations.items():
        duration = sum(sections.values()) if selected=='全部' else sections[selected]
        if not duration:
            continue
        targets = sums[n]
        planned,actual,valid,ok,seconds,busy,cap = map(sum,zip(*(t[:7] for t in targets)))
        coverage = min(1,seconds/duration)
        p95 = max((quantile(t[7],.95) or 65535) for t in targets)
        bounds=[]
        for i,t in enumerate(targets):
            # Cap the effective sample size at one observation per five seconds.
            # Weight each valid response by its planned interval to compare time, not number of requests.
            effective = min(t[2],t[4]/5)
            rate = weighted[n,i]/t[4] if (n,i) in weighted and t[4] else t[3]/max(1,t[2])
            bounds.append(lower(min(1.,rate)*effective,effective))
        bound = min(bounds)
        score = 100*(WEIGHTS['success_lower_bound']*bound + WEIGHTS['valid_time_coverage']*coverage
                     + WEIGHTS['p95']*max(0,1-p95/3000))
        # Insist on evidence on each target; all-period final standings require all time bands.
        window_coverage = min(1,seconds/max(1,span))
        qualified = coverage >= .75 and window_coverage>=.75 and min(t[2] for t in targets) >= 50 and bound >= .90
        out.append(dict(id=n,name=names[n],score=round(score,2),eligible=qualified,n=valid,
            success=round(ok/valid,5) if valid else None,coverage=round(coverage,4),actual=actual,
            planned=planned,hz=round(actual/duration,3),busy=busy,capacity=cap,window_coverage=round(window_coverage,4),
            targets=[dict(n=t[2],ok=t[3],lower=round(bounds[i],4),
                          p50=quantile(t[7],.5),p95=quantile(t[7],.95),p99=quantile(t[7],.99)) for i,t in enumerate(targets)]))
    return sorted(out,key=lambda r:(r['eligible'],r['score']),reverse=True)
