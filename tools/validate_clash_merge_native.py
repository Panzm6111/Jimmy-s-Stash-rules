"""Isolated native checks with synthetic nodes, local HTTP URLs and a test proxy."""
import copy
import argparse
import http.server
import json
import os
from pathlib import Path
import select
import shutil
import socket
import subprocess
import threading
import time
import urllib.parse
import urllib.request
import uuid
import yaml

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--mihomo', type=Path, required=True, help='existing native Mihomo executable')
parser.add_argument('--country-mmdb', type=Path, required=True, help='existing public Country.mmdb fixture')
args = parser.parse_args()
if not args.mihomo.is_file() or not args.country_mmdb.is_file():
    parser.error('Both existing local files are required; nothing is downloaded')
HERE = ROOT/'.local/clash-merge-native-check'
HERE.mkdir(parents=True, exist_ok=True)
NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
overlay = yaml.safe_load((ROOT/'config/clash-verge-merge.yaml').read_text(encoding='utf-8'))
checks = []
state = {'rules_version': 1, 'airport_version': 1, 'requests': 0, 'proxy_connects': 0}
colliding_names = {'台湾', '美国', '日本', 'TikTok', 'ai'}
def group_name(name): return 'Jimmy · '+name
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def check(condition, label):
    if not condition:
        raise AssertionError(label)
    checks.append(label)

def port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

class Proxy(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_CONNECT(self):
        host, target_port = self.path.rsplit(':', 1)
        # Test proxy only forwards to its local fixture HTTP server.
        if host != '127.0.0.1' or int(target_port) != fixture.server_port:
            self.send_error(403)
            return
        state['proxy_connects'] += 1
        with socket.create_connection((host, int(target_port)), timeout=5) as target:
            self.send_response(200)
            self.end_headers()
            pair = (self.connection, target)
            while True:
                ready, _, _ = select.select(pair, [], [], 5)
                if not ready: break
                for src in ready:
                    data = src.recv(65536)
                    if not data: return
                    (target if src is self.connection else self.connection).sendall(data)

def node(name):
    return {'name':name, 'type':'http', 'server':'127.0.0.1', 'port':proxy.server_port,
            'username':'synthetic-user', 'password':'synthetic-password'}

def airport():
    names = ['US-inline-fixture', '剩余流量 fixture'] + sorted(colliding_names)
    names += ['HK-inline-fixture'] if state['airport_version'] == 1 else ['US-new-fixture']
    return {'proxies':[node(n) for n in names],
            'proxy-providers':{'fixture-airport-provider':{'type':'inline','payload':[node('JP-provider-fixture'), node('SG-provider-fixture')]}},
            'proxy-groups':[{'name':'old-airport-group','type':'select','proxies':[names[0]]}],
            'rules':['MATCH,old-airport-group']}

class Fixture(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_GET(self):
        if self.path == '/airport.yaml':
            body = yaml.safe_dump(airport(), allow_unicode=True).encode()
        elif self.path.startswith('/r/'):
            state['requests'] += 1
            entries = ['DOMAIN,fixture-one.example']
            if state['rules_version'] == 2: entries.append('DOMAIN,fixture-two.example')
            body = yaml.safe_dump({'payload':entries}).encode()
        elif self.path == '/204':
            self.send_response(204); self.end_headers(); return
        else:
            self.send_error(404); return
        self.send_response(200)
        self.send_header('Content-Type','application/yaml')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

proxy = http.server.ThreadingHTTPServer(('127.0.0.1',0), Proxy)
fixture = http.server.ThreadingHTTPServer(('127.0.0.1',0), Fixture)
for server in (proxy, fixture):
    threading.Thread(target=server.serve_forever, daemon=True).start()
runtime = HERE/('native-fixture-'+uuid.uuid4().hex[:8])
runtime.mkdir(exist_ok=True)
shutil.copyfile(args.country_mmdb, runtime/'Country.mmdb')
api_port = port()
secret = uuid.uuid4().hex
config_path = runtime/'config.yaml'

def prepare():
    with opener.open(f'http://127.0.0.1:{fixture.server_port}/airport.yaml', timeout=5) as r:
        original = yaml.safe_load(r.read())
    merged = copy.deepcopy(original)
    merged.update(copy.deepcopy(overlay))
    check(merged['proxies'] == original['proxies'], 'airport node protocol fields preserved v'+str(state['airport_version']))
    check(merged['proxy-providers'] == original['proxy-providers'], 'airport providers preserved v'+str(state['airport_version']))
    check(merged['rules'] == overlay['rules'], 'airport rules replaced v'+str(state['airport_version']))
    merged.update({'external-controller':f'127.0.0.1:{api_port}', 'secret':secret,
                   'mixed-port':0,'port':0,'socks-port':0,'mode':'rule','allow-lan':False,
                   'log-level':'info','tun':{'enable':False},'dns':{'enable':False},
                   'profile':{'store-selected':False}})
    for g in merged['proxy-groups']:
        if 'url' in g: g['url'] = f'http://127.0.0.1:{fixture.server_port}/204'
    for i,p in enumerate(merged['rule-providers'].values()):
        p['url'] = f'http://127.0.0.1:{fixture.server_port}/r/{i}'
        p['path'] = f'./fixture-rules/{i}.yaml'
    config_path.write_text(yaml.safe_dump(merged, allow_unicode=True, sort_keys=False), encoding='utf-8')

def api(path, method='GET', body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f'http://127.0.0.1:{api_port}'+path, data=data, method=method,
        headers={'Authorization':'Bearer '+secret,'Content-Type':'application/json'})
    with opener.open(req, timeout=15) as r:
        text = r.read()
        return json.loads(text) if text else None

process = None
try:
    check(set(overlay) == {'rules','proxy-groups','rule-providers'}, 'overlay contains no airport credentials, node or app settings')
    check(all(p['interval'] == 86400 and p['proxy'] == group_name('自动节点') for p in overlay['rule-providers'].values()), 'all rule URLs have daily interval and explicit download proxy')
    prepare()
    env = dict(os.environ)
    for key in list(env):
        if key.lower() in ('http_proxy','https_proxy','all_proxy','no_proxy'): del env[key]
    executable = str(args.mihomo)
    # Reproduce the reported fault with an unnamespaced overlay and a node named 台湾.
    old_overlay = copy.deepcopy(overlay)
    for group in old_overlay['proxy-groups']:
        group['name'] = group['name'].removeprefix('Jimmy · ')
        if 'proxies' in group:
            group['proxies'] = [name.removeprefix('Jimmy · ') for name in group['proxies']]
    for i, rule in enumerate(old_overlay['rules']):
        parts = rule.split(','); target = 1 if parts[0] == 'MATCH' else 2
        parts[target] = parts[target].removeprefix('Jimmy · ')
        old_overlay['rules'][i] = ','.join(parts)
    for provider in old_overlay['rule-providers'].values():
        provider['proxy'] = provider['proxy'].removeprefix('Jimmy · ')
    old_config = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    old_config.update(old_overlay)
    old_config['proxies'] = [node('台湾')]
    old_path = runtime/'before-collision.yaml'
    old_path.write_text(yaml.safe_dump(old_config, allow_unicode=True), encoding='utf-8')
    before = subprocess.run([executable,'-t','-d',str(runtime),'-f',str(old_path)],
                            capture_output=True,text=True,encoding='utf-8',env=env,timeout=15,
                            creationflags=NO_WINDOW)
    check(before.returncode != 0 and 'proxy group 台湾: the duplicate name' in before.stdout+before.stderr,
          'unnamespaced overlay reproduces exact Taiwan duplicate-name error')
    with (runtime/'mihomo.log').open('w', encoding='utf-8') as log:
        process = subprocess.Popen([executable,'-d',str(runtime),'-f',str(config_path)],
                                   stdout=log, stderr=subprocess.STDOUT, env=env,
                                   creationflags=NO_WINDOW)
        deadline = time.monotonic()+25
        while True:
            try:
                groups = api('/proxies')['proxies']
                provider_states = api('/providers/rules')['providers']
                if all(p['ruleCount'] == 1 for p in provider_states.values()): break
            except Exception:
                pass
            if process.poll() is not None: raise RuntimeError('native process exited; inspect fixture log')
            if time.monotonic() > deadline: raise TimeoutError('native rule initialization incomplete')
            time.sleep(.25)
        check(len(provider_states) == len(overlay['rule-providers']), 'all remote rule providers loaded')
        check(state['proxy_connects'] >= len(provider_states), 'rule HTTP downloads passed through selected test proxy')
        check(set(groups[group_name('手动节点')]['all']) == {'US-inline-fixture','HK-inline-fixture','JP-provider-fixture','SG-provider-fixture'} | colliding_names, 'inline and provider nodes included; quota marker excluded')
        check(set(groups[group_name('ai')]['all']) == {'US-inline-fixture','JP-provider-fixture','SG-provider-fixture','美国','日本','台湾'}, 'four-region ai filters both node sources')
        check(groups[group_name('总代理')]['now'] == group_name('自动节点'), 'new master group starts with automatic nodes')
        check(group_name('ai') in groups[group_name('海外AI')]['all'], 'AI exposes four-region ai choice')
        check(groups[group_name('其他地区')]['all'] == ['REJECT'], 'empty region falls back to rejection')
        check(all(groups[n]['type'] == 'Http' and groups[group_name(n)]['type'] in {'Selector','URLTest'} for n in colliding_names), 'airport nodes and namespaced custom groups coexist')
        state['rules_version'] = 2
        first = next(iter(overlay['rule-providers']))
        api('/providers/rules/'+urllib.parse.quote(first,safe=''), 'PUT')
        check(api('/providers/rules')['providers'][first]['ruleCount'] == 2, 'rule URL refresh changes content without reload')
        state['airport_version'] = 2
        prepare()
        api('/configs', 'PUT', {'path':str(config_path)})
        groups = api('/proxies')['proxies']
        check(set(groups[group_name('手动节点')]['all']) == {'US-inline-fixture','US-new-fixture','JP-provider-fixture','SG-provider-fixture'} | colliding_names, 'airport URL refresh plus reload incorporates added and removed nodes')
        check('old-airport-group' not in groups, 'airport strategy groups replaced')
finally:
    if process is not None and process.poll() is None:
        process.terminate()
        try: process.wait(timeout=5)
        except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)
    for server in (proxy, fixture): server.shutdown(); server.server_close()

result = {'native_core':'Mihomo', 'checks':checks, 'passed':len(checks),
          'providers':len(overlay['rule-providers']), 'fixture_rule_requests':state['requests'],
          'fixture_proxy_connects':state['proxy_connects'],
          'client_acceptance':'pending: actual Clash Verge UI, private airport and real service connectivity',
          'actual_client_modified':False, 'system_proxy_modified':False}
(HERE/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':len(checks),'providers':len(overlay['rule-providers']),
                  'fixture_proxy_connects':state['proxy_connects']},ensure_ascii=False))
