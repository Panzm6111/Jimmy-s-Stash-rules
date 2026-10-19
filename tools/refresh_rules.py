#!/usr/bin/env python3
"""Refresh reviewed rule snapshots at an explicit full commit, without touching credentials."""
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import re
import sys
import urllib.request
import yaml
from validate import ROOT, RULE_KINDS

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision',required=True,help='reviewed blackmatrix7 full 40-character Git commit')
    parser.add_argument('--write',action='store_true',help='write only after ALL source files validate; otherwise preview counts')
    args=parser.parse_args()
    if not re.fullmatch('[0-9a-f]{40}',args.revision):parser.error('full lowercase commit required')
    lock=json.loads((ROOT/'research/sources.lock.json').read_text())
    license_url=f'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/{args.revision}/LICENSE'
    with urllib.request.urlopen(license_url,timeout=30) as response: license_bytes=response.read(256*1024)
    if hashlib.sha256(license_bytes).hexdigest()!=hashlib.sha256((ROOT/lock['upstream']['license_file']).read_bytes()).hexdigest():
        raise ValueError('upstream license changed; manual review required before refreshing')
    pending=[]
    for item in lock['resources']:
        url=f'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/{args.revision}/{item["source_path"]}'
        with urllib.request.urlopen(url,timeout=30) as response:
            raw=response.read(8*1024*1024+1)
        if len(raw)>8*1024*1024:raise ValueError('response too large')
        # Preserve integrity checks when replaying the already-reviewed revision.
        if args.revision==lock['upstream']['revision']:
            assert hashlib.sha256(raw).hexdigest()==item['source_sha256'],'source checksum mismatch'
        payload=yaml.safe_load(raw)['payload']
        if not isinstance(payload,list) or not payload or not all(isinstance(x,str) for x in payload):raise ValueError('invalid source payload')
        if 'selection' in item:
            available=set(payload)
            for value in item['selection']:
                kind,domain=value.split(',',1)
                if item['source_path'].endswith('_Classical.yaml'):
                    choices={value}
                else:
                    choices={domain} if kind=='DOMAIN' else {'+.'+domain,'.'+domain}
                if not available.intersection(choices):raise ValueError('curated ad source changed; manual review required')
            values=item['selection'];omitted=[]
            header='# Curated subset of blackmatrix7 '+item['source_path'].rsplit('/',1)[1]+', GPL-2.0.\n# Shared ad SDKs; does not guarantee any App splash removal.\n'
        else:
            values=list(dict.fromkeys(x for x in payload if x.split(',')[0] in RULE_KINDS))
            omitted=[x for x in payload if x.split(',')[0] not in RULE_KINDS]
            header=f'# Derived from blackmatrix7/ios_rule_script; GPL-2.0.\n# Source: {item["source_path"]} @ {args.revision}\n# Only native basic rule kinds retained; see research/sources.lock.json.\n'
        out=(header+yaml.safe_dump({'payload':values},allow_unicode=True,sort_keys=False,width=120)).encode()
        entry=dict(item,url=url,source_sha256=hashlib.sha256(raw).hexdigest(),output_sha256=hashlib.sha256(out).hexdigest(),retained=len(values))
        if 'omitted' in item:entry['omitted']=omitted
        pending.append((entry,out))
        print(item['output'],len(values),'rules; omitted',len(omitted))
    if args.write:
        for entry,data in pending:(ROOT/entry['output']).write_bytes(data)
        lock['resources']=[e for e,_ in pending];lock['upstream']['revision']=args.revision
        lock['checked_at']=datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat()
        (ROOT/'research/sources.lock.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
        print('Snapshots updated. Review diff, update verification date, run tools/validate.py before commit.')
    else:print('Preview only. No files changed.')
    return 0
if __name__=='__main__':sys.exit(main())
