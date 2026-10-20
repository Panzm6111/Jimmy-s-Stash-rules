#!/usr/bin/env python3
"""Render only the explicitly reviewed ad catalog. No network, credentials or conversion service."""
import argparse
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW = 'https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/'

def rendered(catalog):
    result = {}
    for item in catalog['modules']:
        source = catalog['sources'][item['source']]
        config = {'name': item['app'] + '广告专项（可选）',
                  'desc': 'AD-20261020.1；' + item['scope'] + '。独立启停；需设备验收。'}
        if item['domains']:
            config['rules'] = ['DOMAIN,' + host + ',广告拦截' for host in item['domains']]
        http = {}
        if item['mitm']: http['mitm'] = item['mitm']
        if item['rewrite']:
            http['url-rewrite'] = [rule['match'] + ' - ' + rule['upstream_action'] for rule in item['rewrite']]
        if item['script']:
            script = item['script']
            http.setdefault('script', []).append({'match': script['match'], 'name': script['name'],
                                                  'type': 'response', 'require-body': True, 'timeout': 5, 'argument': 'diagnostic=0'})
            config.setdefault('script-providers', {})[script['name']] = {'url': RAW + script['path'], 'interval': 86400}
        if http: config['http'] = http
        header = ('# SPDX-License-Identifier: ' + item['license'] + '\n'
                  '# Reviewed source: ' + source['url'] + '\n'
                  '# License: ' + source['license_file'] + '\n'
                  '# Generated from research/ad-catalog.json; edit the catalog, then regenerate.\n')
        result[item['file']] = header + yaml.safe_dump(config, allow_unicode=True, sort_keys=False, width=120)
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
