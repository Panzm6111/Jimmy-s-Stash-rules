#!/usr/bin/env python3
"""Check public URLs only, with TLS verification; never accepts a private subscription URL."""
import argparse
import concurrent.futures
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request
from validate import ROOT, RAW, load

def fetch(item):
    url, expected = item
    try:
        request = urllib.request.Request(url, headers={'User-Agent':'Jimmy-Stash-public-resource-audit/1'})
        with urllib.request.urlopen(request, timeout=25) as response:
            data = response.read(8 * 1024 * 1024 + 1)
            if len(data) > 8 * 1024 * 1024: raise ValueError('response too large')
            same = hashlib.sha256(data).hexdigest() == expected
            return {'url':url, 'status':response.status, 'sha256_matches':same, 'bytes':len(data), 'ok':same}
    except urllib.error.HTTPError as error:
        return {'url':url, 'status':error.code, 'ok':False}
    except Exception as error:
        # Exception string can contain proxy internals. Only expose the type.
        return {'url':url, 'error_type':type(error).__name__, 'ok':False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', choices=['upstream','published'])
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    lock=json.loads((ROOT/'research/sources.lock.json').read_text())
    ai=json.loads((ROOT/'research/ai-sources.json').read_text())
    if args.target == 'upstream':
        resources=[(r['url'],r['source_sha256']) for r in lock['resources']]
        resources += [(r['source_url'],r['source_sha256']) for r in lock['ad_scripts']]
        resources += [(r['url'],r['sha256']) for r in lock.get('ad_supporting_sources', [])]
        resources += [(r['url'],r['sha256']) for r in ai['sources']]
        resources += [(ai['upstream']['license_url'],ai['upstream']['license_sha256'])]
    else:
        paths={'config/main.yaml','config/core.stoverride','config/stash.yaml'}
        paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'modules/ads').glob('*.stoverride'))
        paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'modules/diagnostics').glob('*.stoverride'))
        paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'scripts/ads').glob('*.js'))
        for r in lock['resources']: paths.add(r['output'])
        for r in lock['ad_scripts']: paths.add(r['output'])
        for p in ['rules/openai.yaml','rules/apple.yaml','rules/microsoft.yaml']: paths.add(p)
        paths.update({'research/ai-sources.json',ai['upstream']['license_file']})
        resources=[(RAW+p,hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in sorted(paths)]
    # Shared sources referenced by several apps are fetched/count once; reject conflicting hashes.
    expected_by_url = {}
    for url, expected in resources:
        if url in expected_by_url and expected_by_url[url] != expected: raise ValueError('conflicting source checksum')
        expected_by_url[url] = expected
    resources = sorted(expected_by_url.items())
    # All URLs are manifest-controlled HTTPS public resources, with no user input or auth.
    assert all(url.startswith('https://raw.githubusercontent.com/') and '?' not in url for url,_ in resources)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results=list(executor.map(fetch,resources))
    for r in results:
        name=r['url'].split('raw.githubusercontent.com/',1)[1]
        print(('PASS ' if r['ok'] else 'FAIL ')+name+' '+str(r.get('status',r.get('error_type'))))
    report={'checked_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'target':args.target,'passed':sum(r['ok'] for r in results),'total':len(results),'results':results}
    if args.report:
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(f'{report["passed"]}/{report["total"]} public resources matched expected bytes. This is not a Stash runtime test.')
    return 0 if all(r['ok'] for r in results) else 1

if __name__=='__main__':sys.exit(main())
