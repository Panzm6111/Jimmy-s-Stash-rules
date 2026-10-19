#!/usr/bin/env python3
"""Render only the explicitly reviewed ad catalog. No network, credentials or conversion service."""
import argparse
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW = 'https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/'
EMPTY_ACTIONS = {'reject-dict', 'reject-200'}
RESPONSE_PATH = 'scripts/ads/empty-response.js'
RESPONSE_NAME = 'jimmy_ad_empty_response'

def empty_response_script(catalog):
    routes = [{'id': item['id'], 'match': rule['match'], 'json': rule['upstream_action'] == 'reject-dict'}
              for item in catalog['modules'] for rule in item['rewrite']
              if rule['upstream_action'] in EMPTY_ACTIONS]
    return '''/* SPDX-License-Identifier: GPL-3.0-only
 * Dedicated advertising endpoints adapted from fmz200/wool_scripts.
 * Generated from research/ad-catalog.json; edit that catalog, not this file.
 * Native Stash request response API evidence: docs/SOURCES.md.
 * No request body, account data, storage, external requests or notifications.
 */
(() => {
  let result = {};
  let marker = '';
  try {
    const req = typeof $request === 'object' && $request ? $request : {};
    // A request script must never modify a response-phase invocation.
    if (typeof $response !== 'undefined' || !['GET', 'POST'].includes(req.method)) return;
    const routes = ''' + json.dumps(routes, ensure_ascii=False, indent=2) + ''';
    const hit = routes.find(route => new RegExp(route.match).test(String(req.url || '')));
    if (!hit) return;
    result = {response: {
      status: 200,
      headers: {'Content-Type': hit.json ? 'application/json; charset=utf-8' : 'text/plain; charset=utf-8',
                'Cache-Control': 'no-store'},
      body: hit.json ? '{}' : ''
    }};
    marker = '[JimmyAds][' + hit.id + '] ' + (hit.json ? 'empty-json' : 'empty-200');
  } catch (_) {
    // Unexpected runtime errors pass through; never print the exception.
  } finally {
    if (marker) { try { console.log(marker); } catch (_) {} }
    $done(result);
  }
})();
'''

def rendered(catalog):
    result = {}
    for item in catalog['modules']:
        source = catalog['sources'][item['source']]
        config = {'name': item['app'] + '广告专项（可选）',
                  'desc': item['scope'] + '。默认不导入；需设备验收。'}
        if item['domains']:
            config['rules'] = ['DOMAIN,' + host + ',广告拦截' for host in item['domains']]
        http = {}
        if item['mitm']: http['mitm'] = item['mitm']
        if item['rewrite']:
            rejects = [rule['match'] + ' - reject' for rule in item['rewrite']
                       if rule['upstream_action'] not in EMPTY_ACTIONS]
            if rejects: http['rewrite'] = rejects
            requests = [{'match': rule['match'], 'name': RESPONSE_NAME,
                         'type': 'request', 'require-body': False, 'timeout': 5}
                        for rule in item['rewrite'] if rule['upstream_action'] in EMPTY_ACTIONS]
            if requests:
                http['script'] = requests
                config['script-providers'] = {RESPONSE_NAME: {'url': RAW + RESPONSE_PATH, 'interval': 86400}}
        if item['script']:
            script = item['script']
            http.setdefault('script', []).append({'match': script['match'], 'name': script['name'],
                                                  'type': 'response', 'require-body': True, 'timeout': 5})
            config.setdefault('script-providers', {})[script['name']] = {'url': RAW + script['path'], 'interval': 86400}
        if http: config['http'] = http
        header = ('# SPDX-License-Identifier: ' + item['license'] + '\n'
                  '# Reviewed source: ' + source['url'] + '\n'
                  '# License: ' + source['license_file'] + '\n'
                  '# Generated from research/ad-catalog.json; edit the catalog, then regenerate.\n')
        result[item['file']] = header + yaml.safe_dump(config, allow_unicode=True, sort_keys=False, width=120)
    result[RESPONSE_PATH] = empty_response_script(catalog)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='write reviewed generated overrides; default checks drift')
    args = parser.parse_args()
    catalog = json.loads((ROOT / 'research/ad-catalog.json').read_text())
    drift = []
    for name, body in rendered(catalog).items():
        destination = ROOT / name
        if not destination.is_file() or destination.read_text() != body:
            drift.append(name)
            if args.write:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(body)
    print(f'{len(catalog["modules"])} reviewed modules; {len(drift)} ' + ('written' if args.write else 'differ'))
    return 0 if args.write or not drift else 1

if __name__ == '__main__': raise SystemExit(main())
