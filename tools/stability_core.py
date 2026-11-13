"""Private measurement core. Production controller only supplies inventory."""
import asyncio
import ctypes
import hashlib
import http.client
import hmac
import json
import os
import re
import secrets
import socket
import subprocess
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import aiohttp
import psutil
import yaml

from mihomo_readonly import CoreClient, ROOT

TARGETS = ('https://www.gstatic.com/generate_204', 'https://cp.cloudflare.com/generate_204')
BASE = Path(__file__).resolve().parents[1]
PRIVATE = BASE / '.local' / 'stability'
EXCLUDED = {'direct', 'reject', 'rejectdrop', 'selector', 'urltest', 'fallback',
            'loadbalance', 'relay', 'dns', 'pass', 'compatible'}
NOTICE = re.compile(r'^(?:剩余流量\s*[:：]|距离下次重置剩余|套餐到期\s*[:：]|跳转域名[（(]?请勿连接)')
verified_notice_providers = set()


def notice_labels(rows):
    """Require multiple account notices sharing identical adapter settings, not just a keyword."""
    groups={}
    for row in rows:
        signature=json.dumps({k:v for k,v in row.items() if k!='name'},sort_keys=True)
        groups.setdefault(signature,[]).append(row['name'])
    return {n for labels in groups.values() if sum(bool(NOTICE.match(n)) for n in labels)>=2
            for n in labels if NOTICE.match(n)}


@dataclass
class Node:
    key: str
    provider: str
    name: str
    kind: str
    config: dict


def project_nodes(provider, exposed, rows, salt):
    counts = Counter(row.get('name') for row in rows)
    visible = [p for p in exposed if p['type'].lower() not in EXCLUDED and 'all' not in p]
    names = Counter(p['name'] for p in visible)
    by_name = {p['name']: p for p in rows}
    result = []
    for p in visible:
        name = p['name']
        if counts[name] != 1 or names[name] != 1:
            raise ValueError('ambiguous or missing provider identity')
        row = by_name[name]
        raw_kind=str(row.get('type','')).lower()
        aliases={'ss':'shadowsocks','ssr':'shadowsocksr','socks5':'socks5'}
        if aliases.get(raw_kind,raw_kind)!=p['type'].lower() and raw_kind!=p['type'].lower():
            raise ValueError('provider adapter type mismatch')
        if row.get('dialer-proxy') or row.get('interface-name'):
            raise ValueError('chained or interface-specific exit requires review')
        identity = json.dumps([provider, name, p['type'], row], sort_keys=True, ensure_ascii=False)
        key = hmac.new(salt, identity.encode(), hashlib.sha256).hexdigest()[:32]
        result.append(Node(key, provider, name, p['type'], dict(row, name=key)))
    return result


def inventory(salt, source=None):
    return inventory_snapshot(salt, source)[0]


def profile_source(name):
    """Resolve one already imported subscription, without downloading or activating it."""
    cfg = yaml.safe_load((ROOT/'profiles.yaml').read_bytes())
    matches = [p for p in cfg.get('items',[]) if p.get('name') == name and p.get('type') == 'remote']
    if len(matches) != 1:
        raise ValueError('expected exactly one installed subscription with this name')
    return {'kind':'installed-profile','uid':matches[0]['uid'],'name':name}


def profile_inventory(salt, source):
    if source.get('kind') != 'installed-profile':
        raise ValueError('unsupported inventory source')
    cfg = yaml.safe_load((ROOT/'profiles.yaml').read_bytes())
    matches = [p for p in cfg.get('items',[]) if p.get('uid') == source['uid']
               and p.get('name') == source['name'] and p.get('type') == 'remote']
    if len(matches) != 1:
        raise ValueError('bound installed subscription missing or renamed')
    folder = (ROOT/'profiles').resolve()
    path = (folder/matches[0]['file']).resolve()
    if not path.is_relative_to(folder):
        raise ValueError('unexpected installed subscription path')
    config = yaml.safe_load(path.read_bytes())
    if config.get('proxy-providers') or config.get('interface-name') or config.get('routing-mark'):
        raise ValueError('profile requires provider or interface review')
    rows = config.get('proxies') or []
    notices = notice_labels(rows)
    rows = [r for r in rows if r.get('name') not in notices]
    if not rows:
        raise ValueError('installed subscription has no exits')
    aliases = {'ss':'Shadowsocks','ssr':'ShadowsocksR'}
    exposed = [{'name':r['name'],'type':aliases.get(r['type'],r['type'])} for r in rows]
    nodes = project_nodes(source['name'],exposed,rows,salt)
    if len(nodes) != len(rows):
        raise ValueError('installed subscription contains non-exit entries')
    return nodes,[]


def live_get(client,endpoint):
    try:
        return client.get(endpoint)
    except OSError:
        # Client builds may expose a loopback TCP controller instead of a pipe.
        cfg=yaml.safe_load((ROOT/'clash-verge.yaml').read_bytes())
        addr=cfg.get('external-controller') or ''
        host,sep,port_text=addr.rpartition(':')
        if host not in ('127.0.0.1','[::1]') or not sep or not port_text.isdecimal():
            raise
        conn=http.client.HTTPConnection(host.strip('[]'),int(port_text),timeout=5)
        try:
            conn.request('GET',endpoint,headers={'Authorization':'Bearer '+cfg.get('secret','')})
            res=conn.getresponse()
            if res.status!=200:
                raise OSError('loopback controller rejected inventory')
            body=res.read(16*1024*1024+1)
            if len(body)>16*1024*1024:
                raise ValueError('oversized controller inventory')
            return json.loads(body)
        finally:
            conn.close()


def cached_generation_matches(exposed,rows):
    cached_names={r['name'] for r in rows}
    return all(p['name'] in cached_names for p in exposed if 'all' not in p and p['type'].lower() not in EXCLUDED)


def inventory_snapshot(salt, source=None):
    if source is not None:
        return profile_inventory(salt,source)
    client = CoreClient()
    providers = live_get(client,'/providers/proxies')['providers']
    cfg = yaml.safe_load((ROOT / 'clash-verge.yaml').read_bytes())
    result = []
    issues = []
    for name, source in (cfg.get('proxy-providers') or {}).items():
        try:
            if source.get('override'):
                raise ValueError('unsupported provider override')
            if source.get('type') == 'inline':
                rows = source['payload']
            else:
                path = (ROOT / source['path']).resolve()
                if not path.is_relative_to(ROOT.resolve()):
                    raise ValueError('unexpected provider cache path')
                rows = yaml.safe_load(path.read_bytes())['proxies']
            exposed=providers[name]['proxies']
            # Use the client's installed provider bytes. Re-fetching a subscription
            # can produce a different TLS fingerprint even under the same display name.
            # Dynamic quota labels are generation witnesses, never measured exits.
            if not cached_generation_matches(exposed,rows):
                issues.append({'provider':name,'reason':'inventory differs; continue matching installed nodes by name'})
            notices=notice_labels(rows)
            if notices:
                verified_notice_providers.add(name)
            counts=Counter(row['name'] for row in exposed)
            for proxy in exposed:
                if proxy['name'] in notices or (notices and NOTICE.match(proxy['name'])):
                    continue
                try:
                    if counts[proxy['name']]!=1:
                        raise ValueError('ambiguous live name')
                    result.extend(project_nodes(name,[proxy],rows,salt))
                except (ValueError,KeyError,TypeError):
                    issues.append({'provider':name,'node':proxy['name'],'reason':'ambiguous or unsupported identity'})
        except (KeyError,ValueError,TypeError,OSError,yaml.YAMLError) as e:
            issues.append({'provider':name,'reason':type(e).__name__})
    if cfg.get('proxies'):
        live = live_get(client,'/proxies')['proxies']
        result.extend(project_nodes('(inline)', [live[p['name']] for p in cfg['proxies']],
                                    cfg['proxies'], salt))
    return result,issues


def physical_interface():
    command = ("$p=@(Get-NetAdapter -Physical | Where-Object Status -eq Up | "
               "Where-Object { Get-NetRoute -InterfaceIndex $_.ifIndex -DestinationPrefix '0.0.0.0/0' "
               "-ErrorAction SilentlyContinue }); if ($p.Count -eq 1) { "
               "[Console]::OutputEncoding=[Text.UTF8Encoding]::new(); $p[0].Name }")
    name = subprocess.check_output(['powershell', '-NoProfile', '-Command', command],
                                   creationflags=subprocess.CREATE_NO_WINDOW, timeout=20).decode().strip()
    if not name:
        raise OSError('physical uplink ambiguous or unavailable')
    return name


def port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def lifetime_job(proc):
    """Terminate only our isolated child when the Python process exits."""
    from ctypes import wintypes as w
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    k.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
    k.CreateJobObjectW.restype = w.HANDLE
    k.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
    k.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
    k.CloseHandle.argtypes = [w.HANDLE]
    job = k.CreateJobObjectW(None, None)
    # JOBOBJECT_EXTENDED_LIMIT_INFORMATION for 64-bit Windows.
    if ctypes.sizeof(ctypes.c_void_p) != 8:
        raise RuntimeError('64-bit Python required')
    info = ctypes.create_string_buffer(144)
    ctypes.c_uint32.from_buffer(info, 16).value = 0x2000
    if not (job and k.SetInformationJobObject(job, 9, info, len(info))
            and k.AssignProcessToJobObject(job, int(proc._handle))):
        k.CloseHandle(job)
        raise OSError('cannot bind lifetime of isolated core')
    return lambda: k.CloseHandle(job)


class Sidecar:
    def __init__(self, nodes, interface):
        self.nodes = nodes
        self.interface = interface
        self.api, self.mixed = port(), port()
        while self.api == self.mixed:
            self.mixed = port()
        self.token, self.password = secrets.token_hex(24), secrets.token_hex(24)
        self.proc = self.job = self.session = None

    async def start(self):
        directory = PRIVATE / 'core'
        directory.mkdir(parents=True, exist_ok=True)
        clients = [n.key for n in self.nodes] + ['baseline']
        cfg = {'external-controller': f'127.0.0.1:{self.api}', 'secret': self.token,
               'mixed-port': self.mixed, 'bind-address': '127.0.0.1', 'allow-lan': False,
               'ipv6': False, 'interface-name': self.interface, 'unified-delay': False,
               'log-level': 'silent', 'profile': {'store-selected': False},
               'authentication': [f'{key}:{self.password}' for key in clients],
               'proxies': [n.config for n in self.nodes],
               'rules': [f'IN-USER,{n.key},{n.key}' for n in self.nodes]
                        + ['IN-USER,baseline,DIRECT', 'MATCH,REJECT']}
        exe = next(Path(p.exe()).parent / 'verge-mihomo.exe'
                   for p in psutil.process_iter(['name']) if p.info['name'] == 'clash-verge.exe')
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith('CLASH_')}
        self.proc = subprocess.Popen([str(exe), '-d', str(directory), '-f', '-'], stdin=subprocess.PIPE,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            self.job = lifetime_job(self.proc)
            self.proc.stdin.write(json.dumps(cfg, ensure_ascii=False).encode())
            self.proc.stdin.close()
            self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=36),
                timeout=aiohttp.ClientTimeout(total=5), trust_env=False)
            for _ in range(60):
                if self.proc.poll() is not None:
                    break
                try:
                    status, data = await self.get('/version')
                    if status == 200 and data.get('meta'):
                        return
                except aiohttp.ClientConnectionError:
                    pass
                await asyncio.sleep(.1)
            raise RuntimeError('isolated core startup failed')
        except BaseException:
            await self.close()
            raise

    async def close(self):
        if self.session:
            await self.session.close()
        if self.proc and self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait(timeout=5)
        if self.job:
            self.job()
            self.job = None

    async def get(self, path, params=None):
        async with self.session.get(f'http://127.0.0.1:{self.api}'+path, params=params,
                                    headers={'Authorization': 'Bearer '+self.token}) as res:
            return res.status, await res.json(content_type=None)

    async def probe(self, key, target):
        """The v1.19.33 delay endpoint returns a delay even for unexpected HTTP status."""
        url = TARGETS[target]
        path = '/proxies/' + quote(key, safe='')
        try:
            code, data = await self.get(path+'/delay', {'url': url, 'timeout': 3000, 'expected': 204})
            if code == 200 and data.get('delay', 0) > 0:
                check, node = await self.get(path)
                extra = node.get('extra', {}).get(url, {})
                if check == 200 and extra.get('alive') and extra['history'][-1]['delay'] == data['delay']:
                    return 'SUCCESS', data['delay'], '200/204', False
                return 'UNKNOWN_ERROR', None, '204-not-confirmed', False
            category = {504: 'NODE_TIMEOUT', 503: 'NODE_TEST_FAILED', 404: 'CONFIG_CHANGED'}.get(code, 'API_UNAVAILABLE')
            return category, None, str(code), False
        except (TimeoutError, aiohttp.ClientError, OSError, ValueError, KeyError):
            return 'API_UNAVAILABLE', None, 'controller-transport', True

    async def direct(self, target):
        start = time.monotonic()
        try:
            async with self.session.head(TARGETS[target], proxy=f'http://127.0.0.1:{self.mixed}',
                    proxy_auth=aiohttp.BasicAuth('baseline', self.password), allow_redirects=False) as r:
                return r.status, round((time.monotonic()-start)*1000)
        except (OSError, TimeoutError, aiohttp.ClientError):
            return 0, round((time.monotonic()-start)*1000)
