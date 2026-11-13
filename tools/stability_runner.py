"""Monotonic single-flight measurement, durable admission and pressure gate."""
import asyncio
import json
import math
import os
import secrets
import shutil
import sqlite3
import statistics
import time
from collections import Counter, defaultdict, deque
from dataclasses import dataclass

import psutil

from stability_core import PRIVATE, Sidecar, inventory_snapshot, physical_interface, verified_notice_providers, NOTICE
from stability_stats import aggregate, classify, connect, master, ranking, run_config
import stability_chatgpt as gpt

RATES = ((5,1),(5,2),(5,3),(5,5),(10,1),(10,2),(10,3),(10,5),(15,3),(15,5))
LIMIT = 30
PER_TARGET = 8
DISK_FLOOR = 3 * 2**30
BATCH_LIMIT = 768


@dataclass
class Plan:
    node: int
    key: str
    next: float
    interval: int = 5
    turn: int = 0
    last: float = -1e10
    cool: float = 0
    active: bool = False

    def due(self, now):
        if now < self.next:
            return None
        missed = math.floor((now-self.next)/self.interval)
        slot = self.next + missed*self.interval
        self.next = slot+self.interval
        return slot, missed


def candidates(rows, current, maximum=10):
    qualified = [r for r in rows if r['eligible']]
    qualified.sort(key=lambda r:r['score'] + (1.5 if r['id'] in current else 0),reverse=True)
    return {r['id'] for r in qualified[:maximum]}


def admit(plan, now, inflight, used, limit, fast):
    if plan.active or now < plan.cool:
        return 'SKIPPED_BUSY'
    if inflight >= limit or (plan.interval < 5 and fast >= max(1,limit//2)) or used >= PER_TARGET:
        return 'SKIPPED_CAPACITY'


def level_change(level, bad, good, held):
    if bad >= 2 and held >= 120:
        return min(len(RATES)-1,level+1)
    if good >= 5 and held >= 300:
        return max(0,level-1)
    return level


class Runner:
    def __init__(self, db, run):
        self.db,self.run = db,run
        self.config = run_config(db,run['id'])
        self.plans = {}
        self.tasks = {}
        self.buckets = defaultdict(list)
        self.starts = [deque(),deque()]
        self.count = Counter()
        self.level = self.bad = self.good = 0
        self.limit = LIMIT
        self.picks = set()
        self.changed = self.boot = time.monotonic()
        self.env = {}
        self.env_id = None
        self.core = None
        self.telemetry = self.catalog = self.special = None
        self.special_key = None
        self.maintenance = None
        self.available = False
        self.peak = 0
        self.net = None
        self.last_slot_wall = 0
        self.inventory_issues = None
        self.unavailable_kind = 'API_UNAVAILABLE'
        self.guest = None
        self.gpt_due = {}
        self.gpt_global = 0
        self.waiting = {}
        self.debt = defaultdict(float)
        self.admissions = defaultdict(Counter)
        self.service = {}

    def event(self, kind, data):
        self.db.execute('insert into st_event values(?,?,?,?)',
                        (self.run['id'],time.time(),kind,json.dumps(data,ensure_ascii=False)))

    def calibrate(self):
        rid=self.run['id']
        if self.config.get('experiment_id'):
            last=self.db.execute('''select e.data,e.run from st_env e join st_run_config c on c.run=e.run
                where e.run<=? and json_extract(c.data,'$.experiment_id')=? order by e.id desc limit 1''',
                (rid,self.config['experiment_id'])).fetchone()
        else:
            last=self.db.execute('select data,run from st_env where run<=? order by id desc limit 1',(rid,)).fetchone()
        if last is None:
            return
        env=json.loads(last[0])
        rates=(env['ordinary'],env['candidate'])
        reason='resume or inherit measured rate'
        if last[1]!=rid:
            worst=self.db.execute('''select max(loss) from (select 1.*sum(capacity)/sum(planned) loss
                      from st_min where run=? group by node having sum(planned)>=20)''',(last[1],)).fetchone()[0] or 0
            if worst>=.08 and rates[0]==5:
                rates=(10,1)
                reason=f'previous worst node capacity loss {worst:.1%}'
            elif rates[0]==5:
                changes=(json.loads(row[0]) for row in self.db.execute(
                    "select data from st_event where run=? and kind='RATE_CHANGED'",(last[1],)))
                if any('worst node capacity loss' in v.get('reasons',[]) and v['rates'][0]>=10 for v in changes):
                    rates=(10,1)
                    reason='previous window required ordinary 10s for fair admission'
        self.level=RATES.index(rates) if rates in RATES else 0
        self.event('RATE_CHANGED',{'reasons':[reason],'rates':RATES[self.level],'limit':self.limit})
        self.db.commit()

    def recover(self):
        r = self.run['id']
        from stability_guest import GuestWindow
        self.guest=GuestWindow(self.db,r)
        if self.config.get('chatgpt_enabled',True):
            gpt.register_conditions(self.db,r)
        else:
            self.db.executescript(gpt.SCHEMA)
        self.db.execute("update st_chatgpt set status='UNKNOWN',evidence=? where run=? and status='IN_PROGRESS'",
                        (json.dumps({'reason':'process ended before result'}),r))
        pending = list(self.db.execute("select * from st_sample where run=? and status in ('PENDING','ADJUDICATE')",(r,)))
        if pending:
            for entry in pending:
                row = dict(entry)
                if row['status']=='PENDING':
                    row.update(status='UNKNOWN_ERROR',raw='crash-after-admission')
                else:
                    status = row['raw'].split('/')[0]
                    row['status'] = status if status not in ('NODE_TIMEOUT','NODE_TEST_FAILED') else 'UNKNOWN_ERROR'
                self.db.execute('update st_sample set status=?,raw=? where id=?',(row['status'],row['raw'],row['id']))
                aggregate(self.db,r,[row])
        last = self.db.execute('select max(at) from st_env where run=?',(r,)).fetchone()[0]
        if last:
            self.event('SYSTEM_SUSPENDED',{'last_heartbeat':last,'resumed':time.time(),'pending':len(pending)})
        self.db.commit()

    async def install(self, nodes, interface):
        # Replacement only after draining requests; do not address a stale alias.
        candidate = Sidecar(nodes,interface)
        await candidate.start()
        previous = self.core
        self.core = candidate
        if previous:
            await previous.close()
        now,wall = time.monotonic(),time.time()
        rid = self.run['id']
        for provider in verified_notice_providers:
            for index,name in self.db.execute('select id,name from st_node where provider=?',(provider,)):
                if NOTICE.match(name):
                    self.db.execute('insert or ignore into st_excluded values(?,?)',(index,'subscription information label'))
        old_active = {r[0] for r in self.db.execute('select node from st_active where run=? and end is null',(rid,))}
        new = {}
        for i,n in enumerate(sorted(nodes,key=lambda n:n.key)):
            self.db.execute('insert into st_node(key,provider,name,kind) values(?,?,?,?) on conflict(key) do nothing',
                            (n.key,n.provider,n.name,n.kind))
            idx = self.db.execute('select id from st_node where key=?',(n.key,)).fetchone()[0]
            base=RATES[self.level][0]
            new[idx] = self.plans.get(idx,Plan(idx,n.key,now+base*(i+.5)/len(nodes),base,turn=i%2))
            if idx not in old_active:
                self.db.execute('insert into st_active values(?,?,?,NULL)',(rid,idx,wall))
        for idx in old_active-new.keys():
            self.db.execute('update st_active set end=? where run=? and node=? and end is null',(wall,rid,idx))
        self.plans = new
        previous_gpt=dict(self.db.execute('select node,max(slot) from st_chatgpt where run=? group by node',(rid,)))
        last_gpt_start=self.db.execute('select max(start) from st_chatgpt where run=?',(rid,)).fetchone()[0]
        if last_gpt_start is not None:
            self.gpt_global=max(self.gpt_global,now+max(0,last_gpt_start+gpt.GLOBAL_SPACING-wall))
        self.gpt_due={n:self.gpt_due.get(n,now+max(0,previous_gpt[n]+gpt.INTERVAL-wall)
            if n in previous_gpt else now+i*gpt.INTERVAL/max(1,len(new))) for i,n in enumerate(new)}
        for n,k,ended,proof,code in self.db.execute("""select node,status,end,evidence,http from st_chatgpt
                where run=? and end>? and (status in ('CHALLENGE','RATE_LIMITED') or http=429
                or json_extract(evidence,'$.cf_challenge')=1)""",(rid,wall-259200)):
            evidence=json.loads(proof or '{}')
            if (k=='CHALLENGE' or evidence.get('cf_challenge')) and n in self.gpt_due:
                self.gpt_due[n]=max(self.gpt_due[n],now+ended+3600-wall)
            if k=='RATE_LIMITED' or code==429:
                self.gpt_global=max(self.gpt_global,now+ended+evidence.get('retry_after_s',1800)-wall)
        self.event('CONFIG_CHANGED',{'added':sorted(new.keys()-old_active),'removed':sorted(old_active-new.keys()),
                                     'core_pid':candidate.proc.pid,'interface':interface})
        self.db.commit()

    async def environment(self):
        api = False
        try:
            api = (await self.core.get('/version'))[0] == 200
        except Exception:
            pass
        direct = await asyncio.gather(*(self.core.direct(t) for t in range(2)))
        iface = self.core.interface
        p = psutil.Process()
        counters = psutil.net_io_counters(pernic=True).get(iface)
        tick = time.monotonic()
        total = counters.bytes_recv+counters.bytes_sent if counters else 0
        rate = max(0,(total-self.net[1])/max(1,tick-self.net[0])) if self.net else 0
        self.net = (tick,total)
        child = psutil.Process(self.core.proc.pid) if self.core.proc.poll() is None else None
        nic = psutil.net_if_stats().get(iface)
        return dict(api=api,direct=direct,uplink=bool(nic and nic.isup),cpu=psutil.cpu_percent(),
            rss=p.memory_info().rss,core_rss=child.memory_info().rss if child else 0,
            threads=p.num_threads(),handles=p.num_handles(),core_handles=child.num_handles() if child else 0,
            collector_cpu_s=sum(p.cpu_times()[:2]),core_cpu_s=sum(child.cpu_times()[:2]) if child else None,
            core_threads=child.num_threads() if child else 0,
            waiting_slots=len(self.waiting),special_in_flight=int(self.special is not None),
            net_total=total,net_Bps=round(rate),disk_free=shutil.disk_usage(master().parent).free,
            in_flight=len(self.tasks),peak=self.peak,level=self.level,limit=self.limit,
            ordinary=RATES[self.level][0],candidate=RATES[self.level][1],nodes=len(self.plans))

    def save_env(self, env):
        self.env = env
        self.env_id = self.db.execute('insert into st_env(run,at,data) values(?,?,?)',
            (self.run['id'],time.time(),json.dumps(env))).lastrowid
        self.peak = len(self.tasks)

    def adjust(self):
        total = sum(self.count.values())
        actual = total-self.count['SKIPPED_CAPACITY']-self.count['SKIPPED_BUSY']
        cpu = self.env.get('cpu',0)
        reasons = []
        for name,value,threshold in [('capacity',self.count['SKIPPED_CAPACITY']/max(1,total),.08),
                ('busy',self.count['SKIPPED_BUSY']/max(1,total),.12),
                ('host_cpu',cpu,85),('host_net_Bps',self.env.get('net_Bps',0),4*2**20),
                ('memory',self.env.get('rss',0)+self.env.get('core_rss',0),512*2**20)]:
            if value>threshold:
                reasons.append(name)
        if self.count['NODE_TIMEOUT']/max(1,actual)>.18 and reasons:
            reasons.append('timeouts under pressure')
        worst=max((v['SKIPPED_CAPACITY']/v['all'] for v in self.admissions.values() if v['all']>=4),default=0)
        if worst>.10:
            reasons.append('worst node capacity loss')
        self.bad = self.bad+1 if reasons else 0
        self.good = self.good+1 if not reasons else 0
        old = self.level
        step=level_change(old,self.bad,self.good,time.monotonic()-self.changed)
        ordinary,fast=RATES[old]
        if step>old:
            if not self.picks or 'worst node capacity loss' in reasons or 'host_net_Bps' in reasons:
                target_ordinary=10 if ordinary==5 else 15
                match=[i for i,(o,f) in enumerate(RATES) if o==target_ordinary and f>=fast]
                step=match[0] if match else len(RATES)-1
            self.level=step
        elif step<old:
            if not self.picks and ordinary>5:
                step=0 if ordinary==10 else 4
            proposed=RATES[step]
            demand=sum(self.service.get(n,3)/proposed[int(n in self.picks)] for n in self.plans)
            rate=sum(1/proposed[int(n in self.picks)] for n in self.plans)
            if demand <= self.limit*.70 and rate<=2*PER_TARGET*.95:
                self.level=step
        if self.level != old:
            self.changed = time.monotonic()
            if self.level>old and any(k in reasons for k in ('memory','host_cpu','host_net_Bps')):
                self.limit=max(16,self.limit-2)
            elif self.level<old:
                self.limit=min(LIMIT,self.limit+2)
            self.set_rates()
            self.event('RATE_CHANGED',{'reasons':reasons or ['five healthy windows'],'level':self.level,
                'limit':self.limit,'rates':RATES[self.level],'counts':dict(self.count),'worst_capacity':worst})
        self.count.clear()
        self.admissions.clear()

    def set_rates(self):
        self.expire_waiting(time.monotonic(),time.time(),True)
        now = time.monotonic()
        for p in self.plans.values():
            interval = RATES[self.level][int(p.node in self.picks)]
            if p.interval != interval:
                p.interval = interval
                p.next = now+interval*((int(p.key[:8],16)+.5)/2**32)

    def record(self,p,slot,wall,now,target,skip):
        # Write admission intent before dispatch. Recovery never guesses its outcome.
        row = dict(run=self.run['id'],node=p.node,slot=wall+(slot-now),start=None,target=target,
                   interval=p.interval,env=self.env_id,status=skip or 'PENDING',end=None,raw=skip,delay=None,elapsed=None)
        row['id'] = self.db.execute('''insert into st_sample(run,node,slot,start,target,interval,env,status,raw)
              values(:run,:node,:slot,:start,:target,:interval,:env,:status,:raw)''',
              dict(row,status='ADJUDICATE' if skip else 'PENDING')).lastrowid
        return row

    async def measure(self, p, row):
        start = time.monotonic()
        row['start'] = time.time()
        try:
            self.db.execute('update st_sample set start=? where id=?',(row['start'],row['id']))
            self.db.commit()
        except sqlite3.OperationalError as e:
            self.db.rollback()
            # No network request until the durable start marker is committed.
            row.update(start=None,status='SKIPPED_CAPACITY',raw='storage-before-send')
            return row
        status,delay,code,uncertain = await self.core.probe(p.key,row['target'])
        row.update(end=time.time(),elapsed=(time.monotonic()-start)*1000,delay=delay,status=status,raw=code)
        if uncertain:
            p.cool = time.monotonic()+3.25
        return row

    def collect(self):
        for node,(p,task) in list(self.tasks.items()):
            if task.done():
                row = task.result()
                self.db.execute("""update st_sample set start=:start,end=:end,elapsed=:elapsed,
                   delay=:delay,status='ADJUDICATE',raw=:evidence where id=:id""",
                   dict(row,evidence=f"{row['status']}/{row['raw']}"))
                p.active = False
                del self.tasks[node]
                self.count[row['status']] += 1
                if row['elapsed']:
                    seconds=min(5.,row['elapsed']/1000)
                    self.service[node]=.85*self.service.get(node,seconds)+.15*seconds
                self.buckets[int(row['slot'])//10].append(row)

    def flush(self, wall, force=False):
        for bucket in list(self.buckets):
            if not force and wall < (bucket+1)*10+7:
                continue
            rows = self.buckets.pop(bucket)
            peers = []
            for t in range(2):
                votes = defaultdict(list)
                for r in rows:
                    if r['target']==t and r['status'] in ('SUCCESS','NODE_TEST_FAILED','NODE_TIMEOUT'):
                        votes[r['node']].append(r['status']=='SUCCESS')
                peers.append((len(votes),sum(not any(v) for v in votes.values())))
            contexts = {}
            for r in rows:
                eid = r['env']
                if eid not in contexts:
                    contexts[eid] = json.loads(self.db.execute('select data from st_env where id=?',(eid,)).fetchone()[0])
                raw = r['status']
                r['status'] = classify(raw,peers,contexts[eid],r['target'])
                r['raw'] = f"{raw}/{r['raw']}"
            self.db.executemany('''update st_sample set start=:start,end=:end,elapsed=:elapsed,delay=:delay,
                status=:status,raw=:raw where id=:id''',rows)
            aggregate(self.db,self.run['id'],rows)
        self.db.commit()

    def skip(self,p,slot,now,wall,status):
        row=self.record(p,slot,wall,now,p.turn%2,status)
        self.buckets[int(row['slot'])//10].append(row)
        self.count[status]+=1
        self.admissions[p.node]['all']+=1
        self.admissions[p.node][status]+=1
        if status=='SKIPPED_CAPACITY':
            self.debt[p.node]=.85*self.debt[p.node]+.15

    def expire_waiting(self,now,wall,force=False):
        for node,(p,slot,deadline) in list(self.waiting.items()):
            if force or now>deadline:
                self.skip(p,slot,now,wall,'SKIPPED_CAPACITY')
                del self.waiting[node]

    def dispatch(self,now,wall):
        self.expire_waiting(now,wall)
        reserved = []
        for p in self.plans.values():
            due = p.due(now)
            if not due:
                continue
            slot,missed=due
            if missed:
                self.event('MISSED_SLOTS',{'node':p.node,'count':missed,'interval':p.interval,'last':wall})
            deadline=slot+min(1.,p.interval*.25)
            if p.active or p.key==self.special_key or (self.guest and p is self.guest.plan) or now<p.cool:
                self.skip(p,slot,now,wall,'SKIPPED_BUSY')
            elif not self.available:
                self.skip(p,slot,now,wall,self.unavailable_kind)
            elif now>deadline:
                self.skip(p,slot,now,wall,'SKIPPED_CAPACITY')
            else:
                self.waiting[p.node]=(p,slot,deadline)
        for p,slot,deadline in sorted(self.waiting.values(),key=lambda x:(-self.debt[x[0].node],x[0].last)):
            t = p.turn%2
            q = self.starts[t]
            while q and now-q[0]>=1:
                q.popleft()
            fast = sum(other.interval<5 for other,_ in self.tasks.values()) + sum(other.interval<5 for other,_ in reserved)
            auxiliary=int(self.special is not None and not self.special.done())+int(bool(self.guest and self.guest.task))
            skip = admit(p,now,len(self.tasks)+len(reserved)+auxiliary,len(q),self.limit,fast)
            if not self.available:
                skip = self.unavailable_kind
            if p.key == self.special_key or (self.guest and p is self.guest.plan):
                skip = 'SKIPPED_BUSY'
            if skip=='SKIPPED_CAPACITY':
                continue
            del self.waiting[p.node]
            if skip:
                self.skip(p,slot,now,wall,skip)
            else:
                r = self.record(p,slot,wall,now,t,None)
                p.turn += 1
                p.last,p.active = now,True
                q.append(now)
                self.admissions[p.node]['all']+=1
                self.debt[p.node]*=.85
                reserved.append((p,r))
        if reserved:
            self.db.commit()
        for p,r in reserved:
            self.tasks[p.node] = (p,asyncio.create_task(self.measure(p,r)))
        self.peak = max(self.peak,len(self.tasks))

    async def run_loop(self):
        if shutil.disk_usage(master().parent).free < DISK_FLOOR:
            raise OSError('disk reserve reached before admission')
        self.recover()
        self.calibrate()
        self.db.execute('pragma busy_timeout=0')
        blocked = None
        last_check = last_wall = None
        next_env = next_eval = next_inventory = next_special = next_adjust = 0
        try:
            while time.time() < self.run['end'] and not (PRIVATE/'stop').exists():
                now,wall = time.monotonic(),time.time()
                try:
                    if not self.db.in_transaction:
                        self.db.execute('begin immediate')
                except sqlite3.OperationalError as e:
                    if getattr(e,'sqlite_errorcode',None) not in (sqlite3.SQLITE_BUSY,sqlite3.SQLITE_LOCKED):
                        raise
                    if blocked is None:
                        blocked = wall
                        (PRIVATE/'writer-alert.txt').write_text('SQLite writer busy; admissions paused',encoding='utf8')
                    await asyncio.sleep(.25)
                    continue
                if blocked is not None:
                    self.event('WRITER_RECOVERED',{'from':blocked,'to':wall})
                    blocked = None
                self.collect()
                if last_wall and (abs((wall-last_wall)-(now-last_check))>2 or now-last_check>10):
                    self.event('SYSTEM_SUSPENDED',{'from':last_wall,'to':wall})
                    self.expire_waiting(now,wall,True)
                    self.flush(wall,True)
                    for p in self.plans.values():
                        p.next = now + p.interval*((int(p.key[:8],16)+.5)/2**32)
                last_wall,last_check = wall,now
                if now >= next_inventory and not self.catalog and not self.maintenance:
                    self.catalog = asyncio.create_task(asyncio.to_thread(inventory_snapshot,self.run['salt'],self.config.get('source')))
                    next_inventory = now+60
                if self.catalog and self.catalog.done():
                    try:
                        nodes,issues = self.catalog.result()
                        if issues!=self.inventory_issues:
                            if issues or self.inventory_issues:
                                self.event('CONFIG_CHANGED',{'quarantined':issues})
                            self.inventory_issues=issues
                        self.available = bool(nodes) or bool(self.core and issues)
                        self.unavailable_kind='CONFIG_CHANGED' if not nodes else 'API_UNAVAILABLE'
                        if nodes and (not self.core or {n.key for n in nodes}!={p.key for p in self.plans.values()} or self.core.proc.poll() is not None):
                            self.maintenance = nodes
                    except Exception as e:
                        self.available = False
                        self.unavailable_kind='API_UNAVAILABLE'
                        self.event('API_UNAVAILABLE',{'inventory':type(e).__name__})
                        next_inventory = now+10
                    self.catalog = None
                if self.guest.task and self.guest.task.done():
                    self.guest.finish(self)
                if self.maintenance and not self.guest.task and not self.tasks and not self.special and not self.telemetry:
                    try:
                        self.expire_waiting(now,wall,True)
                        await self.install(self.maintenance,await asyncio.to_thread(physical_interface))
                        self.save_env(await self.environment())
                        if self.env['disk_free'] < DISK_FLOOR:
                            raise OSError('disk reserve reached')
                        next_env = now+15
                    except Exception as e:
                        self.available = False
                        self.event('API_UNAVAILABLE',{'setup':type(e).__name__})
                        next_inventory = now+10
                    self.maintenance = None
                if self.telemetry and self.telemetry.done():
                    self.save_env(self.telemetry.result())
                    self.telemetry = None
                    if self.env['disk_free'] < DISK_FLOOR:
                        raise OSError('disk reserve reached')
                if self.special and self.special.done():
                    self.finish_special()
                if self.core and not self.maintenance:
                    if now>=next_env and not self.telemetry:
                        self.telemetry = asyncio.create_task(self.environment())
                        next_env = now+15
                    if now>=next_adjust:
                        self.adjust()
                        next_adjust = now+60
                    if self.run['phase']=='formal' and now>=next_eval:
                        self.elect()
                        next_eval = now+600
                    if self.available and self.config.get('guest_enabled',True):
                        self.guest.start(self,now)
                    if self.available and self.picks and now>=next_special and not self.special and len(self.tasks)+int(bool(self.guest.task))<self.limit:
                        options = [p for p in self.plans.values() if p is not self.guest.plan and p.node in self.picks and p.node not in self.waiting and not p.active and p.cool<=now]
                        if options:
                            p = options[int(now//90)%len(options)]
                            self.special_key = p.key
                            self.special = asyncio.create_task(self.transfer(p))
                            next_special = now+90
                    if self.available:
                        self.start_gpt(now)
                    if sum(map(len,self.buckets.values()))+len(self.plans)+len(self.tasks)>=BATCH_LIMIT:
                        self.event('WRITE_BACKPRESSURE',{'bounded_rows':sum(map(len,self.buckets.values()))})
                        self.flush(wall,True)
                        self.level=min(len(RATES)-1,self.level+1)
                        self.set_rates()
                    # Setup and inventory can take seconds. Never submit using their stale admission time.
                    self.dispatch(time.monotonic(),time.time())
                self.flush(wall)
                await asyncio.sleep(.075)
        finally:
            if self.tasks:
                await asyncio.gather(*(task for _,task in self.tasks.values()),return_exceptions=True)
            try:
                self.collect()
                self.expire_waiting(time.monotonic(),time.time(),True)
                self.flush(time.time(),True)
                if self.guest.task:
                    await self.guest.task
                    self.guest.finish(self)
                if self.special:
                    await self.special
                    self.finish_special()
                if self.telemetry:
                    await self.telemetry
            finally:
                if self.core:
                    await self.core.close()

    def elect(self):
        if self.config.get('experiment_id'):
            latest = self.db.execute("""select r.* from st_run r join st_run_config c on c.run=r.id
                where r.phase='pressure' and r.state='passed' and json_extract(c.data,'$.experiment_id')=?
                order by r.id desc limit 1""",(self.config['experiment_id'],)).fetchone()
        else:
            latest = self.db.execute("select * from st_run where phase='pressure' and state='passed' order by id desc limit 1").fetchone()
        source = self.run if time.time()-self.run['start'] >= 1800 else latest
        if source is None:
            return
        rows = ranking(self.db,source)
        # Leave headroom for timing jitter and public target budgets.
        ordinary,fast=RATES[self.level]
        increment=1/fast-1/ordinary
        budget=max(0,math.floor((PER_TARGET*2*.95-len(self.plans)/ordinary)/increment)) if increment>0 else 10
        fresh = candidates([r for r in rows if r['id'] in self.plans],self.picks,min(10,budget))
        if fresh != self.picks:
            self.event('CANDIDATES',{'previous':sorted(self.picks),'current':sorted(fresh)})
            self.picks = fresh
            self.set_rates()

    async def transfer(self,p):
        from stability_transfer import small_transfer
        start = time.time()
        data = await asyncio.to_thread(small_transfer,self.core.mixed,p.key,self.core.password)
        return 'transfer',(self.run['id'],p.node,start,time.time(),json.dumps(data))

    def finish_special(self):
        kind,values=self.special.result()
        if kind=='transfer':
            self.db.execute('insert into st_transfer values(?,?,?,?,?)',values)
        else:
            self.db.execute('''update st_chatgpt set start=?,end=?,elapsed=?,status=?,http=?,tls=?,evidence=?
                               where id=?''',values)
        self.db.commit()
        self.special=self.special_key=None

    def start_gpt(self,now):
        if not self.config.get('chatgpt_enabled',True):
            return
        if self.special or now<self.gpt_global or len(self.tasks)+int(bool(self.guest and self.guest.task))>=self.limit:
            return
        options=[n for n,due in self.gpt_due.items() if due<=now and not (self.guest and self.guest.plan is self.plans[n]) and n not in self.waiting and not self.plans[n].active and self.plans[n].cool<=now]
        if not options:
            return
        n=min(options,key=self.gpt_due.get)
        p=self.plans[n]
        due=self.gpt_due[n]
        slot=due+math.floor((now-due)/gpt.INTERVAL)*gpt.INTERVAL
        wall=time.time()
        key=self.db.execute("""insert into st_chatgpt(run,node,slot,start,status,env,tls_limit_s)
            values(?,?,?,?,'IN_PROGRESS',?,?)""",(self.run['id'],n,wall-(now-slot),wall,self.env_id,gpt.TLS_LIMIT_S)).lastrowid
        self.db.commit()
        self.gpt_due[n]=slot+gpt.INTERVAL
        self.gpt_global=now+gpt.GLOBAL_SPACING
        self.special_key=p.key
        self.special=asyncio.create_task(self.measure_gpt(p,key))

    async def measure_gpt(self,p,key):
        data=await gpt.probe(self.core.mixed,p.key,self.core.password)
        if data['status']=='RATE_LIMITED' or data.get('http')==429:
            self.gpt_global=max(self.gpt_global,time.monotonic()+data.get('retry_after_s',1800))
        if data['status']=='CHALLENGE' or data.get('cf_challenge'):
            self.gpt_due[p.node]=max(self.gpt_due[p.node],time.monotonic()+3600)
        if data['status'] in ('TIMEOUT','TRANSPORT_ERROR'):
            p.cool=time.monotonic()+3.25
        return 'chatgpt',(data['start'],data['end'],data['elapsed'],data['status'],data['http'],int(data['tls']),json.dumps(data),key)
