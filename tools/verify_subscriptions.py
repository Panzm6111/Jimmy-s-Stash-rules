"""Read-only public source health audit. Never reads private nodes or republishes sources."""
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request
import yaml
import community_rules as c
import maintain as m
from provider_sources import plan, ROOT


def direct_parts(root=ROOT):
    p=plan(root)
    parts={x['url']:x for values in p['providers'].values() for x in values
           if not x['url'].startswith('https://raw.githubusercontent.com/Panzm6111/')}
    parts[p['clash_basic_ads']['url']]=p['clash_basic_ads']
    return list(parts.values())


def fetch(url):
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme!='https' or parsed.netloc!='raw.githubusercontent.com' or parsed.query or parsed.fragment:
        raise ValueError('unapproved public source')
    request=urllib.request.Request(url,headers={'User-Agent':'Jimmy-public-subscription-check/2'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request,timeout=25) as response:
                if response.status!=200 or urllib.parse.urlsplit(response.url).netloc!='raw.githubusercontent.com':
                    raise ValueError('unexpected response')
                raw=response.read(m.LIMIT+1)
                if not raw or len(raw)>m.LIMIT:raise ValueError('empty or oversized response')
                return raw
        except (OSError,TimeoutError):
            if attempt==2:raise
            time.sleep(2)


def parsed_rules(raw,behavior):
    if behavior not in {'domain','classical'}:raise ValueError('unsupported behavior')
    return c.parse(raw,'domain_yaml' if behavior=='domain' else 'classical_yaml')[0]


def check(part,root=ROOT,fetcher=fetch):
    root=Path(root)
    result={k:part[k] for k in ('name','url','behavior','snapshot')}
    try:
        raw=fetcher(part['url'])
        if not raw or len(raw)>m.LIMIT:raise ValueError('invalid response size')
        rules=parsed_rules(raw,part['behavior'])
        before=yaml.load((root/part['snapshot']).read_bytes(),Loader=m.UniqueLoader)['payload']
        delta=m.rule_delta(before,rules)
        destination=root/'.local/direct-sources'/hashlib.sha256(part['url'].encode()).hexdigest()
        destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
        result.update(status=200,rules=len(rules),sha256=hashlib.sha256(raw).hexdigest(),
                      cached_file=destination.relative_to(root).as_posix(),delta=delta,
                      health='review_required' if delta['blocked'] else 'ok')
    except Exception as error:
        # Do not include arbitrary response bodies or exception messages in receipts.
        result.update(health='error',error_type=type(error).__name__)
        if isinstance(error,urllib.error.HTTPError):result['http_status']=error.code
    return result


def run(root=ROOT,fetcher=fetch):
    root=Path(root);checked=datetime.now(timezone.utc).isoformat();parts=direct_parts(root)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda part:check(part,root,fetcher),parts))
    receipt={'checked_at':checked,'ok':all(x['health']=='ok' for x in results),'sources':results,
             'comparison':'reviewed offline snapshots; timestamps do not create commits',
             'boundary':'Public source and route checks only; no private nodes or app requests.'}
    local=root/'.local';local.mkdir(exist_ok=True)
    # Compatibility with native verifier. Failed sources never reuse stale cache evidence.
    usable=[x for x in results if x['health']!='error']
    (local/'direct-source-check.json').write_text(json.dumps(usable,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if len(usable)==len(results):
        from app_route_audit import audit_profiles
        try:receipt['app_routes']=audit_profiles(root,usable)
        except Exception as error:receipt['app_routes']={'ok':False,'status':'error','error_type':type(error).__name__}
        receipt['ok'] &= receipt['app_routes']['ok']
    else:receipt['app_routes']={'ok':False,'status':'not_run_incomplete_sources'}
    (local/'direct-source-health.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    summary=['## Public subscription health',f'Checked at (UTC): {checked}',
             f'Result: {"PASS" if receipt["ok"] else "FAIL - review required"}',
             f'Sources: {len(results)}; healthy: {sum(x["health"]=="ok" for x in results)}',
             'No private subscriptions or device connectivity were tested.',
             '', '| Source | Health | Rules |', '|---|---|---|']
    summary += [f'| {x["name"]} | {x["health"]} | {x.get("rules","unknown")} |' for x in results]
    summary += ['',f'App routing checks: {receipt["app_routes"].get("passed",0)} passed; '
                f'{receipt["app_routes"].get("failed",0)} failed.',
                'Direct client downloads are not gated by this monitor.',
                'Unchanged is healthy after a successful check. No-run is not success.']
    (local/'direct-source-health.md').write_text('\n'.join(summary)+'\n',encoding='utf-8')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as out:out.write('\n'.join(summary)+'\n')
    print(json.dumps({'checked_at':checked,'ok':receipt['ok'],'sources':len(results),
                      'review_required':sum(x['health']=='review_required' for x in results),
                      'errors':sum(x['health']=='error' for x in results),
                      'app_routes_passed':receipt['app_routes'].get('passed',0)}))
    return receipt


if __name__=='__main__':raise SystemExit(0 if run()['ok'] else 1)
