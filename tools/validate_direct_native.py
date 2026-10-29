"""Load the verified real upstream bodies in isolated Mihomo processes via loopback."""
import argparse,copy,hashlib,http.server,json,os,shutil,socket,subprocess,tempfile,threading,time,urllib.request
from pathlib import Path
import yaml
from provider_sources import ROOT
from validate import local_public_path

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mihomo',type=Path,required=True);parser.add_argument('--country-mmdb',type=Path,required=True);args=parser.parse_args()
    verified=json.loads((ROOT/'.local/direct-source-check.json').read_text())
    fetched={x['url']:x for x in verified};bodies={};results=[]
    class Fixture(http.server.BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            if self.path=='/204':self.send_response(204);self.end_headers();return
            body=bodies.get(self.path)
            if body is None:self.send_error(404);return
            self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Fixture);threading.Thread(target=server.serve_forever,daemon=True).start()
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        for source in ['config/clash-verge.yaml','config/clash-verge-auto.yaml']:
            config=yaml.safe_load((ROOT/source).read_text(encoding='utf-8'));runtime=Path(tempfile.mkdtemp(prefix='direct-native-',dir=ROOT/'.local'))
            shutil.copyfile(args.country_mmdb,runtime/'Country.mmdb')
            with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
            config.update({'external-controller':f'127.0.0.1:{port}','mixed-port':0,'dns':{'enable':False},'tun':{'enable':False},'log-level':'warning'})
            config['proxy-providers']={'机场':{'type':'inline','payload':[{'name':'US-fixture','type':'socks5','server':'127.0.0.1','port':9}]}}
            expected={}
            for index,(name,provider) in enumerate(config['rule-providers'].items()):
                url=provider['url'];item=fetched.get(url)
                if item:
                    body=(ROOT/item['cached_file']).read_bytes();assert hashlib.sha256(body).hexdigest()==item['sha256']
                else:body=(ROOT/local_public_path(url)).read_bytes()
                path=f'/rules/{index}';bodies[path]=body;expected[name]=len(yaml.safe_load(body)['payload'])
                provider.update(url=f'http://127.0.0.1:{server.server_port}{path}',path=f'./rules/{index}.yaml',proxy='DIRECT')
            for group in config['proxy-groups']:
                if 'url' in group:group['url']=f'http://127.0.0.1:{server.server_port}/204'
            path=runtime/'config.yaml';path.write_text(yaml.safe_dump(config,allow_unicode=True,sort_keys=False),encoding='utf-8')
            process=None
            try:
                with (runtime/'core.log').open('w',encoding='utf-8') as log:
                    process=subprocess.Popen([str(args.mihomo),'-d',str(runtime),'-f',str(path)],stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                    deadline=time.monotonic()+35
                    while True:
                        try:
                            with opener.open(f'http://127.0.0.1:{port}/providers/rules',timeout=3) as response:providers=json.load(response)['providers']
                            if len(providers)==len(expected) and all(providers[k]['ruleCount']==n for k,n in expected.items()):break
                        except (OSError,ValueError,KeyError):pass
                        if process.poll() is not None or time.monotonic()>deadline:raise AssertionError('Real source native load failed; inspect ignored core log')
                        time.sleep(.2)
                    results.append({'configuration':source,'providers':len(providers),'counts':expected,'source_bytes_verified':True,'current_client_modified':False})
            finally:
                if process and process.poll() is None:process.terminate();process.wait(timeout=10)
    finally:server.shutdown();server.server_close()
    (ROOT/'.local/direct-native-result.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False))
if __name__=='__main__':main()
