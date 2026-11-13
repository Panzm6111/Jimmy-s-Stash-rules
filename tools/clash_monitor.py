"""Bounded, passive Clash Verge usage recorder. No core writes or active probes.

All collected data belongs in ignored .local, never in public research artifacts.
Times in reports use UTC+8, independently of Windows' timezone.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import queue
import re
import sqlite3
import threading
import time

import yaml
from mihomo_readonly import CoreClient, ROOT as APP_ROOT

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.local' / 'clash-monitor'
TZ = timezone(timedelta(hours=8))
AI_ROOTS = ('Jimmy · 海外AI', 'Jimmy · ai')
GROUP_TYPES = {'Selector', 'URLTest', 'Fallback', 'LoadBalance', 'Relay'}
DIRECT = {'DIRECT', 'REJECT', 'REJECT-DROP', 'PASS', 'COMPATIBLE'}
AI_DOMAINS = ('openai.com', 'chatgpt.com', 'oaistatic.com', 'oaiusercontent.com',
              'anthropic.com', 'claude.ai', 'gemini.google.com', 'generativelanguage.googleapis.com',
              'aistudio.google.com', 'grok.com', 'x.ai', 'perplexity.ai', 'deepseek.com')


def stamp(t): return datetime.fromtimestamp(t, TZ).isoformat(timespec='seconds')
def digest(obj): return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:20]
def ai_service(host):
    host = host.lower().rstrip('.')
    return any(host == d or host.endswith('.' + d) for d in AI_DOMAINS)


def resolve(groups, root):
    path, seen = [], set()
    while root and root not in seen:
        path.append(root); seen.add(root)
        if root not in groups: break
        root = groups[root].get('now')
    return path


def node_health(node, url=''):
    record = node.get('extra', {}).get(url) if url else None
    exact = record is not None
    if record is None: record = node
    history = record.get('history') or []
    last = history[-1] if history else {}
    return {'alive': record.get('alive'), 'delay_ms': last.get('delay'),
            'probe_at': last.get('time'), 'exact_test_url': exact}


def transition_state(old, new, before_groups, groups, before_nodes, nodes):
    """Preserve only used-node positions, not full unused pool membership."""
    states=[]
    for name in dict.fromkeys(old[:-1]+new[:-1]):
        if name not in before_groups and name not in groups:continue
        versions=[]
        for source in (before_groups,groups):
            group=source.get(name,{})
            members=group.get('all') or []
            versions.append({'type':group.get('type'),'now':group.get('now'),'fixed':group.get('fixed'),
                'member_count':len(members),'old_node_index':members.index(old[-1]) if old[-1] in members else None,
                'new_node_index':members.index(new[-1]) if new[-1] in members else None,
                'tolerance_ms':group.get('monitor_tolerance')})
        states.append({'group':name,'before':versions[0],'after':versions[1]})
    url=next((groups.get(g,before_groups.get(g,{})).get('testUrl') for g in reversed(old[:-1])
              if groups.get(g,before_groups.get(g,{})).get('testUrl')),'')
    return {'schema':1,'group_states':states,
        'old_health_before':node_health(before_nodes.get(old[-1],{}),url),
        'old_health_after':node_health(nodes.get(old[-1],before_nodes.get(old[-1],{})),url),
        'new_health_after':node_health(nodes.get(new[-1],{}),url),
        'meaning':'API observations around transition, not internal branch or user/API actor attribution'}


def classify_switch(old, new, before_groups, groups, before_nodes, nodes, recent_errors, context_changed):
    if context_changed:
        return {'reason': 'context_changed', 'certainty': 'observed', 'detail': '配置、内核或网络上下文改变，不能归为节点质量问题'}
    changed = next((g for g in old[:-1] if g in groups and
                    before_groups.get(g, {}).get('now') != groups[g].get('now')), None)
    if changed is None:
        return {'reason': 'unknown', 'certainty': 'unknown', 'detail': '观测到出口变化，未取得足够触发证据'}
    g, prev = groups[changed], before_groups.get(changed, {})
    common = {'trigger_group': changed, 'group_type': g.get('type')}
    if g.get('type') == 'Selector':
        return {**common, 'reason': 'selection_changed', 'certainty': 'observed',
                'detail': '选择入口改变；无法区分手动操作与其他API调用'}
    if prev.get('fixed') != g.get('fixed'):
        return {**common, 'reason': 'fixed_selection_changed', 'certainty': 'observed', 'detail': '自动池的API固定选择发生变化'}
    old_name, new_name = old[-1], new[-1]
    if old_name not in g.get('all', []):
        return {**common, 'reason': 'node_removed', 'certainty': 'observed', 'detail': '原节点已不在该池成员列表'}
    url = g.get('testUrl', '')
    old_health = node_health(nodes.get(old_name, before_nodes.get(old_name, {})), url)
    new_health = node_health(nodes.get(new_name, {}), url)
    evidence = {**common, 'old_health': old_health, 'new_health': new_health}
    if old_health['alive'] is False:
        return {**evidence, 'reason': 'health_failure', 'certainty': 'inferred', 'detail': '与原节点内置探测不可用一致；不是内核给出的触发原因'}
    a, b = old_health['delay_ms'], new_health['delay_ms']
    tolerance = g.get('monitor_tolerance')
    if g.get('type') == 'URLTest' and tolerance is not None and old_health['exact_test_url'] and new_health['exact_test_url'] and a and b and a > b + tolerance:
        return {**evidence, 'reason': 'latency_advantage', 'certainty': 'inferred',
                'detail': '新节点探测延迟优势超过已读取容差；不代表实际带宽更高', 'tolerance_ms': tolerance}
    if recent_errors:
        return {**evidence, 'reason': 'nearby_dial_errors', 'certainty': 'correlated', 'detail': '切换前后附近有建连错误，仅时间相关'}
    return {**evidence, 'reason': 'unknown', 'certainty': 'unknown', 'detail': '无足够证据区分健康刷新、手动固定或其他原因'}


def parse_log(message, groups):
    """Discard original text immediately; persist only allowlisted categories/names."""
    text = message.get('payload', '')
    match = re.match(r'^\[(TCP|UDP)\] ', text)
    if not match: return None
    protocol = match[1]
    error = ' error: ' in text and ' dial ' in text
    target = re.search(r' --> (\S+)', text)
    service = ai_service(target[1].rsplit(':', 1)[0]) if target else False
    if not error:
        m = re.search(r' using (.+)$', text)
        if not m: return None
        chain = m[1]
        # Mihomo renders outermost-group[innermost-node], omitting middle groups.
        if chain.endswith(']') and '[' in chain:
            group, leaf = chain.split('[', 1); leaf = leaf[:-1]
        else: group, leaf = chain, chain
        if leaf in DIRECT or '订阅更新' in group: return None
        return {'kind': 'connection_open', 'group': group, 'node': leaf, 'protocol': protocol,
                'scope': 'AI' if service or 'AI' in group or group.endswith(' · ai') else '其他代理',
                'attribution': 'logged_chain'}
    group = next((g for g in sorted(groups, key=len, reverse=True)
                  if text.startswith('[' + protocol + '] dial ' + g + ' ')), None)
    if group is None or '订阅更新' in group: return None
    path = resolve(groups, group)
    if not path or path[-1] in DIRECT: return None
    lower = text.lower()
    category = next((name for pattern, name in [
        (r'dns|lookup |no such host|resolv', 'dns'),
        (r'tls|certificate|handshake', 'tls'),
        (r'timeout|deadline exceeded|timed out', 'timeout'),
        (r'refused', 'refused'), (r'reset|broken pipe|eof', 'reset_or_eof'),
        (r'unreachable|no route', 'unreachable')]
        if re.search(pattern, lower)), 'other')
    return {'kind': 'dial_error', 'group': group, 'node': path[-1], 'protocol': protocol,
            'scope': 'AI' if service or any('AI' in x or x.endswith(' · ai') for x in path) else '其他代理',
            'category': category, 'attribution': 'selection_near_log_time_not_confirmed_node'}


def network_signature():
    """Hash only up physical adapter identities/addresses; never save IPs or MACs."""
    import ctypes as c
    from ctypes import wintypes as w
    class SocketAddress(c.Structure):
        _fields_ = [('address', c.c_void_p), ('length', c.c_int)]
    class Unicast(c.Structure): pass
    Unicast._fields_ = [('alignment', c.c_uint64), ('next', c.POINTER(Unicast)), ('socket', SocketAddress)]
    class Adapter(c.Structure): pass
    Adapter._fields_ = [('alignment', c.c_uint64), ('next', c.POINTER(Adapter)), ('name', c.c_char_p),
        ('unicast', c.POINTER(Unicast)), ('anycast', c.c_void_p), ('multicast', c.c_void_p), ('dns', c.c_void_p),
        ('suffix', w.LPWSTR), ('description', w.LPWSTR), ('friendly', w.LPWSTR), ('physical', c.c_ubyte * 8),
        ('physical_length', w.ULONG), ('flags', w.ULONG), ('mtu', w.ULONG), ('kind', w.ULONG), ('status', c.c_int)]
    lib = c.WinDLL('iphlpapi')
    size = w.ULONG(32768); buffer = c.create_string_buffer(size.value)
    result = lib.GetAdaptersAddresses(0, 14, None, buffer, c.byref(size))
    if result == 111:
        buffer = c.create_string_buffer(size.value)
        result = lib.GetAdaptersAddresses(0, 14, None, buffer, c.byref(size))
    if result: return {'signature': 'unavailable', 'types': []}
    ptr = c.cast(buffer, c.POINTER(Adapter)); identities, kinds = [], set()
    while ptr:
        a = ptr.contents
        if a.status == 1 and a.kind in (6, 71, 243, 244):
            addresses, u = [], a.unicast
            while u:
                addr = u.contents.socket
                if addr.address and addr.length > 0: addresses.append(c.string_at(addr.address, addr.length).hex())
                u = u.contents.next
            identities.append([a.name.decode(errors='replace'), sorted(addresses)])
            kinds.add({6: 'Ethernet', 71: 'Wi-Fi', 243: 'Cellular', 244: 'Cellular'}[a.kind])
        ptr = a.next
    return {'signature': digest(sorted(identities)), 'types': sorted(kinds)}


SCHEMA = '''
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,at REAL,kind TEXT,payload TEXT);
CREATE INDEX IF NOT EXISTS event_time ON events(at);
CREATE TABLE IF NOT EXISTS minutes(minute INTEGER,node TEXT,scope TEXT,context TEXT,
 selected_s REAL DEFAULT 0,active_s REAL DEFAULT 0,down INTEGER DEFAULT 0,up INTEGER DEFAULT 0,
 seen INTEGER DEFAULT 0,opens INTEGER DEFAULT 0,errors INTEGER DEFAULT 0,
 PRIMARY KEY(minute,node,scope,context));
CREATE TABLE IF NOT EXISTS coverage(minute INTEGER PRIMARY KEY,api_s REAL DEFAULT 0,log_s REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS health(epoch TEXT,node TEXT,scope TEXT,probe_at TEXT,at REAL,delay REAL,alive INTEGER,
 PRIMARY KEY(epoch,node,scope,probe_at));
'''


class Store:
    def __init__(self, folder):
        self.folder = Path(folder); self.db = sqlite3.connect(self.folder / 'monitor.sqlite')
        self.db.execute('PRAGMA journal_mode=WAL'); self.db.execute('PRAGMA busy_timeout=5000')
        self.db.executescript(SCHEMA); self.db.commit()
    def event(self, at, kind, **payload):
        self.db.execute('INSERT INTO events(at,kind,payload) VALUES(?,?,?)', (at, kind, json.dumps(payload, ensure_ascii=False)))
    def metric(self, at, node, scope, context, **values):
        # Split interval time before calling if it crosses a minute boundary.
        minute = int(at // 60) * 60
        self.db.execute('INSERT OR IGNORE INTO minutes(minute,node,scope,context) VALUES(?,?,?,?)', (minute,node,scope,context))
        if not values: return
        assert set(values) <= {'selected_s','active_s','down','up','seen','opens','errors'}
        self.db.execute('UPDATE minutes SET ' + ','.join(k+'='+k+'+?' for k in values) +
                        ' WHERE minute=? AND node=? AND scope=? AND context=?', (*values.values(),minute,node,scope,context))
    def interval(self, start, end, **values):
        while start < end:
            finish = min(end, (int(start//60)+1)*60)
            self.metric(start, **{k:v for k,v in values.items() if k not in ('selected_s','active_s')},
                        **{k:finish-start for k in values if k in ('selected_s','active_s')})
            start = finish
    def coverage(self, start, end, log_on):
        while start < end:
            finish = min(end, (int(start//60)+1)*60); delta = finish-start; minute=int(start//60)*60
            self.db.execute('INSERT OR IGNORE INTO coverage(minute) VALUES(?)',(minute,))
            self.db.execute('UPDATE coverage SET api_s=api_s+?,log_s=log_s+? WHERE minute=?',(delta,delta if log_on else 0,minute))
            start=finish
    def close(self): self.db.commit(); self.db.close()


def report(folder):
    from clash_monitor_report import render
    render(Path(folder))


class Recorder:
    def __init__(self, session):
        self.session = session; self.folder = Path(session['folder']); self.store = Store(self.folder)
        self.stop = threading.Event(); self.client = CoreClient(stop=self.stop)
        self.queue = queue.Queue(maxsize=10000); self.log_online = False; self.log_dropped=0
        self.groups = {}; self.nodes = {}; self.paths = {}; self.previous_connections = {}
        self.recent_groups = {}; self.recent_errors = {}; self.last = None; self.context = ''; self.epoch = ''
        self.node_first_seen = {}; self.health_since=session['start']
        self.last_meta=0; self.last_report=0; self.last_commit=0; self.meta={}; self.offline=False

    def logs_worker(self):
        while not self.stop.is_set():
            try:
                for raw in self.client.logs():
                    self.log_online=True
                    event=parse_log(raw,self.groups)
                    if event:
                        try:self.queue.put_nowait((time.time(),event))
                        except queue.Full:self.log_dropped+=1
            except Exception:
                pass
            self.log_online=False
            self.stop.wait(1)

    def metadata(self, now):
        config=self.client.get('/configs');version=self.client.get('/version')['version']
        p=yaml.safe_load((APP_ROOT/'profiles.yaml').read_text(encoding='utf-8'))
        uid=p.get('current'); profile=next((i.get('name') or i.get('file') for i in p.get('items',[]) if i.get('uid')==uid),'unknown')
        runtime_path=APP_ROOT/'clash-verge.yaml';runtime=yaml.safe_load(runtime_path.read_text(encoding='utf-8'))
        tolerance={g['name']:g.get('tolerance') for g in runtime.get('proxy-groups',[])}
        meta={'profile':profile,'mode':config.get('mode'),'log_level':config.get('log-level'),'tun':config.get('tun',{}).get('enable'),
              'core':version,'network':network_signature()}
        epoch=digest([self.client.identity(),runtime_path.stat().st_mtime_ns,uid])
        context=digest([meta,epoch])
        changed=bool(self.meta and (meta!=self.meta or epoch!=self.epoch))
        if meta!=self.meta or epoch!=self.epoch:self.store.event(now,'context',**meta,epoch=epoch,context=context)
        self.meta,self.epoch,self.context,self.tolerance=meta,epoch,context,tolerance
        self.last_meta=now
        return changed

    def poll(self, now):
        pipe_before=self.client.identity()
        changed=self.metadata(now) if now-self.last_meta>=15 else False
        gap=self.last is not None and now-self.last>self.session['poll_seconds']*3
        continuity=self.last is not None and not gap and not changed and not self.offline
        proxies=self.client.get('/proxies')['proxies']
        providers=self.client.get('/providers/proxies').get('providers',{})
        nodes={n['name']:n for p in providers.values() for n in p.get('proxies',[])}
        nodes.update({k:v for k,v in proxies.items() if v.get('type') not in GROUP_TYPES})
        groups={k:dict(v,monitor_tolerance=self.tolerance.get(k)) for k,v in proxies.items() if v.get('type') in GROUP_TYPES}
        connections=self.client.get('/connections').get('connections') or []
        if self.client.identity()!=pipe_before:raise OSError('Core changed during read sample')
        current={};active=set();watched={};old_groups=self.groups
        for c in connections:
            chain=c.get('chains') or []
            if not chain or chain[0] in DIRECT or any('订阅更新' in x for x in chain):continue
            host=c.get('metadata',{}).get('host','')
            if host in ('www.gstatic.com','cp.cloudflare.com'):continue
            group=next((g for g in reversed(chain) if g in groups),None)
            if group:self.recent_groups[group]=now
            scope='AI' if ai_service(host) or any('AI' in x or x.endswith(' · ai') for x in chain) else '其他代理'
            node=chain[0];active.add((node,scope));cid=c['id']
            previous=self.previous_connections.get(cid) if continuity else None
            # First sight of an existing connection contributes no historical bytes.
            down=max(0,c.get('download',0)-previous['download']) if previous else 0
            up=max(0,c.get('upload',0)-previous['upload']) if previous else 0
            self.store.metric(now,node,scope,self.context,down=down,up=up,seen=0 if previous else 1)
            current[cid]={'download':c.get('download',0),'upload':c.get('upload',0)}
            watched[(node,scope)]=''
        roots={r for r in AI_ROOTS if r in groups}
        roots.update(g for g,t in self.recent_groups.items() if now-t<120 and g in groups)
        paths={r:resolve(groups,r) for r in roots}
        if gap:self.store.event(now,'coverage_gap',start=stamp(self.last),end=stamp(now),seconds=now-self.last,reason='sleep_or_unobserved')
        for root,path in paths.items():
            prior=self.paths.get(root)
            if prior is not None and path!=prior:
                evidence=classify_switch(prior,path,old_groups,groups,self.nodes,nodes,
                    any(now-t<90 for g,t in self.recent_errors.items() if g in prior),changed or not continuity)
                self.store.event(now,'node_switch' if prior[-1]!=path[-1] else 'route_change',
                    group=root,old_path=prior,new_path=path,**evidence,
                    state_evidence=transition_state(prior,path,old_groups,groups,self.nodes,nodes))
            elif prior is None:self.store.event(now,'selection_baseline',group=root,path=path)
        # Track AI business route even when idle. The ai pool is also watched separately as events.
        ai_path=paths.get(AI_ROOTS[0]) or paths.get(AI_ROOTS[1])
        if ai_path and ai_path[-1] not in DIRECT:
            node=ai_path[-1];watched[(node,'AI')]=next((groups[g].get('testUrl','') for g in reversed(ai_path[:-1]) if groups[g].get('testUrl')), '')
            if continuity:self.store.interval(self.last,now,node=node,scope='AI',context=self.context,selected_s=True)
        for node,scope in active:
            if continuity:self.store.interval(self.last,now,node=node,scope=scope,context=self.context,active_s=True)
        for (node,scope),url in watched.items():
            first_seen=self.node_first_seen.setdefault((node,scope),now)
            h=node_health(nodes.get(node,{}),url)
            if h['probe_at']:
                try:at=datetime.fromisoformat(h['probe_at']).timestamp()
                except ValueError:continue
                # Do not import pre-monitor history or use unrelated/stale probes as new samples.
                if at<max(self.health_since,first_seen) or at>now+10:continue
                self.store.db.execute('INSERT OR IGNORE INTO health VALUES(?,?,?,?,?,?,?)',
                    (self.epoch,node,scope,h['probe_at'],at,h['delay_ms'],h['alive']))
        if continuity:self.store.coverage(self.last,now,self.log_online)
        if self.offline:self.store.event(now,'core_available_again')
        self.offline=False;self.last=now;self.groups=groups;self.nodes=nodes;self.paths=paths
        self.previous_connections=current
        return len(active)

    def drain(self):
        while True:
            try:at,event=self.queue.get_nowait()
            except queue.Empty:break
            if event['kind']=='connection_open':
                self.store.metric(at,event['node'],event['scope'],self.context,opens=1)
            else:
                self.store.metric(at,event['node'],event['scope'],self.context,errors=1)
                self.recent_errors[event['group']]=at
                self.store.event(at,'dial_error',**{k:v for k,v in event.items() if k!='kind'})
            self.recent_groups[event['group']]=at
        if self.log_dropped:
            self.store.event(time.time(),'log_queue_overflow',dropped=self.log_dropped);self.log_dropped=0

    def run(self):
        worker=threading.Thread(target=self.logs_worker,daemon=True);worker.start()
        first_start=self.store.db.execute("SELECT min(at) FROM events WHERE kind='recorder_start'").fetchone()[0]
        self.health_since=max(self.session['start'],first_start or time.time())
        prior_path=self.folder/'status.json'
        if prior_path.exists():
            try:
                prior=json.loads(prior_path.read_text(encoding='utf-8'))
                last=datetime.fromisoformat(prior['updated']).timestamp()
                if time.time()-last>self.session['poll_seconds']*3:
                    self.store.event(time.time(),'coverage_gap',start=stamp(last),end=stamp(time.time()),
                                     seconds=time.time()-last,reason='recorder_not_running_or_sleep')
            except (ValueError,KeyError):pass
        self.store.event(time.time(),'recorder_start',pid=os.getpid(),deadline=stamp(self.session['end']))
        try:
            while time.time()<self.session['end'] and not (self.folder/'stop.request').exists():
                start=time.time();active=0
                try:active=self.poll(start)
                except Exception as e:
                    if not self.offline:self.store.event(start,'core_unavailable',error_type=type(e).__name__,
                        errno=getattr(e,'errno',None),meaning='control_read_failed_not_proof_of_core_or_node_failure')
                    self.offline=True;self.previous_connections={}
                self.drain()
                if start-self.last_commit>=30:self.store.db.commit();self.last_commit=start
                state={'status':'collecting','pid':os.getpid(),'updated':stamp(start),'deadline':stamp(self.session['end']),
                       'core_available':not self.offline,'log_stream_online':self.log_online,
                       'active_node_scope_pairs':active,'ai_routes':{r:p for r,p in self.paths.items() if r in AI_ROOTS},'context':self.meta}
                write_json(self.folder/'status.json',state)
                if start-self.last_report>=300:
                    self.store.db.commit()
                    try:report(self.folder)
                    except Exception as e:self.store.event(start,'report_error',error_type=type(e).__name__)
                    self.last_report=start
                    if sum(p.stat().st_size for p in self.folder.glob('monitor.sqlite*'))>self.session['max_db_bytes']:
                        self.store.event(start,'storage_limit');(self.folder/'stop.request').write_text('storage_limit',encoding='utf-8');break
                self.stop.wait(max(0,self.session['poll_seconds']-(time.time()-start)))
        finally:
            self.stop.set();worker.join(timeout=2);self.drain()
            ended=time.time();self.store.event(ended,'recorder_stop',deadline_reached=ended>=self.session['end'])
            self.store.close();report(self.folder)
            write_json(self.folder/'status.json',{'status':'completed' if ended>=self.session['end'] else 'stopped',
                'updated':stamp(ended),'deadline':stamp(self.session['end']),'pid':None})


def write_json(path, data):
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(path)


def create_session(days):
    if not 3<=days<=5:raise ValueError('Monitoring duration must be 3 to 5 days')
    now=time.time();folder=LOCAL/datetime.fromtimestamp(now,TZ).strftime('%Y%m%d-%H%M%S');folder.mkdir(parents=True)
    data={'version':1,'start':now,'end':now+days*86400,'folder':str(folder),'poll_seconds':5,
          'max_db_bytes':250*1024*1024,'timezone':'Asia/Shanghai','days':days,
          'passive_only':True,'public_configuration_changed':False}
    write_json(folder/'session.json',data);LOCAL.mkdir(exist_ok=True);write_json(LOCAL/'current.json',{'session':str(folder/'session.json')})
    Store(folder).close();report(folder)
    return folder/'session.json'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['create','run','report','status','stop','mark'])
    parser.add_argument('--session',type=Path);parser.add_argument('--days',type=int,default=5)
    parser.add_argument('--kind',choices=['stall','disconnect','good'],default='stall');args=parser.parse_args()
    if args.command=='create':print(create_session(args.days));return
    session_path=args.session or Path(json.loads((LOCAL/'current.json').read_text(encoding='utf-8'))['session'])
    data=json.loads(session_path.read_text(encoding='utf-8'));folder=Path(data['folder'])
    if args.command=='run':
        if time.time()>=data['end'] or (folder/'stop.request').exists():return
        import msvcrt
        with (folder/'recorder.lock').open('a+b') as lock:
            lock.seek(0);lock.write(b'1');lock.flush();lock.seek(0)
            try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
            except OSError:return
            Recorder(data).run()
    elif args.command=='report':report(folder);print(folder/'report.html')
    elif args.command=='status':
        print((folder/'status.json').read_text(encoding='utf-8') if (folder/'status.json').exists() else 'Not started')
    elif args.command=='stop':(folder/'stop.request').touch();print('Stop requested; recorder will flush and exit.')
    elif args.command=='mark':
        store=Store(folder);store.event(time.time(),'user_experience',experience=args.kind);store.close();report(folder)
        print('Experience marker saved at '+stamp(time.time()))


if __name__=='__main__':main()
