"""Refresh only necessary public conversions; publication is a separate verified step."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import yaml
import maintain as m
import community_rules as c
from provider_sources import plan

ROOT=Path(__file__).resolve().parents[1]
STATE='.local/cloud-update.json'

def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.PIPE).decode().strip()

def convert(raw,fmt):
    if fmt=='classical_text':return c.parse(raw,fmt)
    obj=yaml.load(raw,Loader=m.UniqueLoader)
    if not isinstance(obj,dict) or set(obj)!={'payload'} or not isinstance(obj['payload'],list):raise ValueError('Invalid source payload')
    retained=[];omitted=[]
    for rule in obj['payload']:
        if not isinstance(rule,str):raise ValueError('Invalid rule')
        kind=rule.split(',')[0]
        if kind in m.RULE_KINDS:m.validate_rule(rule);retained.append(rule)
        elif kind in {'PROCESS-NAME','IP-ASN'}:omitted.append(rule)
        else:raise ValueError('Unknown upstream rule kind requires review')
    if not retained:raise ValueError('Empty converted source')
    return list(dict.fromkeys(retained)),omitted

def refresh(root=ROOT,fetcher=m.fetch_public,resolver=m.resolve_head):
    root=Path(root);m.ensure_clean(root)
    head=git(root,'rev-parse','HEAD');pending={};manifests={};heads={};deltas=[]
    for spec in plan(root)['cloud_sources']:
        manifest=manifests.setdefault(spec['manifest'],m.read_json(root/spec['manifest']))
        src=next(x for x in manifest['resources'] if x['output']==spec['output'])
        primary=spec['manifest'].endswith('sources.lock.json') and not spec['manifest'].endswith('community-sources.json')
        repo='blackmatrix7/ios_rule_script' if primary else src['repository']
        ref='refs/heads/master' if primary else src.get('ref','HEAD')
        key=(repo,ref)
        if key not in heads:heads[key]=resolver(repo,ref)
        revision=heads[key];path=src['source_path'] if primary else src['path']
        if primary:
            license_raw=fetcher(m.source_url(repo,revision,'LICENSE'))
            expected=hashlib.sha256((root/manifest['upstream']['license_file']).read_bytes()).hexdigest()
            if hashlib.sha256(license_raw).hexdigest()!=expected:raise ValueError('License changed')
        else:
            lic=next(x for x in manifest['licenses'] if x['repository']==repo)
            licrev=resolver(repo,lic.get('ref','HEAD'));licraw=fetcher(m.source_url(repo,licrev,lic['path']))
            if hashlib.sha256(licraw).hexdigest()!=lic['sha256']:raise ValueError('License changed')
        url=m.source_url(repo,revision,path);raw=fetcher(url)
        rules,omitted=convert(raw,spec['format'])
        before=yaml.safe_load((root/src['output']).read_text(encoding='utf-8'))['payload']
        delta=m.rule_delta(before,rules);deltas.append(dict(output=src['output'],**delta))
        if delta['blocked']:raise ValueError('Rule delta requires review: '+src['output'])
        if not delta['added'] and not delta['removed']:continue
        body=c.document(rules,[repo+'/'+path+' @ '+revision])
        pending[src['output']]=body
        src.update(url=url,source_sha256=hashlib.sha256(raw).hexdigest(),output_sha256=hashlib.sha256(body.encode()).hexdigest(),retained=len(rules),omitted=omitted)
        if not primary:src['revision']=revision
    # Fetch, license, format and delta validation finish before any checkout mutation.
    if not pending:
        state={'status':'no_changes','base_head':head,'deltas':deltas,'files':{}}
    else:
        for path,body in pending.items():(root/path).write_text(body,encoding='utf-8',newline='\n')
        for path,data in manifests.items():(root/path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        subprocess.run([sys.executable,'-X','utf8','tools/build_ads.py','--write'],cwd=root,check=True)
        from datetime import datetime,timezone,timedelta
        from auto_update import progress_bytes
        evidence={'date':datetime.now(timezone(timedelta(hours=8))).isoformat(),
                  'upstream_revision':heads.get(('blackmatrix7/ios_rule_script','refs/heads/master'),'unchanged'),
                  'source_heads':{repo+' '+ref:sha for (repo,ref),sha in heads.items()},
                  'deltas':deltas,'device_tested':False,'status':'converted; publication follows workflow validation'}
        main=root/'PROGRESS.md'
        m.atomic_write(main,progress_bytes(main.read_bytes(),evidence))
        m.write_json(root/'research/last-cloud-update.json',evidence)
        changed=git(root,'diff','--name-only').splitlines()
        allowed=set(m.GENERATED)|{x['output'] for x in m.read_json(root/'research/sources.lock.json')['resources']}
        cm=m.read_json(root/'research/community-sources.json');allowed|={x['output'] for x in cm['resources']}|{x['output'] for x in cm['aggregates']}
        allowed|={'PROGRESS.md','research/last-cloud-update.json'}
        if not set(changed)<=allowed:raise ValueError('Unexpected generated change: '+str(sorted(set(changed)-allowed)))
        state={'status':'updated','base_head':head,'deltas':deltas,'files':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in changed}}
    (root/'.local').mkdir(exist_ok=True)
    m.write_json(root/STATE,state)
    print(json.dumps({'status':state['status'],'converted_sources':len(deltas),'changed_files':len(state['files'])}))
    return state

def publish(root=ROOT):
    root=Path(root);state=m.read_json(root/STATE)
    if state['status']=='no_changes':print('No semantic rule changes; no commit or push.');return
    if git(root,'rev-parse','HEAD')!=state['base_head']:raise ValueError('HEAD changed during validation')
    origin=git(root,'remote','get-url','origin')
    if git(root,'branch','--show-current')!='main' or origin.removesuffix('.git')!='https://github.com/Panzm6111/Jimmy-s-Stash-rules':raise ValueError('Unexpected publication target')
    if git(root,'diff','--cached','--name-only'):raise ValueError('Unexpected staged changes')
    if set(git(root,'diff','--name-only').splitlines())!=set(state['files']):raise ValueError('Checkout changed during validation')
    from scan_secrets import inspect
    for path,digest in state['files'].items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest()!=digest or inspect((root/path).read_text(encoding='utf-8'),path):raise ValueError('Publication content changed or secret found')
    git(root,'diff','--check');git(root,'add','--',*sorted(state['files']))
    if set(git(root,'diff','--cached','--name-only').splitlines())!=set(state['files']):raise ValueError('Unexpected staged files')
    for path,digest in state['files'].items():
        data=subprocess.check_output(['git','-C',str(root),'show',':'+path])
        if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('Staged bytes differ')
    git(root,'commit','-m','Refresh necessary public rule conversions [skip ci]')
    git(root,'push','origin','HEAD:refs/heads/main')
    commit=git(root,'rev-parse','HEAD')
    if git(root,'ls-remote','origin','refs/heads/main').split()[0]!=commit:raise ValueError('Remote verification failed')
    print(json.dumps({'status':'pushed','commit':commit}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['refresh','publish']);args=parser.parse_args()
    refresh() if args.mode=='refresh' else publish()
