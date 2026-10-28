#!/usr/bin/env python3
"""Bounded credential pattern scan; prints locations/rule names, NEVER matched values."""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----'),
    'github-token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b'),
    'aws-access-id': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'jwt': re.compile(r'\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\b'),
    'sensitive-url-query': re.compile(r'[?&](?:token|access_token|pt_key|auth|password|api_key)=([A-Za-z0-9_%+./=-]{12,})', re.I),
    'account-cookie': re.compile(r'\b(?:pt_key|SESSDATA|P00001|userToken|pkey)=[A-Za-z0-9_%+./-]{16,}'),
    'uuid': re.compile(r'\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b'),
    'yaml-credential': re.compile(r'^\s*(?:password|uuid|cookie|token|authorization|client-key|ca-p12):\s*["\']?([^\s"\'#]+)', re.I | re.M)
}
PLACEHOLDERS = {'EXAMPLE_NOT_A_SECRET', '00000000-0000-4000-8000-000000000000', 'REPLACE_ON_DEVICE', '{}', 'null', '[]'}

def inspect(text, location):
    hits = []
    for name, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            candidate = match.group(1) if match.lastindex else match.group()
            if candidate in PLACEHOLDERS: continue
            line = text.count('\n', 0, match.start()) + 1
            hits.append((location, line, name))
    return hits

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', action='store_true', help='scan every reachable blob, not just current HEAD')
    args = parser.parse_args()
    paths = git('ls-files', '-z', '--cached', '--others', '--exclude-standard').decode().split('\0')
    findings = []
    count = 0
    for path in paths:
        if not path: continue
        file = ROOT / path
        if file.is_symlink():
            findings.append((path, 0, 'symlink-needs-review')); continue
        if not file.is_file(): continue
        data = file.read_bytes()
        if b'\0' in data:
            findings.append((path, 0, 'binary-needs-review')); continue
        findings += inspect(data.decode('utf-8', errors='replace'), path)
        count += 1
    blobs = 0
    if args.history:
        # Scan publishable Git history. Codex's private turn-diff capture refs
        # can contain ignored/uncommitted context and are never pushed.
        for item in git('rev-list', '--objects', '--branches', '--remotes', '--tags').decode().splitlines():
            oid = item.split(' ', 1)[0]
            if git('cat-file', '-t', oid).strip() != b'blob': continue
            data = git('cat-file', 'blob', oid)
            findings += inspect(data.decode('utf-8', errors='replace'), 'git-blob:' + oid[:12])
            blobs += 1
    for path, line, rule in findings:
        print(f'REVIEW {path}:{line} [{rule}]')
    print(f'Secret-pattern scan: {count} current files, {blobs} reachable historical blobs, {len(findings)} findings.')
    print('Pattern scanning cannot prove absence of unknown credential formats. Review staged diffs before publishing.')
    return 1 if findings else 0

if __name__ == '__main__': sys.exit(main())
