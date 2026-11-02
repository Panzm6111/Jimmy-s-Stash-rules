"""Native automatic subscription failover test using synthetic local HTTP proxies."""
import argparse
import copy
import http.server
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import time
import urllib.request
import urllib.parse

import yaml
from build_clash import DOWNLOAD_GROUP

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mihomo', type=Path, required=True)
    args = parser.parse_args()
    if not args.mihomo.is_file():
        parser.error('Existing native core required')
    runtime = Path(tempfile.mkdtemp(prefix='download-failover-', dir=ROOT/'.local'))
    state = {'alive': [True, True], 'downloads': [0, 0], 'checks': [0, 0], 'version': 1}
    nodes = []
    servers = []
    checks = []

    def handler(index):
        class Proxy(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_CONNECT(self):
                if not state['alive'][index]:
                    self.send_error(503)
                    return
                self.send_response(200, 'Connection Established')
                self.end_headers()
                self.handle_one_request()
                self.close_connection = True

            def do_HEAD(self):
                self.do_GET()

            def do_GET(self):
                path = urllib.parse.urlsplit(self.path).path
                if not state['alive'][index]:
                    self.send_error(503)
                    return
                if path == '/health':
                    state['checks'][index] += 1
                    self.send_response(204)
                    self.end_headers()
                elif path == '/airport':
                    state['downloads'][index] += 1
                    body = yaml.safe_dump({'proxies': nodes + ([
                        {'name': 'US-new-arrival', 'type': 'http', 'server': '127.0.0.1',
                         'port': servers[1].server_port}] if state['version'] == 2 else [])}).encode()
                    self.send_response(200)
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_error(404)
        return Proxy

    for index in range(2):
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler(index))
        server.daemon_threads = True
        servers.append(server)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        nodes.append({'name': f'US-fixture-{index+1}', 'type': 'http',
                      'server': '127.0.0.1', 'port': server.server_port})
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    public = yaml.safe_load((ROOT/'config/clash-verge-auto.yaml').read_text(encoding='utf-8'))
    group = copy.deepcopy(next(g for g in public['proxy-groups'] if g['name'] == DOWNLOAD_GROUP))
    group.update(url='http://health.example.invalid/health', interval=1, timeout=300)
    provider = copy.deepcopy(public['proxy-providers']['机场'])
    provider.update(url='http://airport.example.invalid/airport', path='./airport.yaml',
                    payload=nodes, interval=2)
    provider['health-check'].update(url=group['url'], interval=1, timeout=300)
    config = {'mixed-port': 0, 'external-controller': f'127.0.0.1:{port}',
              'tun': {'enable': False}, 'dns': {'enable': False}, 'log-level': 'warning',
              'proxy-providers': {'机场': provider}, 'proxy-groups': [group], 'rules': ['MATCH,DIRECT']}
    path = runtime/'config.yaml'
    path.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding='utf-8')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def api(endpoint):
        with opener.open(f'http://127.0.0.1:{port}'+endpoint, timeout=3) as response:
            return json.load(response)

    def until(predicate, label, timeout=20):
        deadline = time.monotonic()+timeout
        while time.monotonic() < deadline:
            try:
                if predicate():
                    checks.append(label)
                    return
            except (OSError, ValueError, KeyError):
                pass
            time.sleep(.2)
        raise AssertionError(label)

    process = None
    try:
        with (runtime/'core.log').open('w', encoding='utf-8') as log:
            process = subprocess.Popen([str(args.mihomo), '-d', str(runtime), '-f', str(path)],
                stdout=log, stderr=subprocess.STDOUT,
                env={k:v for k,v in os.environ.items() if k.lower() not in {'http_proxy','https_proxy','all_proxy','no_proxy'}},
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            until(lambda: state['downloads'][0] > 0, 'cold start downloads through first available proxy automatically')
            until(lambda: all(state['checks']), 'both proxies receive scheduled health checks')
            first_count = state['downloads'][0]
            state['alive'][0] = False
            state['version'] = 2
            until(lambda: state['downloads'][1] > 0, 'scheduled subscription refresh fails over after first proxy outage')
            until(lambda: any(n['name']=='US-new-arrival' for n in
                  api('/providers/proxies')['providers']['机场']['proxies']),
                  'new subscription nodes propagate without manual selection or reload')
            until(lambda: api('/proxies')['proxies'][DOWNLOAD_GROUP]['now']=='US-fixture-2',
                  'download pool chooses the remaining live proxy')
            state['alive'][1] = False
            time.sleep(3)
            until(lambda: len(api('/providers/proxies')['providers']['机场']['proxies'])==3,
                  'all exits failing does not discard last valid nodes')
            state['alive'][0] = True
            until(lambda: state['downloads'][0] > first_count,
                  'scheduled refresh resumes after an exit recovers')
    finally:
        if process and process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        for server in servers:
            server.shutdown()
            server.server_close()
    result = {'passed': len(checks), 'checks': checks,
              'manual_proxy_selection_calls': 0, 'manual_provider_refresh_calls': 0,
              'production_network_changed': False,
              'test_intervals': {'health_seconds': 1, 'provider_seconds': 2},
              'production_intervals': {
                  'health_seconds': public['proxy-providers']['机场']['health-check']['interval'],
                  'provider_seconds': public['proxy-providers']['机场']['interval']}}
    (ROOT/'.local/download-failover-result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
