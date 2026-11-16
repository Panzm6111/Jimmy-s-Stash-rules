"""Isolated business-dial failures, distinct from waiting for scheduled probes."""
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

from curated_pools import STABLE, PRIORITY_PREFIX

ROOT=Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]


def scenario(core, root, strategy, fault):
    folder=Path(tempfile.mkdtemp(prefix=strategy+'-'+fault+'-',dir=root))
    names=list(STABLE) if strategy=='ordered' else ['新加坡 A','台湾 E','台湾 D']
    first=names[0];bad=set();servers={};proc=None
    def handler(name):
        class Proxy(http.server.BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_CONNECT(self):
                if name in bad:
                    self.send_error(503);self.close_connection=True;return
                self.send_response(200,'Connection Established');self.end_headers()
                self.handle_one_request();self.close_connection=True
            def do_GET(self):
                time.sleep(.01 if name==first else .08)
                body=json.dumps({'node':name}).encode()
                status=204 if self.path.endswith('/generic') else 200
                if status==204:body=b''
                self.send_response(status);self.send_header('Content-Length',str(len(body)))
                self.end_headers();self.wfile.write(body)
            do_HEAD=do_GET
        return Proxy
    nodes=[]
    for name in names:
        s=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler(name));servers[name]=s
        threading.Thread(target=s.serve_forever,daemon=True).start()
        nodes.append(dict(name=name,type='http',server='127.0.0.1',port=s.server_port))
    name='Jimmy · AI组'
    if strategy=='ordered':
        source=yaml.safe_load((ROOT/'config/clash-verge-auto.yaml').read_text('utf-8'))
        wanted={name,*('Jimmy · '+PRIORITY_PREFIX+n for n in STABLE)}
        groups=[copy.deepcopy(g) for g in source['proxy-groups'] if g['name'] in wanted]
    else:
        groups=[dict(name=name,type='url-test',use=['机场'],url='https://chatgpt.com/',
                     interval=60,lazy=False,tolerance=250,timeout=6000,**{'expected-status':200})]
    for g in groups:g['url']='http://probe.invalid/gpt'
    port=free_port();mixed=free_port()
    cfg={'external-controller':f'127.0.0.1:{port}','mixed-port':mixed,'mode':'rule',
         'ipv6':False,'dns':{'enable':False},'tun':{'enable':False},'log-level':'warning',
         'proxy-providers':{'机场':dict(type='inline',payload=nodes,**{'health-check':dict(
             enable=True,url='http://probe.invalid/generic',interval=60,lazy=False)})},
         'proxy-groups':groups,'rules':['MATCH,'+name]}
    path=folder/'config.yaml';path.write_text(yaml.safe_dump(cfg,allow_unicode=True),'utf-8')
    control=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    proxy=urllib.request.build_opener(urllib.request.ProxyHandler({'http':f'http://127.0.0.1:{mixed}'}))
    def api(route):
        with control.open(f'http://127.0.0.1:{port}'+route,timeout=5) as r:return json.load(r)
    def business():
        with proxy.open('http://service.invalid/business',timeout=3) as r:return json.load(r)['node']
    try:
        with (folder/'core.log').open('w',encoding='utf-8') as log:
            proc=subprocess.Popen([str(core),'-d',str(folder),'-f',str(path)],stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            deadline=time.monotonic()+15
            while True:
                try:
                    pd=api('/providers/proxies/'+urllib.parse.quote('机场',safe=''))
                    if all(p.get('extra',{}).get('http://probe.invalid/gpt',{}).get('alive') for p in pd['proxies']):break
                except OSError:pass
                if proc.poll() is not None or time.monotonic()>deadline:raise AssertionError('initial healthy probes missing')
                time.sleep(.05)
            assert business()==first,'initial business path not on expected first node'
            if fault=='refused':servers[first].shutdown();servers[first].server_close()
            else:bad.add(first)
            started=time.monotonic();errors=0;retries=0
            while True:
                try:
                    selected=business()
                    if selected!=first:break
                except (OSError,ValueError):errors+=1
                retries+=1
                if time.monotonic()-started>10:raise AssertionError('event-driven recovery exceeded 10 seconds')
                time.sleep(.1)
            elapsed=round(time.monotonic()-started,3)
            assert selected in names[1:]
            assert elapsed<10 and min(g['interval'] for g in groups)>=60
            cascade={}
            if strategy=='ordered' and fault=='refused':
                servers[selected].shutdown();servers[selected].server_close()
                cascade_start=time.monotonic()
                while True:
                    try:
                        next_node=business()
                        if next_node!=selected:break
                    except (OSError,ValueError):pass
                    if time.monotonic()-cascade_start>10:raise AssertionError('second business failure did not recover')
                    time.sleep(.1)
                assert next_node==names[2]
                cascade=dict(second_recovered=next_node,second_recovery_seconds=round(time.monotonic()-cascade_start,3))
            return dict(strategy=strategy,fault=fault,first=first,recovered=selected,
                        recovery_seconds=elapsed,failed_requests=errors,client_retries=retries,
                        minimum_scheduled_interval=min(g['interval'] for g in groups),
                        manual_healthcheck=False,manual_selection=False,
                        note='Measured through business requests; fixture client retries every 100ms. No general transparent replay claim.',**cascade)
    finally:
        if proc and proc.poll() is None:proc.terminate();proc.wait(10)
        for s in servers.values():s.shutdown();s.server_close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mihomo',type=Path,required=True);args=parser.parse_args()
    folder=Path(tempfile.mkdtemp(prefix='business-failover-',dir=ROOT/'.local'))
    rows=[]
    for strategy in ('desktop-baseline','ordered'):
        for fault in ('refused','handshake'):
            row=scenario(args.mihomo,folder,strategy,fault);rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
    receipt=dict(cases=rows,real_phone_tested=False,production_client_modified=False)
    (folder/'result.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n','utf-8')
    print('Evidence: '+str(folder/'result.json'))


if __name__=='__main__':main()
