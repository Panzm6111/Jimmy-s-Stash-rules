"""Explicit public subscription plan; no private inputs and no implicit URL fallback."""
import copy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def plan(root=ROOT):
    return json.loads((Path(root)/'research/subscription-plan.json').read_text(encoding='utf-8'))

def apply(config):
    result=copy.deepcopy(config)
    replacements=plan()['providers']
    providers={}
    for name,p in result['rule-providers'].items():
        for part in replacements.get(name,[dict(name=name,**p)]):
            value={k:v for k,v in p.items() if k not in {'behavior','format','url'}}
            value.update({k:part[k] for k in ('behavior','format','url') if k in part})
            providers[part['name']]=value
    result['rule-providers']=providers
    rules=[]
    for rule in result['rules']:
        fields=rule.split(',')
        if fields[0]=='RULE-SET' and fields[1] in replacements:
            rules.extend(','.join([fields[0],part['name'],*fields[2:]]) for part in replacements[fields[1]])
        else:rules.append(rule)
    result['rules']=rules
    return result

def reference_path(url,root=ROOT):
    value=plan(root)
    for part in [p for parts in value['providers'].values() for p in parts]+[value['clash_basic_ads']]:
        if part['url']==url:return part['snapshot']
    raise ValueError('URL absent from reviewed direct subscription plan')

def fixture_payload(classical,behavior):
    if behavior=='classical':return classical
    if behavior!='domain':raise ValueError('Unknown behavior')
    result=[]
    for rule in classical:
        kind,host=rule.split(',',1)
        if kind not in {'DOMAIN','DOMAIN-SUFFIX'}:raise ValueError('Non-domain fixture')
        result.append(('+.' if kind=='DOMAIN-SUFFIX' else '')+host)
    return result
