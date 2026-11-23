"""Real isolated Mihomo, synthetic loopback exits, production failover intervals."""
import argparse
import copy
import http.server
import json
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import time
import urllib.parse
import urllib.request

import yaml

# Historical ROUTE-20261123.1 evidence fixture.
STABLE = ('HKG B', 'HKG C', 'HKG J', '新加坡 A', '台湾 B', '日本 A', '美国 B')
NODE_FAST = ('日本 A', '日本 B', 'HKG B', 'HKG C', 'HKG A', 'HKG I', 'HKG J', 'HKG M')
PRIORITY_PREFIX = 'AI稳备 · '

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mihomo',type=Path,required=True)
    args=parser.parse_args()
    runtime=Path(tempfile.mkdtemp(prefix='curated-failover-',dir=ROOT/'.local'))
    state={n:200 for n in set(STABLE+NODE_FAST)}
    checks=[];servers=[];proc=None
    def check(ok,label):
        if not ok:raise AssertionError(label)
        checks.append(label)
    def handler(name):
        class Proxy(http.server.BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_CONNECT(self):
                self.send_response(200,'Connection Established');self.end_headers()
                self.handle_one_request();self.close_connection=True
            def do_GET(self):
                status=state[name] if self.path.endswith('/gpt') else 204
                time.sleep(.01 if name=='日本 A' else .12)
                self.send_response(status)
                self.send_header('Content-Length','0');self.end_headers()
            do_HEAD=do_GET
        return Proxy
    nodes=[]
    for name in state:
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler(name));servers.append(server)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        nodes.append(dict(name=name,type='http',server='127.0.0.1',port=server.server_port))
    source=yaml.safe_load(subprocess.check_output(
            ['git', 'show', '963953e:config/clash-verge-auto.yaml'], cwd=ROOT).decode('utf-8'))
    wanted={'Jimmy · AI组','Jimmy · AI最速组','Jimmy · 最优速组',
            *('Jimmy · '+PRIORITY_PREFIX+n for n in STABLE)}
    groups=[copy.deepcopy(g) for g in source['proxy-groups'] if g['name'] in wanted]
    interval=next(g['interval'] for g in groups if g['name']=='Jimmy · AI组')
    for g in groups:
        if g.get('url')=='https://chatgpt.com/':g['url']='http://probe.invalid/gpt'
        else:g['url']='http://probe.invalid/generic'
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    config=dict(ipv6=False,dns={'enable':False},tun={'enable':False},**{
        'external-controller':f'127.0.0.1:{port}','mixed-port':0,'log-level':'warning',
        'proxy-providers':{'机场':dict(type='inline',payload=nodes,**{
            'health-check':dict(enable=True,url='http://probe.invalid/generic',interval=60,lazy=False,**{'expected-status':204})})},
        'proxy-groups':groups,'rules':['MATCH,REJECT']})
    path=runtime/'config.yaml';path.write_text(yaml.safe_dump(config,allow_unicode=True),'utf-8')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def api(route):
        with opener.open(f'http://127.0.0.1:{port}'+route,timeout=8) as r:return json.load(r)
    def selected(name):
        proxies=api('/proxies')['proxies'];seen=set()
        while name in proxies and 'now' in proxies[name]:
            if name in seen:raise AssertionError('selection cycle')
            seen.add(name);name=proxies[name]['now']
        return name
    def wait_for(name,expected,seconds=None):
        seconds=seconds if seconds is not None else interval+15
        start=time.monotonic()
        while selected(name)!=expected:
            if proc.poll() is not None or time.monotonic()-start>seconds:
                proxies=api('/proxies')['proxies']
                details={n:proxies[n] for n in ['Jimmy · AI组','Jimmy · AI稳备 · HKG B','Jimmy · AI稳备 · HKG C','HKG B','HKG C'] if n in proxies}
                (runtime/'failure.json').write_text(json.dumps(details,ensure_ascii=False,indent=2),'utf-8')
                print(json.dumps(dict(expected=expected,actual=selected(name),evidence=str(runtime/'failure.json')),ensure_ascii=False),flush=True)
                raise AssertionError('automatic failover timed out')
            time.sleep(.25)
        return round(time.monotonic()-start,3)
    try:
        with (runtime/'core.log').open('w',encoding='utf-8') as log:
            proc=subprocess.Popen([str(args.mihomo),'-d',str(runtime),'-f',str(path)],stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            deadline=time.monotonic()+15
            while True:
                try:api('/version');break
                except OSError:
                    if proc.poll() is not None or time.monotonic()>deadline:raise
                    time.sleep(.2)
            stable='Jimmy · AI组'
            deadline=time.monotonic()+15
            while True:
                provider=api('/providers/proxies/'+urllib.parse.quote('机场',safe=''))
                by_name={p['name']:p for p in provider['proxies']}
                if all(by_name[n].get('extra',{}).get('http://probe.invalid/gpt',{}).get('alive') for n in STABLE):break
                if time.monotonic()>deadline:raise AssertionError('initial successful health observations missing')
                time.sleep(.25)
            wait_for(stable,'HKG B',15)
            check(selected(stable)=='HKG B','stable pool selects historical priority B despite Japan being much faster')
            check(next(g for g in groups if g['name']=='Jimmy · 最优速组')['type']=='url-test',
                  'general speed pool retains automatic latency selection')
            state['HKG B']=503
            first=wait_for(stable,'HKG C')
            check(first<=interval+15,'service-specific B failure switches to C without manual healthcheck or selection')
            provider=api('/providers/proxies/'+urllib.parse.quote('机场',safe=''))
            b=next(n for n in provider['proxies'] if n['name']=='HKG B')
            check(b['extra']['http://probe.invalid/generic']['alive'],'generic health remains good while GPT failure triggers failover')
            state['HKG C']=503
            second=wait_for(stable,'HKG J')
            check(second<=interval+15,'second failed exit advances in fixed order to J')
            state['HKG B']=200
            restored=wait_for(stable,'HKG B')
            check(restored<=interval+15,'recovered first priority is restored automatically')
            check(all(g['interval']==interval and g['lazy'] is False for g in groups),'production active-check settings retained throughout fixture')
            receipt=dict(checks=checks,count=len(checks),first_failure_to_switch_seconds=first,
                         second_failure_to_switch_seconds=second,recovery_seconds=restored,
                         real_phone_tested=False,production_runtime_changed=False,
                         automatic_observation=True,scheduled_interval=interval)
            (runtime/'result.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),'utf-8')
            print(json.dumps(dict(receipt,evidence=str(runtime/'result.json')),ensure_ascii=False))
    finally:
        if proc and proc.poll() is None:
            proc.terminate();proc.wait(10)
        for server in servers:server.shutdown();server.server_close()


if __name__=='__main__':main()
