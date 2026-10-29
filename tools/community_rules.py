#!/usr/bin/env python3
"""Mechanical conversion of maintained rule files. No locally authored host list."""
from pathlib import Path
import json, re, hashlib, argparse
import yaml
ROOT=Path(__file__).resolve().parents[1]
MANIFEST='research/community-sources.json'
KINDS={'DOMAIN','DOMAIN-SUFFIX','DOMAIN-KEYWORD','IP-CIDR','IP-CIDR6'}

def parse(raw, fmt):
    from maintain import UniqueLoader, validate_rule
    omitted=[]
    if fmt=='domain_yaml':
        value=yaml.load(raw, Loader=UniqueLoader)
        if not isinstance(value,dict) or set(value)!={'payload'} or not isinstance(value['payload'],list):
            raise ValueError('invalid maintained payload')
        entries=value['payload'];rules=[]
        for item in entries:
            if not isinstance(item,str) or not item:raise ValueError('invalid maintained domain')
            if item.startswith('+.'):kind,host='DOMAIN-SUFFIX',item[2:]
            elif item.startswith('.'):kind,host='DOMAIN-SUFFIX',item[1:]
            else:kind,host='DOMAIN',item
            if not re.fullmatch(r'[a-zA-Z0-9_.-]+',host):raise ValueError('unsupported maintained domain syntax')
            rules.append(kind+','+host)
    elif fmt=='classical_text':
        rules=[]
        for line in raw.decode('utf-8-sig').splitlines():
            line=line.split('#',1)[0].strip()
            if not line:continue
            if line.split(',')[0] in KINDS:rules.append(line)
            elif line.startswith('URL-REGEX,'):omitted.append(line)
            else:raise ValueError('unreviewed maintained rule kind')
    else:raise ValueError('unknown maintained format')
    rules=list(dict.fromkeys(rules))
    if not rules:raise ValueError('empty maintained list')
    for rule in rules:validate_rule(rule)
    return rules,omitted

def document(rules, sources):
    return ('# Mechanically adapted maintained rules; no locally authored domains.\n'
            '# Sources and original licenses: research/community-sources.json; '+', '.join(sources)+'\n'
            +yaml.safe_dump({'payload':rules},allow_unicode=True,sort_keys=False,width=120))

def generated_documents(root=ROOT, manifest=None):
    root=Path(root);manifest=manifest or json.loads((root/MANIFEST).read_text(encoding='utf-8'))
    result={}
    for aggregate in manifest['aggregates']:
        rules=[]
        for source_id in aggregate['sources']:
            item=next(x for x in manifest['resources'] if x['id']==source_id)
            rules+=yaml.safe_load((root/item['output']).read_text(encoding='utf-8'))['payload']
        if aggregate.get('official_supplement'):
            official=json.loads((root/aggregate['official_supplement']).read_text(encoding='utf-8'))
            additions=['DOMAIN-SUFFIX,'+h for h in official['suffixes']]+['DOMAIN,'+h for h in official['exact_hosts']]
            from maintain import validate_rule
            for rule in additions:validate_rule(rule)
            rules+=additions
        result[aggregate['output']]=document(list(dict.fromkeys(rules)),aggregate['sources'])
    return result

def verify(root=ROOT):
    root=Path(root);m=json.loads((root/MANIFEST).read_text(encoding='utf-8'))
    for item in m['resources']:
        assert hashlib.sha256((root/item['output']).read_bytes()).hexdigest()==item['output_sha256'],item['id']
    for license in m['licenses']:
        assert hashlib.sha256((root/license['file']).read_bytes()).hexdigest()==license['sha256']
    for file,body in generated_documents(root,m).items():
        assert (root/file).read_text(encoding='utf-8')==body,file

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args()
    for file,body in generated_documents().items():
        path=ROOT/file
        if args.write:path.write_text(body,encoding='utf-8',newline='\n')
        elif path.read_text(encoding='utf-8')!=body:raise ValueError('maintained aggregate drift')
    verify();print('Maintained source hashes and aggregates verified.')
if __name__=='__main__':main()
