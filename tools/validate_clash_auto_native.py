"""Full remote profile reload checks; synthetic loopback services, no real client changes."""
import argparse,copy,http.server,json,os,shutil,socket,subprocess,threading,time,urllib.request,urllib.error,urllib.parse
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mihomo',type=Path,required=True)
    parser.add_argument('--country-mmdb',type=Path,required=True)
    args=parser.parse_args()
    if not args.mihomo.is_file() or not args.country_mmdb.is_file():parser.error('Existing core and MMDB required')
    import tempfile
    base=ROOT/'.local/clash-auto-native-check';base.mkdir(parents=True,exist_ok=True)
    runtime=Path(tempfile.mkdtemp(prefix='fixture-',dir=base))
    shutil.copyfile(args.country_mmdb,runtime/'Country.mmdb')
    state={'airport_version':1,'rule_version':1,'airport_requests':0,'airport_ua_matched':0,'airport_available':False}
    checks=[]
    def check(ok,label):
        if not ok:raise AssertionError(label)
        checks.append(label)
    def node(name):return {'name':name,'type':'socks5','server':'127.0.0.1','port':9}
    class Fixture(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            if self.path=='/airport.yaml':
                state['airport_requests']+=1
                if not state['airport_available']:
                    self.send_error(503);return
                if self.headers.get('User-Agent')!='clash-verge/v2.5.8':
                    body=b'dmxlc3M6Ly9zeW50aGV0aWMtaW52YWxpZA=='
                    self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
                state['airport_ua_matched']+=1
                names=['美国','日本','台湾','TikTok','US-synthetic' if state['airport_version']==1 else 'US-updated']
                obj={'proxies':[node(n) for n in names]}
            elif self.path.startswith('/rules/'):
                obj={'payload':['DOMAIN,one.example.invalid']+(['DOMAIN,two.example.invalid'] if state['rule_version']==2 else [])}
            else:self.send_error(404);return
            body=yaml.safe_dump(obj,allow_unicode=True).encode()
            self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    fixture=http.server.ThreadingHTTPServer(('127.0.0.1',0),Fixture)
    threading.Thread(target=fixture.serve_forever,daemon=True).start()
    with socket.socket() as s:s.bind(('127.0.0.1',0));api_port=s.getsockname()[1]
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def api(path,method='GET',body=None):
        data=json.dumps(body).encode() if body is not None else None
        req=urllib.request.Request(f'http://127.0.0.1:{api_port}'+path,data=data,method=method,headers={'Content-Type':'application/json'})
        with opener.open(req,timeout=15) as r:
            result=r.read();return json.loads(result) if result else None
    public=yaml.safe_load((ROOT/'config/clash-verge-auto.yaml').read_text(encoding='utf-8'))
    private_url=f'http://127.0.0.1:{fixture.server_port}/airport.yaml'
    def prepared(source):
        config=copy.deepcopy(source)
        config.update({'external-controller':f'127.0.0.1:{api_port}','mixed-port':0,'mode':'rule',
                       'tun':{'enable':False},'dns':{'enable':False},'log-level':'warning'})
        config['proxy-providers']['机场'].update(url=private_url,path='./airport.yaml')
        config['proxy-providers']['机场']['payload']=[node(n) for n in ['跳转域名{请勿连接}:example.invalid','美国','日本','台湾','TikTok','US-synthetic']]
        for i,p in enumerate(config['rule-providers'].values()):
            p.update(url=f'http://127.0.0.1:{fixture.server_port}/rules/{i}',path=f'./rules/{i}.yaml',proxy='DIRECT')
        return config
    path=runtime/'config.yaml'
    def save(value):path.write_text(yaml.safe_dump(value,allow_unicode=True,sort_keys=False),encoding='utf-8')
    config=prepared(public);save(config)
    env={k:v for k,v in os.environ.items() if k.lower() not in {'http_proxy','https_proxy','all_proxy','no_proxy'}}
    process=None
    try:
        with (runtime/'core.log').open('w',encoding='utf-8') as log:
            process=subprocess.Popen([str(args.mihomo),'-d',str(runtime),'-f',str(path)],stdout=log,stderr=subprocess.STDOUT,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            deadline=time.monotonic()+25
            while True:
                try:
                    groups=api('/proxies')['proxies'];providers=api('/providers/rules')['providers']
                    if all(v['ruleCount']==1 for v in providers.values()) and 'US-synthetic' in groups['Jimmy · 手动节点']['all']:break
                except (OSError,ValueError):pass
                if process.poll() is not None or time.monotonic()>deadline:raise RuntimeError('Fixture initialization failed; inspect local log')
                time.sleep(.2)
            check(len(providers)==17,'all 17 remote rule providers load')
            check(state['airport_requests']>0 and not (runtime/'airport.yaml').exists(),
                  'private fallback supplies nodes with failed first download and no cache')
            check('跳转域名{请勿连接}:example.invalid' not in groups['Jimmy · 手动节点']['all'],
                  'airport informational redirect entry is excluded from selectable nodes')
            api('/proxies/'+urllib.parse.quote('Jimmy · 手动节点',safe=''),'PUT',{'name':'US-synthetic'})
            state['airport_available']=True
            api('/providers/proxies/'+urllib.parse.quote('机场',safe=''),'PUT')
            check((runtime/'airport.yaml').exists(),'successful later download replaces startup fallback with a cache')
            check(state['airport_ua_matched']>0,'airport fetch requests Clash YAML through explicit client user agent')
            check(len([n for n in groups if n.startswith('Jimmy · ')])==20,'all 20 namespaced groups load')
            members=groups['Jimmy · 手动节点']['all']
            check(all(n in members for n in ['美国','日本','台湾','TikTok']),'same-name airport nodes coexist with groups')
            check(groups['Jimmy · 总代理']['now']=='Jimmy · 自动节点','initial default is automatic pool')
            check('Jimmy · 日本+美国' in groups['Jimmy · 海外AI']['all'],'AI Japan plus US option retained')
            check(groups['Jimmy · 新加坡']['all']==['REJECT'],'empty region rejects instead of direct fallback')
            api('/proxies/'+urllib.parse.quote('Jimmy · 海外AI',safe=''),'PUT',{'name':'Jimmy · 日本+美国'})
            next_public=copy.deepcopy(public)
            next_public['proxy-groups'].append({'name':'Jimmy · remote-update-fixture','type':'select','proxies':['Jimmy · 美国']})
            next_public['rule-providers']['remote-update-fixture']=copy.deepcopy(public['rule-providers']['海外AI'])
            next_public['rules'].insert(0,'RULE-SET,remote-update-fixture,Jimmy · remote-update-fixture')
            next_config=prepared(next_public);save(next_config)
            api('/configs','PUT',{'path':str(path)})
            groups=api('/proxies')['proxies']
            check('Jimmy · remote-update-fixture' in groups,'new group arrives after complete profile reload')
            check(api('/rules')['rules'][0]['proxy']=='Jimmy · remote-update-fixture','new rule priority takes effect')
            check('remote-update-fixture' in api('/providers/rules')['providers'],'new provider declaration takes effect')
            check(next_config['proxy-providers']['机场']['url']==private_url,'private airport URL survives public structural update')
            check(groups['Jimmy · 海外AI']['now']=='Jimmy · 日本+美国','selected AI pool survives reload')
            state['airport_version']=2
            api('/providers/proxies/'+urllib.parse.quote('机场',safe=''),'PUT')
            members=api('/proxies')['proxies']['Jimmy · 手动节点']['all']
            check('US-updated' in members and 'US-synthetic' not in members,'airport node refresh propagates without profile replacement')
            state['rule_version']=2
            api('/providers/rules/'+urllib.parse.quote('基础广告',safe=''),'PUT')
            check(api('/providers/rules')['providers']['基础广告']['ruleCount']==2,'advertising rules refresh independently')
            invalid=copy.deepcopy(next_config);invalid['rules']=['MATCH,missing-fixture-group'];save(invalid)
            rejected=False
            try:api('/configs','PUT',{'path':str(path)})
            except urllib.error.HTTPError:rejected=True
            check(rejected and 'Jimmy · remote-update-fixture' in api('/proxies')['proxies'],'core rejects invalid reload and keeps running configuration')
            save(config);api('/configs','PUT',{'path':str(path)})
            check('Jimmy · remote-update-fixture' not in api('/proxies')['proxies'],'previous profile can be restored')
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
        fixture.shutdown();fixture.server_close()
    result={'passed':len(checks),'checks':checks,'actual_client_modified':False,
            'boundary':'Native fixture checks only; does not test Clash Verge timer or real airport connectivity.'}
    (base/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
