#!/usr/bin/env python3
"""Rebuild/check ad sources, stable entry, docs and optionally offline bundle.

No private input, network or upstream revision changes. Only local output hashes
are refreshed with --write; source pins/checksums are never replaced here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--write',action='store_true')
    p.add_argument('--bundle',action='store_true',help='also render ignored dist/ with inline scripts')
    args=p.parse_args()
    def run(name):
        command=[sys.executable,str(ROOT/'tools'/name)]
        if args.write: command.append('--write')
        subprocess.run(command,cwd=ROOT,check=True)
    for name in ['generate_ad_modules.py','build_ad_scripts.py','build_ad_diagnostics.py','build_subscription.py']:
        run(name)
    path=ROOT/'research/sources.lock.json';lock=json.loads(path.read_text())
    drift=False
    for item in lock['ad_scripts']:
        sha=hashlib.sha256((ROOT/item['output']).read_bytes()).hexdigest()
        if sha!=item['output_sha256']:drift=True;item['output_sha256']=sha
    if drift:
        if not args.write:raise ValueError('output hash drift; review sources and use --write')
        path.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n')
    for name in ['render_app_research.py','render_ad_architecture.py']:run(name)
    if args.bundle:subprocess.run([sys.executable,str(ROOT/'tools/build_local_bundle.py')],cwd=ROOT,check=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
