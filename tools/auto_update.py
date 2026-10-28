#!/usr/bin/env python3
"""Scheduled public-rule updates and narrow, validated Git publication."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re
import subprocess
import os
import sys
import maintain as m

ORIGIN = 'https://github.com/Panzm6111/Jimmy-s-Stash-rules.git'
JOURNAL = '.local/maintenance/pending-publication.json'
EVIDENCE = 'research/last-auto-update.json'

def git(root, *args):
    result = subprocess.run(['git','-C',str(root),*args], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=90,
                            env=dict(os.environ,GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never'))
    if result.returncode:
        raise m.MaintenanceError('publication_git_failed')
    return result.stdout.decode('utf-8').strip()

def paths(root, *args):
    return {p for p in git(root,*args).split(chr(0)) if p}

def dirty(root):
    return paths(root,'diff','--name-only','-z') | paths(root,'ls-files','--others','--exclude-standard','-z')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_branch(root, expected):
    if git(root,'branch','--show-current') != 'main':
        raise m.MaintenanceError('publication_requires_main')
    if git(root,'remote','get-url','origin') != expected:
        raise m.MaintenanceError('unexpected_publication_remote')

def verify_commit(root, journal):
    commit = journal['commit']
    if not re.fullmatch('[0-9a-f]{40}',commit):
        raise m.MaintenanceError('invalid_publication_journal')
    if git(root,'rev-parse','HEAD') != commit or git(root,'rev-parse',commit+'^') != journal['parent']:
        raise m.MaintenanceError('publication_head_changed')
    files = paths(root,'diff-tree','--no-commit-id','--name-only','-r','-z',commit)
    if files != set(journal['files']):
        raise m.MaintenanceError('publication_contains_unexpected_files')
    if 'Jimmy-Auto-Update: v1' not in git(root,'show','-s','--format=%B',commit):
        raise m.MaintenanceError('publication_not_automatic_commit')
    for file, expected in journal['sha256'].items():
        if digest(m.safe_path(root,file)) != expected:
            raise m.MaintenanceError('publication_content_changed')

def push(root, journal):
    verify_branch(root,journal['origin'])
    m.ensure_clean(root,journal['commit'])
    verify_commit(root,journal)
    if git(root,'rev-parse','origin/main') != journal['parent']:
        raise m.MaintenanceError('publication_remote_changed')
    git(root,'push','origin',journal['commit']+':refs/heads/main')
    remote = git(root,'ls-remote','--heads','origin','refs/heads/main').split()
    if not remote or remote[0] != journal['commit']:
        raise m.MaintenanceError('publication_remote_not_verified')
    journal['status']='pushed'
    m.write_json(root/JOURNAL,journal)

def progress_bytes(before, evidence):
    text=before.decode('utf-8')
    if '<!-- sop-current-end -->' not in text:
        raise m.MaintenanceError('main_document_marker_missing')
    # Keep the historical suffix byte-for-byte.
    prefix, suffix=before.split(b'<!-- sop-current-end -->',1)
    current=prefix.decode('utf-8')
    block=('<!-- auto-update:start -->\n自动更新：'+evidence['date']+
           '；普通规则来源 '+evidence['upstream_revision']+
           '。来源/许可、变化量、隔离生成与回归通过；本次只发布核准的公开文件。'
           '发布状态见本机.local维护日志及GitHub对应自动提交。\n<!-- auto-update:end -->\n\n')
    pattern=r'<!-- auto-update:start -->.*?<!-- auto-update:end -->\n*'
    current=re.sub(pattern,lambda _:block,current,flags=re.S) if '<!-- auto-update:start -->' in current else current+block
    return current.encode('utf-8')+b'<!-- sop-current-end -->'+suffix

def execute(root, expected_origin=ORIGIN, checker=m.check_upstreams, updater=m.update):
    root=Path(root)
    verify_branch(root,expected_origin)
    m.ensure_clean(root)
    git(root,'fetch','--no-tags','origin','main')
    head=git(root,'rev-parse','HEAD')
    remote=git(root,'rev-parse','origin/main')
    journal_path=root/JOURNAL
    journal=m.read_json(journal_path) if journal_path.is_file() else None
    if head == remote and journal and journal.get('status')=='pending' and journal.get('commit')==head:
        if journal.get('origin') != expected_origin:
            raise m.MaintenanceError('unexpected_publication_remote')
        verify_commit(root,journal)
        journal['status']='pushed'
        m.write_json(journal_path,journal)
        return {'status':'publication_already_received','commit':head,'pushed':False}
    if head != remote and journal and journal.get('status')=='pending' and journal.get('commit')==head:
        if journal.get('origin') != expected_origin:
            raise m.MaintenanceError('unexpected_publication_remote')
        push(root,journal)
        return {'status':'retried_publication','commit':head,'pushed':True}
    if head != remote:
        # ff-only refuses unpublished local commits or diverged histories.
        git(root,'merge','--ff-only','origin/main')
        head=git(root,'rev-parse','HEAD')
        if head != remote:
            raise m.MaintenanceError('unreviewed_local_commits')
        m.ensure_clean(root,head)
    before_main=(root/'PROGRESS.md').read_bytes()
    report=checker(root)
    m.write_report(root,report)
    if not report['ok']:
        raise m.MaintenanceError('all_sources_not_checked')
    backup=updater(root,report)
    if not backup:
        m.ensure_clean(root,head)
        return {'status':'no_relevant_changes','committed':False,'pushed':False,
                'review_required':report['summary']['review-required']}
    manifest=m.read_json(root/'.local/maintenance/backups'/backup/'manifest.json')
    generated=set(m.GENERATED)|{i['output'] for i in m.read_json(root/'research/sources.lock.json')['resources']}
    if (root/'research/community-sources.json').is_file():
        community=m.read_json(root/'research/community-sources.json')
        generated|={x['output'] for x in community['resources']}|{x['output'] for x in community['aggregates']}
    files={i['path'] for i in manifest['files']}
    if not files <= generated or dirty(root)!=files or git(root,'diff','--cached','--name-only'):
        raise m.MaintenanceError('unrelated_worktree_changes')
    expected={i['path']:i['after_sha256'] for i in manifest['files']}
    for file, sha in expected.items():
        if digest(m.safe_path(root,file))!=sha:
            raise m.MaintenanceError('publication_content_changed')
    if git(root,'rev-parse','HEAD')!=head or (root/'PROGRESS.md').read_bytes()!=before_main:
        raise m.MaintenanceError('publication_head_or_main_changed')
    evidence={'date':datetime.now(timezone(timedelta(hours=8))).isoformat(),
              'upstream_revision':report['repositories'][m.PRIMARY]['head'],'upstream_heads':report['repositories'],
              'base_head':head,'files':sorted(files),
              'validation':'isolated source/license/delta/build/project/JS/private/maintenance/Clash/auto-publication regressions',
              'review_required':report['summary']['review-required'],'device_tested':False}
    # No timestamp-only evidence is generated unless actual rule changes applied.
    m.atomic_write(root/'PROGRESS.md',progress_bytes(before_main,evidence))
    m.write_json(root/EVIDENCE,evidence)
    files|={'PROGRESS.md',EVIDENCE}
    expected.update({f:digest(root/f) for f in ('PROGRESS.md',EVIDENCE)})
    if dirty(root)!=files or git(root,'diff','--cached','--name-only'):
        raise m.MaintenanceError('unrelated_worktree_changes')
    git(root,'diff','--check')
    from scan_secrets import inspect
    if any(inspect((root/f).read_text(encoding='utf-8'),f) for f in files):
        raise m.MaintenanceError('publication_secret_pattern')
    git(root,'add','--',*sorted(files))
    if paths(root,'diff','--cached','--name-only','-z')!=files:
        raise m.MaintenanceError('unrelated_staged_changes')
    # Verify exactly the staged bytes, not only a list of filenames.
    for file, sha in expected.items():
        data=subprocess.check_output(['git','-C',str(root),'show',':'+file])
        if hashlib.sha256(data).hexdigest()!=sha:
            raise m.MaintenanceError('staged_content_changed')
    git(root,'commit','-m','Update reviewed public rule snapshots\n\nJimmy-Auto-Update: v1')
    commit=git(root,'rev-parse','HEAD')
    journal={'status':'pending','commit':commit,'parent':head,'origin':expected_origin,
             'files':sorted(files),'sha256':expected}
    m.write_json(journal_path,journal)
    push(root,journal)
    return {'status':'updated_and_pushed','commit':commit,'files':sorted(files),'pushed':True}

def main():
    try:
        with m.maintenance_lock(m.ROOT):
            result=execute(m.ROOT)
            m.write_json(m.maintenance_dir(m.ROOT)/'publication-latest.json',result)
            print(json.dumps(result,ensure_ascii=False))
        return 0
    except Exception as error:
        code=error.code if isinstance(error,m.MaintenanceError) else type(error).__name__
        m.write_json(m.maintenance_dir(m.ROOT)/'publication-latest.json',{'status':'failed','error_code':code})
        print('Automatic update stopped: '+code)
        return 1
if __name__=='__main__':raise SystemExit(main())
