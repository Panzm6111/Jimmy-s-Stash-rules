"""Fetch all direct public sources and validate formats before client migration."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.request
import time
import yaml
import community_rules as c
import maintain as m
from provider_sources import plan,ROOT

def check(part):
    request=urllib.request.Request(part['url'],headers={'User-Agent':'Jimmy-public-subscription-check/1'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request,timeout=35) as response:
                raw=response.read(m.LIMIT+1)
                if len(raw)>m.LIMIT:raise ValueError('Source too large')
                status=response.status
            break
        except OSError:
            if attempt==2:raise
            time.sleep(2)
    if part['behavior']=='domain':rules,omitted=c.parse(raw,'domain_yaml');assert not omitted
    else:
        value=yaml.load(raw,Loader=m.UniqueLoader)
        if not isinstance(value,dict) or not isinstance(value.get('payload'),list):raise ValueError('Invalid classical payload')
        rules=value['payload']
        for rule in rules:m.validate_rule(rule)
    if not rules:raise ValueError('Empty source')
    destination=ROOT/'.local/direct-sources'/hashlib.sha256(part['url'].encode()).hexdigest()
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
    return {'url':part['url'],'behavior':part['behavior'],'status':status,'rules':len(rules),'sha256':hashlib.sha256(raw).hexdigest(),'snapshot':part['snapshot'],'cached_file':str(destination.relative_to(ROOT))}

def main():
    p=plan();parts={x['url']:x for v in p['providers'].values() for x in v if not x['url'].startswith('https://raw.githubusercontent.com/Panzm6111/')}
    parts[p['clash_basic_ads']['url']]=p['clash_basic_ads']
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:results=list(pool.map(check,parts.values()))
    (ROOT/'.local/direct-source-check.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':len(results),'domain':sum(x['behavior']=='domain' for x in results),'classical':sum(x['behavior']=='classical' for x in results)}))
    return results

if __name__=='__main__':main()
