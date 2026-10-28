#!/usr/bin/env python3
"""Refresh whole maintained community sources at revisions already checked by maintain.py."""
import argparse,json,hashlib
from pathlib import Path
import community_rules as c

def refresh(root, report, fetcher):
    root=Path(root);m=json.loads((root/c.MANIFEST).read_text(encoding='utf-8'))
    # Licenses are independently tracked on their real branch, not the generated-data branch.
    for lic in m['licenses']:
        item=next(x for x in report['files'] if x['repository']==lic['repository'] and x['path']==lic['path'] and 'license' in x['categories'])
        raw=fetcher(item['latest_url'])
        if hashlib.sha256(raw).hexdigest()!=lic['sha256']:raise ValueError('community license changed')
    pending={}
    for src in m['resources']:
        item=next(x for x in report['files'] if x['repository']==src['repository'] and x['path']==src['path'] and src['output'] in x['outputs'])
        raw=fetcher(item['latest_url'])
        digest=hashlib.sha256(raw).hexdigest()
        if digest!=item['latest_sha256']:raise ValueError('community source changed after check')
        rules,omitted=c.parse(raw,src['source_format'])
        body=c.document(rules,[src['id']])
        pending[src['output']]=body
        if digest!=src['source_sha256']:
            src.update(revision=item['latest_revision'],url=item['latest_url'],source_sha256=digest,
                       output_sha256=hashlib.sha256(body.encode()).hexdigest(),retained=len(rules),omitted=omitted)
    for path,body in pending.items():(root/path).write_text(body,encoding='utf-8',newline='\n')
    for path,body in c.generated_documents(root,m).items():(root/path).write_text(body,encoding='utf-8',newline='\n')
    (root/c.MANIFEST).write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    c.verify(root)

def main():
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    from maintain import fetch_public
    refresh(c.ROOT,json.loads(a.report.read_text(encoding='utf-8')),fetch_public)
    print('Maintained community sets refreshed from checked public revisions.')
if __name__=='__main__':main()
