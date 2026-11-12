#!/usr/bin/env python3
"""Generate the sole Clash remote profile from the maintained Stash routing source."""
import argparse, copy, hashlib
from pathlib import Path
import yaml
from config_helpers import pool_tolerance_ms
ROOT=Path(__file__).resolve().parents[1]
AIRPORT_INFO_EXCLUDE=r'(?i)(请勿连接|跳转域名)'
DOWNLOAD_GROUP='Jimmy · 订阅更新'

def remote_profile(source):
    """Full remotely replaceable structure; only the airport URL belongs in local Merge."""
    result=copy.deepcopy(source)
    result.update(global_merge(source))
    # HTTP-specific exceptions and per-app ads belong to Stash. The Clash subscription
    # uses the whole maintained basic advertising set, not our per-app selections.
    removed={'广告路径例外','App广告域名','手机广告补充'}
    result['rules']=[r for r in result['rules'] if not (r.startswith('RULE-SET,') and r.split(',')[1] in removed)]
    for name in removed:del result['rule-providers'][name]
    from provider_sources import plan
    result['rule-providers']['基础广告'].update({k:plan()['clash_basic_ads'][k] for k in ('url','behavior','format')})
    result['profile']={'store-selected':True}
    # Local payload/cache bootstraps this pool when the subscription needs a proxy.
    # Keep download failover independent of the user's manual/AI/social selections.
    manual=next(g for g in result['proxy-groups'] if g['name']=='Jimmy · 手动节点')
    result['proxy-groups'].append({'name':DOWNLOAD_GROUP,'type':'fallback','use':['机场'],
        'filter':manual['filter'],'url':'https://www.gstatic.com/generate_204',
        'interval':300,'lazy':False,'timeout':5000,'max-failed-times':1,
        'empty-fallback':'REJECT','hidden':True})
    result['proxy-providers']['机场']['proxy']=DOWNLOAD_GROUP
    # Groups using `use` rely on provider health checks, not their own timer.
    result['proxy-providers']['机场']['health-check'].update(
        enable=True, interval=60, lazy=False, timeout=5000, **{'expected-status':204})
    result['proxy-groups'][-1]['expected-status']=204
    # Airports may vary subscription format by User-Agent.
    # Request the same Clash YAML representation as the supported desktop client.
    result['proxy-providers']['机场']['header']={'User-Agent':['clash-verge/v2.5.8']}
    result['proxy-providers']['机场']['exclude-filter']=AIRPORT_INFO_EXCLUDE
    return result

def global_merge(source):
    """Pure overlay: keep the airport's node/provider and application settings."""
    overlay={key:copy.deepcopy(source[key]) for key in ('proxy-groups','rule-providers','rules')}
    names={group['name']:'Jimmy · '+group['name'] for group in overlay['proxy-groups']}
    for group in overlay['proxy-groups']:
        original=group['name']
        if 'use' in group:
            del group['use']
            group.update({'include-all':True,'empty-fallback':'REJECT'})
            if group['type']=='url-test' or original=='手动节点':
                group['proxies']=[name for name in group.get('proxies',[]) if name!='REJECT']
                if not group['proxies']:del group['proxies']
        if group['type']=='url-test':
            # UI guard only: Mihomo's API can still pin a URLTest pool.
            group.update(hidden=True, tolerance=pool_tolerance_ms(original), **{'expected-status':204})
        elif group['type']=='select' and original!='手动节点':
            # Raw airport nodes have one explicit manual entry point.
            for key in ('include-all','empty-fallback','filter'):
                group.pop(key,None)
        group['name']=names[original]
        if 'proxies' in group:group['proxies']=[names.get(name,name) for name in group['proxies']]
    for index,rule in enumerate(overlay['rules']):
        parts=rule.split(',')
        if parts[0] not in {'RULE-SET','GEOIP','MATCH'}:
            raise ValueError('Review Merge target parsing for new rule kind')
        target=1 if parts[0]=='MATCH' else 2
        parts[target]=names.get(parts[target],parts[target])
        overlay['rules'][index]=','.join(parts)
    for name,provider in overlay['rule-providers'].items():
        provider.update(proxy=names['自动节点'],
                        path='./ruleset/jimmy-merge-'+hashlib.sha256(name.encode()).hexdigest()[:12]+'.yaml')
    return overlay
def base_profile():
    """Internal preparation model; never a second published configuration."""
    source=yaml.safe_load((ROOT/'config/stash.yaml').read_text(encoding='utf-8'))
    from stash_ai_guard import for_clash
    from validate import merged
    source=for_clash(source, merged())
    result={k:copy.deepcopy(v) for k,v in source.items() if k not in {'http','script-providers'}}
    result['mixed-port']=7890
    result['dns']['enable']=True
    result['proxy-providers']['机场']['path']='./providers/jimmy-airport.yaml'
    for name,p in result['rule-providers'].items():
        p.update(type='http',format='yaml',interval=86400,
                 path='./ruleset/jimmy-'+hashlib.sha256(name.encode()).hexdigest()[:12]+'.yaml')
    assert result['rules']==source['rules'] and result['proxy-groups']==source['proxy-groups']
    return result

def render():
    result=base_profile()
    remote=('# Generated by tools/build_clash.py; full remotely updated Clash Verge profile.\n'
            '# Import this URL as a remote profile; enable auto update, interval 1440 minutes.\n'
            '# Local profile Merge: private airport URL and personal settings only; no Jimmy routing snapshot.\n'
            '# See docs/CLASH-VERGE.md. Do not upload your merged private configuration.\n'
            +yaml.safe_dump(remote_profile(result),allow_unicode=True,sort_keys=False,width=120))
    return {'config/clash-verge-auto.yaml':remote}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args()
    drift=[]
    for name,body in render().items():
        path=ROOT/name
        if not path.exists() or path.read_text(encoding='utf-8')!=body:
            drift.append(name)
            if args.write:path.write_text(body,encoding='utf-8',newline='\n')
    print(str(len(drift))+' Clash files '+('written' if args.write else 'differ'))
    return 0 if args.write or not drift else 1
if __name__=='__main__':raise SystemExit(main())
