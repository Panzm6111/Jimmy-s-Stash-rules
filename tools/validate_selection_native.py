"""Isolated Mihomo status/tolerance/manual-pin checks using synthetic HTTP proxies."""
import argparse,copy,http.server,json,socket,subprocess,tempfile,threading,time,urllib.parse,urllib.request
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mihomo',type=Path,required=True);args=parser.parse_args()
    runtime=Path(tempfile.mkdtemp(prefix='selection-',dir=ROOT/'.local'))
    # Keep initial fastest away from index zero; v1.19.32 has a separate
    # first-member tolerance boundary, recorded below rather than hidden.
    state={'新加坡 A':[200,.01],'荷兰':[204,.43],'英国 B':[204,.60]}
    servers=[];checks=[]
    def check(ok,label):
        if not ok:raise AssertionError(label)
        checks.append(label)
    def handler(name):
        class Proxy(http.server.BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_CONNECT(self):
                self.send_response(200,'Connection Established');self.end_headers()
                self.handle_one_request();self.close_connection=True
            def do_HEAD(self):self.do_GET()
            def do_GET(self):
                status,delay=state[name];time.sleep(delay)
                self.send_response(status);self.send_header('Content-Length','0');self.end_headers()
        return Proxy
    nodes=[]
    for name in state:
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler(name));servers.append(server)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        nodes.append(dict(name=name,type='http',server='127.0.0.1',port=server.server_port))
    source=yaml.safe_load((ROOT/'config/clash-verge-auto.yaml').read_text(encoding='utf-8'))
    group=copy.deepcopy(next(g for g in source['proxy-groups'] if g['name']=='Jimmy · ai'))
    # Deliberately non-TLS loopback HTTP test endpoint; no production DNS/TUN/ports.
    probe='http://probe.example.invalid/204';group['url']=probe
    health=copy.deepcopy(source['proxy-providers']['机场']['health-check']);health['url']=probe
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    config={'external-controller':f'127.0.0.1:{port}','mixed-port':0,'ipv6':False,
            'dns':{'enable':False},'tun':{'enable':False},'log-level':'warning',
            'profile':{'store-selected':True},
            'proxy-providers':{'机场':{'type':'inline','payload':nodes,'health-check':health}},
            'proxy-groups':[group],'rules':['MATCH,REJECT']}
    path=runtime/'config.yaml';path.write_text(yaml.safe_dump(config,allow_unicode=True),encoding='utf-8')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def api(path,method='GET',body=None):
        request=urllib.request.Request(f'http://127.0.0.1:{port}'+path,method=method,
                                      data=json.dumps(body).encode() if body is not None else None,
                                      headers={'Content-Type':'application/json'})
        with opener.open(request,timeout=10) as response:
            raw=response.read();return json.loads(raw) if raw else None
    group_path='/proxies/'+urllib.parse.quote(group['name'],safe='')
    provider_path='/providers/proxies/'+urllib.parse.quote('机场',safe='')
    process=None
    try:
        with (runtime/'core.log').open('w',encoding='utf-8') as log:
            process=subprocess.Popen([str(args.mihomo),'-d',str(runtime),'-f',str(path)],stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            deadline=time.monotonic()+20
            while True:
                try:api('/version');break
                except OSError:
                    if process.poll() is not None or time.monotonic()>deadline:raise
                    time.sleep(.2)
            api(provider_path+'/healthcheck')
            deadline=time.monotonic()+10
            while True:
                proxies={p['name']:p for p in api(provider_path)['proxies']}
                if all(p.get('history') for p in proxies.values()):break
                if time.monotonic()>deadline:raise AssertionError('health probe did not finish')
                time.sleep(.2)
            check(not proxies['新加坡 A']['extra'][probe]['alive'],'HTTP 200 is rejected for this test URL despite transport success')
            check(proxies['荷兰']['extra'][probe]['alive'] and proxies['英国 B']['extra'][probe]['alive'],'HTTP 204 probe succeeds on both healthy fixtures')
            current=api(group_path)
            check(current['now']=='荷兰','healthy lowest-latency node selected automatically')
            check(current['hidden'] and current['expectedStatus']=='204','hidden and expected-status fields loaded')
            time.sleep(1.1)
            state['新加坡 A']=[204,.25];api(provider_path+'/healthcheck');time.sleep(11)
            measured={p['name']:p['extra'][probe] for p in api(provider_path)['proxies']}
            check(measured['新加坡 A']['alive'],'previously invalid node recovers on a new 204 response')
            advantage=measured['荷兰']['history'][-1]['delay']-measured['新加坡 A']['history'][-1]['delay']
            check(100<advantage<250,'measured improvement is between the old and new thresholds')
            check(api(group_path)['now']=='荷兰','250ms AI tolerance retains the current healthy node')
            state['新加坡 A']=[204,.01];api(provider_path+'/healthcheck');time.sleep(11)
            check(api(group_path)['now']=='新加坡 A','improvement greater than tolerance switches automatically')
            api(group_path,'PUT',{'name':'英国 B'})
            check(api(group_path)['fixed']=='英国 B','hidden is not a hard API manual-selection lock')
            api(group_path,'DELETE')
            current=api(group_path)
            check(not current['fixed'] and current['now']=='新加坡 A','explicit unpin restores automatic selection')
            state['荷兰']=[204,.001];api(provider_path+'/healthcheck');time.sleep(11)
            boundary={'former_first_member':'新加坡 A','selected_after_small_improvement':api(group_path)['now'],
                      'note':'v1.19.32 may ignore tolerance when the current node is the first member; not a hard switching guarantee.'}
            failed=api(group_path)['now']
            state[failed]=[503,.01]
            started=time.monotonic()
            while api(group_path)['now']==failed:
                if time.monotonic()-started>90:raise AssertionError('scheduled health check did not switch')
                time.sleep(.25)
            elapsed=round(time.monotonic()-started,2)
            check(not api(group_path).get('fixed'),'unpinned pool switches after an HTTP 503 without manual probing')
            result={'scheduled_switch_seconds':elapsed,'passed':len(checks),'checks':checks,'retained_at_advantage_ms':advantage,'actual_client_modified':False,'private_nodes_used':False,
                    'first_member_tolerance_boundary':boundary,
                    'boundary':'Synthetic Mihomo test; no Clash UI or real AI/TikTok acceptance.'}
            (runtime/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
            print(json.dumps(result))
    finally:
        if process and process.poll() is None:process.terminate();process.wait(timeout=10)
        for server in servers:server.shutdown();server.server_close()


if __name__=='__main__':main()
