"""Representative public app/comment routing guards, not authenticated app tests."""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
import yaml
from validate import ROOT, provider_rules, matches


def decision(config,sets,host):
    for rule in config['rules']:
        fields=rule.split(',')
        if fields[0]=='RULE-SET':
            for item in sets[fields[1]]:
                if matches(item,host):return fields[2],fields[1],item
        elif fields[0]=='MATCH':return fields[1],'MATCH',''
    raise ValueError('missing terminal route')


def audit(config,sets,cases,prefix=''):
    results=[]
    for case in cases:
        host=urlsplit(case['url']).hostname
        policy,provider,matched=decision(config,sets,host)
        expected=case['policy'] if case['policy'] in {'DIRECT','REJECT'} else prefix+case['policy']
        handlers=[]
        if case.get('unmodified_http'):
            for item in config.get('http',{}).get('url-rewrite',[]):
                if re.search(item.rsplit(' - ',1)[0],case['url']):handlers.append('rewrite')
            for item in config.get('http',{}).get('script',[]):
                if re.search(item['match'],case['url']):handlers.append(item['name'])
        results.append(dict(app=case['app'],surface=case['surface'],host=host,expected=expected,
                            actual=policy,provider=provider,matched_rule=matched,
                            http_handlers=handlers,ok=policy==expected and not handlers))
    return results


def audit_profiles(root=ROOT,live_sources=None):
    root=Path(root);cases=json.loads((root/'tests/fixtures/app-routes.json').read_text(encoding='utf-8'))['cases']
    by_url={x['url']:x for x in live_sources or []};profiles=[]
    for filename,prefix in [('config/stash.yaml',''),('config/clash-verge-auto.yaml','Jimmy · ')]:
        config=yaml.safe_load((root/filename).read_text(encoding='utf-8'));sets=provider_rules(config)
        if live_sources is not None:
            from verify_subscriptions import parsed_rules
            for name,provider in config['rule-providers'].items():
                item=by_url.get(provider['url'])
                if item:
                    raw=(root/item['cached_file']).read_bytes()
                    if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('checked source changed')
                    sets[name]=parsed_rules(raw,provider['behavior'])
                elif 'raw.githubusercontent.com/Panzm6111/' not in provider['url']:
                    raise ValueError('missing checked source')
        results=audit(config,sets,cases,prefix)
        profiles.append({'profile':filename,'results':results})
    flat=[x for profile in profiles for x in profile['results']]
    return {'ok':all(x['ok'] for x in flat),'passed':sum(x['ok'] for x in flat),
            'failed':sum(not x['ok'] for x in flat),'profiles':profiles,
            'boundary':'Public host/path samples; no app login, comment loading, posting, IP display or iPhone acceptance.'}


if __name__=='__main__':
    result=audit_profiles()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['ok'] else 1)
