#!/usr/bin/env python3
"""本地上游维护：默认只检查；普通规则隔离更新；专项脚本只报告差异。

只访问清单内的公开 GitHub 文件。不接收机场 URL、凭据或配置上传参数。
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

import yaml

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = 'blackmatrix7/ios_rule_script'
REPOSITORIES = frozenset({PRIMARY, 'fmz200/wool_scripts', 'app2smile/rules',
                          'NobyDa/Script', 'Maasea/sgmodule', 'v2fly/domain-list-community'})
SHA = re.compile(r'[0-9a-f]{40}\Z')
DIGEST = re.compile(r'[0-9a-f]{64}\Z')
LIMIT = 8 * 1024 * 1024
GENERATED = frozenset({'config/clash-verge.yaml', 'config/clash-verge.js', 'config/stash.yaml', 'research/sources.lock.json',
                       'docs/AD-MODULES.md', 'docs/APP-INVENTORY.md',
                       'docs/AD-ARCHITECTURE.md', 'research/ad-architecture-audit.json',
                       'research/local-bundle-audit.json'})
RULE_KINDS = frozenset({'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD', 'IP-CIDR', 'IP-CIDR6'})
STATUS = {'unchanged': '内容未变', 'rules-update': '普通规则变化，可进入隔离验证',
          'review-required': '需审查适配，不自动覆盖', 'reference-changed': '参考资料变化，未自动采用',
          'error': '检查失败，不能判断是否有更新'}


class MaintenanceError(Exception):
    """Only fixed machine-readable codes may leave the implementation."""
    def __init__(self, code):
        self.code = code if re.fullmatch(r'[a-z0-9_:-]+', str(code)) else 'maintenance_failed'
        super().__init__(self.code)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def safe_path(root, relative):
    path = PurePosixPath(relative)
    if not relative or path.is_absolute() or '..' in path.parts or '\\' in relative or ':' in relative:
        raise MaintenanceError('unsafe_path')
    result = root.joinpath(*path.parts)
    # Reject symlinks, including any parent directory, without following them.
    cursor = result
    while cursor != root:
        if cursor.is_symlink():
            raise MaintenanceError('symlink_rejected')
        cursor = cursor.parent
    return result


def parse_source_url(url):
    value = urllib.parse.urlsplit(url)
    if value.scheme != 'https' or value.netloc != 'raw.githubusercontent.com' or value.query or value.fragment:
        raise MaintenanceError('non_public_source')
    fields = value.path.lstrip('/').split('/', 3)
    if len(fields) != 4:
        raise MaintenanceError('invalid_source_url')
    owner, name, revision, path = fields
    repository = owner + '/' + name
    if repository not in REPOSITORIES or not SHA.fullmatch(revision):
        raise MaintenanceError('unapproved_source')
    if not path or any(x in ('', '.', '..') for x in path.split('/')) or not re.fullmatch(r'[A-Za-z0-9_./!+@-]+', path):
        raise MaintenanceError('invalid_source_path')
    return repository, revision, path


def source_url(repository, revision, path):
    url = f'https://raw.githubusercontent.com/{repository}/{revision}/{path}'
    parse_source_url(url)
    return url


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def collect_sources(root):
    """Collect only existing manifest sources. Missing native-reference hashes use pinned bytes."""
    root = Path(root)
    lock = read_json(root / 'research/sources.lock.json')
    ai = read_json(root / 'research/ai-sources.json')
    catalog = read_json(root / 'research/ad-catalog.json')
    entries = {}

    def add(url, expected, category, output=None):
        repository, revision, path = parse_source_url(url)
        if expected is not None and not DIGEST.fullmatch(expected):
            raise MaintenanceError('invalid_source_hash')
        key = (repository, revision, path)
        entry = entries.setdefault(key, {'repository': repository, 'path': path,
                                        'pinned_revision': revision, 'expected_sha256': expected,
                                        'categories': [], 'outputs': []})
        if entry['expected_sha256'] and expected and entry['expected_sha256'] != expected:
            raise MaintenanceError('conflicting_source_hash')
        if expected:
            entry['expected_sha256'] = expected
        if category not in entry['categories']:
            entry['categories'].append(category)
        if output and output not in entry['outputs']:
            entry['outputs'].append(output)

    for item in lock['resources']:
        add(item['url'], item['source_sha256'], 'rules', item['output'])
    for item in lock['ad_scripts']:
        add(item['source_url'], item['source_sha256'], 'script', item['output'])
        if item.get('native_reference'):
            add(source_url(item['repository'], item['revision'], item['native_reference']),
                None, 'script')
    for item in lock.get('ad_supporting_sources', []):
        category = 'license' if item['url'].rsplit('/', 1)[-1].lower() in ('license', 'license.md', 'license.txt') else 'reference'
        if parse_source_url(item['url'])[0] == 'Maasea/sgmodule':
            category = 'reference'  # investigated resources are not active modules
        add(item['url'], item['sha256'], category)
    for item in catalog['sources'].values():
        add(item['url'], item['sha256'], 'script')
    for item in ai['sources']:
        add(item['url'], item['sha256'], 'curated', ai['output'])
    add(ai['upstream']['license_url'], ai['upstream']['license_sha256'], 'license')
    # Licenses for actually adopted repositories; these local copies are reviewed baselines.
    licenses = {PRIMARY: ('LICENSE', 'licenses/blackmatrix7-GPL-2.0.txt'),
                'fmz200/wool_scripts': ('LICENSE', 'licenses/fmz200-GPL-3.0.txt'),
                'app2smile/rules': ('LICENSE.md', 'licenses/app2smile-MIT.txt'),
                'NobyDa/Script': ('LICENSE', 'licenses/NobyDa-GPL-3.0.txt')}
    revisions = {(entry['repository'], entry['pinned_revision']) for entry in entries.values()}
    for repository, revision in revisions:
        if repository in licenses:
            remote_path, local_path = licenses[repository]
            add(source_url(repository, revision, remote_path),
                sha256((root / local_path).read_bytes()), 'license')
    return sorted(entries.values(), key=lambda e: (e['repository'], e['path'], e['pinned_revision']))


class PublicRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        parse_source_url(newurl)
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def fetch_public(url):
    parse_source_url(url)
    for attempt in range(2):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'Jimmy-Stash-maintenance/1'})
            with urllib.request.build_opener(PublicRedirect()).open(request, timeout=20) as response:
                data = response.read(LIMIT + 1)
            if not data or len(data) > LIMIT:
                raise MaintenanceError('empty_or_oversized_source')
            return data
        except MaintenanceError:
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            if attempt:
                raise MaintenanceError('public_download_failed') from None
            time.sleep(1)
    raise MaintenanceError('public_download_failed')


def git(root, *args, timeout=40):
    try:
        result = subprocess.run(['git', '-C', str(root), *args], check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return result.stdout
    except (OSError, subprocess.SubprocessError):
        raise MaintenanceError('git_failed') from None


def resolve_head(repository):
    if repository not in REPOSITORIES:
        raise MaintenanceError('unapproved_repository')
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0')
    for attempt in range(2):
        try:
            result = subprocess.run(['git', '-c', 'credential.helper=', 'ls-remote',
                                     f'https://github.com/{repository}.git', 'HEAD'],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    timeout=25, env=env, check=True)
            lines = result.stdout.decode('ascii').splitlines()
            hashes = [line.split()[0] for line in lines if len(line.split()) == 2 and line.split()[1] == 'HEAD']
            if len(hashes) != 1 or not SHA.fullmatch(hashes[0]):
                raise MaintenanceError('invalid_upstream_head')
            return hashes[0]
        except (OSError, subprocess.SubprocessError, UnicodeError):
            if attempt:
                raise MaintenanceError('upstream_head_failed') from None
            time.sleep(1)
    raise MaintenanceError('upstream_head_failed')


def check_upstreams(root, fetcher=fetch_public, head_resolver=resolve_head):
    sources = collect_sources(Path(root))
    repositories = sorted({item['repository'] for item in sources})

    def head(repository):
        try:
            revision = head_resolver(repository)
            if not SHA.fullmatch(revision):
                raise MaintenanceError('invalid_upstream_head')
            return repository, {'status': 'ok', 'head': revision}
        except Exception as error:
            return repository, {'status': 'error', 'error_type': type(error).__name__}

    with ThreadPoolExecutor(max_workers=4) as executor:
        heads = dict(executor.map(head, repositories))

    def compare(item):
        entry = dict(item)
        upstream = heads[item['repository']]
        if upstream['status'] != 'ok':
            return dict(entry, status='error', error_type='UpstreamHeadUnavailable')
        try:
            revision = upstream['head']
            url = source_url(item['repository'], revision, item['path'])
            expected = item['expected_sha256']
            if expected is None:
                expected = sha256(fetcher(source_url(item['repository'], item['pinned_revision'], item['path'])))
            raw = fetcher(url)
            if not raw or len(raw) > LIMIT:
                raise MaintenanceError('empty_or_oversized_source')
            digest = sha256(raw)
            if 'rules' in item['categories']:
                rule_payload(raw)
            if revision == item['pinned_revision'] and digest != expected:
                raise MaintenanceError('pinned_source_integrity_failed')
            if digest == expected:
                status = 'unchanged'
            elif 'rules' in item['categories']:
                status = 'rules-update'
            elif any(x in item['categories'] for x in ('script', 'license', 'curated')):
                status = 'review-required'
            else:
                status = 'reference-changed'
            return dict(entry, expected_sha256=expected, latest_revision=revision,
                        latest_url=url, latest_sha256=digest, bytes=len(raw), status=status)
        except Exception as error:
            details = {'error_type': type(error).__name__}
            if isinstance(error, MaintenanceError):
                details['error_code'] = error.code
            return dict(entry, status='error', **details)

    with ThreadPoolExecutor(max_workers=4) as executor:
        files = list(executor.map(compare, sources))
    return {'schema': 1, 'checked_at_utc': now(), 'operation': 'check',
            'repositories': heads, 'files': files,
            'summary': {key: sum(item['status'] == key for item in files) for key in STATUS},
            'ok': all(item['status'] != 'error' for item in files),
            'notice': '文件变化不代表已修复广告；专项脚本仅报告，不自动覆盖；未做 iPhone 效果验收。'}


def atomic_write(path, data):
    path = Path(path)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
    descriptor, temporary = tempfile.mkstemp(prefix='.maintenance-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path, value):
    atomic_write(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


def maintenance_dir(root):
    path = safe_path(Path(root), '.local/maintenance')
    path.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def maintenance_lock(root):
    directory = maintenance_dir(root)
    path = directory / 'run.lock'
    try:
        with path.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps({'pid': os.getpid(), 'started_at_utc': now()}))
    except FileExistsError:
        raise MaintenanceError('maintenance_already_running') from None
    try:
        yield
    finally:
        path.unlink(missing_ok=True)


def write_report(root, report):
    directory = maintenance_dir(root)
    write_json(directory / 'latest.json', report)
    text = ['# 上游维护检查报告', '', f'检查时间（UTC）：{report["checked_at_utc"]}', '',
            '只检查清单里已记录的公开文件；不自动发现新 App 或新接口。',
            '普通规则可隔离更新；脚本、重写、MITM、许可和人工精选 AI 域名需审查。',
            '文件变化不代表有效修复，检查/模拟验证不等于 iPhone 去广告验收。', '',
            '| 状态 | 文件数量 |', '|---|---:|']
    for status, label in STATUS.items():
        text.append(f'| {label} | {report["summary"][status]} |')
    if report.get('update'):
        text += ['', '更新结果：`' + report['update']['status'] + '`。']
        if report['update'].get('backup_id'):
            text.append('本地备份：`' + report['update']['backup_id'] + '`。')
        text.append('只保存本地文件；未提交、未推送，不会自行改变手机的订阅内容。')
        if report['update'].get('deltas'):
            text += ['', '| 规则输出 | 原条数 | 新条数 | 新增 | 删除 |', '|---|---:|---:|---:|---:|']
            for delta in report['update']['deltas']:
                text.append(f'| {delta["output"]} | {delta["old_count"]} | {delta["new_count"]} | {delta["added"]} | {delta["removed"]} |')
        if report['update'].get('changed_files'):
            text += ['', '本次实际改变的文件：', '']
            text += ['- `' + path + '`' for path in report['update']['changed_files']]
        if report['update'].get('rolled_back_at_utc'):
            text += ['', '已在本地回退；上面的文件差异是该次更新的历史记录。']
    if report.get('failure'):
        text += ['', '处理已停止：`' + report['failure'] + '`。现有配置未通过本工具发布。']
    text += ['', '| 来源文件 | 结果 | 已用版本 → 上游版本 |', '|---|---|---|']
    for item in report['files']:
        text.append(f'| {item["repository"]}/{item["path"]} | {STATUS[item["status"]]} | '
                    f'{item["pinned_revision"][:8]} → {item.get("latest_revision", "未知")[:8]} |')
    text += ['', '推荐每天检查一次，有变化才处理。报告保存在本机 .local/maintenance/，不提交到仓库。',
             '上游当前无法连接时会明确失败，不把连接失败视为“没有更新”。', '']
    atomic_write(directory / 'latest.md', '\n'.join(text).encode('utf-8'))


def rule_delta(old, new):
    before, after = set(old), set(new)
    added, removed = len(after - before), len(before - after)
    reasons = []
    if not after:
        reasons.append('empty_rules')
    if any(rule.startswith('DOMAIN-SUFFIX,') and '.' not in rule.split(',')[1].rstrip('.') for rule in after - before):
        reasons.append('new_top_level_suffix')
    if removed > len(before) * .10:
        reasons.append('large_removal')
    if added + removed > max(1, len(before)) * .25:
        reasons.append('large_change_ratio')
    if added + removed > 5000:
        reasons.append('large_change_count')
    return {'old_count': len(before), 'new_count': len(after), 'added': added,
            'removed': removed, 'blocked': bool(reasons), 'reasons': reasons}


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise MaintenanceError('duplicate_yaml_key')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def rule_payload(raw):
    try:
        value = yaml.load(raw, Loader=UniqueLoader)
        if not isinstance(value, dict) or set(value) != {'payload'}:
            raise MaintenanceError('invalid_rule_document')
        payload = value['payload']
        if not isinstance(payload, list) or not payload or not all(isinstance(x, str) and x.strip() for x in payload):
            raise MaintenanceError('empty_or_invalid_rules')
        return payload
    except MaintenanceError:
        raise
    except Exception:
        raise MaintenanceError('invalid_rule_yaml') from None


def validate_rule(rule):
    fields = rule.split(',')
    if len(fields) not in (2, 3) or fields[0] not in RULE_KINDS:
        raise MaintenanceError('invalid_native_rule')
    kind, value = fields[:2]
    if len(fields) == 3 and (kind not in ('IP-CIDR', 'IP-CIDR6') or fields[2] != 'no-resolve'):
        raise MaintenanceError('unexpected_rule_action')
    if not value or value != value.strip() or any(c.isspace() or ord(c) < 32 for c in value):
        raise MaintenanceError('invalid_rule_value')
    if kind in ('IP-CIDR', 'IP-CIDR6'):
        try:
            network = ipaddress.ip_network(value, strict=False)
            if network.prefixlen == 0 or network.version != (6 if kind == 'IP-CIDR6' else 4):
                raise ValueError()
        except ValueError:
            raise MaintenanceError('invalid_rule_network') from None
    elif kind == 'DOMAIN-KEYWORD':
        if any(x in value for x in ('/', ':', '?', '#', '*', '"', "'")):
            raise MaintenanceError('invalid_rule_keyword')
    else:
        # Reviewed Stash classical lists contain explicit domains, not URL syntax or regexes.
        value = value.rstrip('.')
        try:
            labels = value.encode('idna').decode('ascii').split('.')
        except UnicodeError:
            raise MaintenanceError('invalid_rule_domain') from None
        if len(value) > 253 or not all(re.fullmatch(r'[A-Za-z0-9_](?:[A-Za-z0-9_-]{0,61}[A-Za-z0-9_])?', x) for x in labels):
            raise MaintenanceError('invalid_rule_domain')


def tracked_paths(root):
    return [path for path in git(root, 'ls-files', '-z').decode('utf-8').split('\0') if path]


def ensure_clean(root, base_head=None):
    if git(root, 'status', '--porcelain', '--untracked-files=normal').strip():
        raise MaintenanceError('working_tree_not_clean')
    current = git(root, 'rev-parse', 'HEAD').decode('ascii').strip()
    if base_head is not None and current != base_head:
        raise MaintenanceError('head_changed')
    return current


def apply_verified_changes(root, candidate, allowed, base_head):
    """Commit no Git state. Only an unchanged clean working tree can receive verified bytes."""
    root, candidate = Path(root), Path(candidate)
    ensure_clean(root, base_head)
    changes = {}
    for relative in tracked_paths(root):
        original, staged = safe_path(root, relative), safe_path(candidate, relative)
        if not original.is_file() or not staged.is_file():
            raise MaintenanceError('candidate_file_missing')
        before, after = original.read_bytes(), staged.read_bytes()
        if before != after:
            if relative not in allowed:
                raise MaintenanceError('unexpected_generated_change')
            changes[relative] = (before, after)
    if not changes:
        return None
    directory = maintenance_dir(root)
    backup_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + os.urandom(4).hex()
    backup = safe_path(directory, 'backups/' + backup_id)
    backup.mkdir(parents=True)
    manifest = {'schema': 1, 'id': backup_id, 'base_head': base_head,
                'created_at_utc': now(), 'status': 'prepared', 'files': []}
    for relative, (before, after) in changes.items():
        path = safe_path(backup / 'before', relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(before)
        manifest['files'].append({'path': relative, 'before_sha256': sha256(before), 'after_sha256': sha256(after)})
    write_json(backup / 'manifest.json', manifest)
    ensure_clean(root, base_head)
    applied = []
    try:
        for relative, (before, after) in changes.items():
            original = safe_path(root, relative)
            if original.read_bytes() != before:
                raise MaintenanceError('file_changed_during_apply')
            atomic_write(original, after)
            applied.append(relative)
        manifest['status'] = 'applied'
        write_json(backup / 'manifest.json', manifest)
        write_json(directory / 'latest-backup.json', {'id': backup_id})
    except BaseException:
        recovery_failed = False
        for relative in reversed(applied):
            try:
                destination = safe_path(root, relative)
                if destination.read_bytes() != changes[relative][1]:
                    recovery_failed = True
                    continue
                atomic_write(destination, changes[relative][0])
            except Exception:
                recovery_failed = True
        manifest['status'] = 'recovery_required' if recovery_failed else 'rolled_back'
        write_json(backup / 'manifest.json', manifest)
        raise MaintenanceError('apply_failed_recovery_required' if recovery_failed else 'apply_failed_restored') from None
    return backup_id


def rollback(root, backup_id=None):
    root = Path(root)
    directory = maintenance_dir(root)
    if backup_id is None:
        pointer = directory / 'latest-backup.json'
        if not pointer.is_file():
            raise MaintenanceError('backup_not_found')
        backup_id = read_json(pointer)['id']
    if not re.fullmatch(r'\d{8}T\d{6}Z-[0-9a-f]{8}', backup_id):
        raise MaintenanceError('invalid_backup_id')
    backup = safe_path(directory, 'backups/' + backup_id)
    try:
        manifest = read_json(backup / 'manifest.json')
    except (OSError, ValueError):
        raise MaintenanceError('backup_not_found') from None
    if manifest.get('status') not in ('applied', 'prepared', 'recovery_required'):
        raise MaintenanceError('backup_not_active')
    if git(root, 'diff', '--cached', '--name-only').strip():
        raise MaintenanceError('staged_changes_present')
    changes = []
    tracked = set(tracked_paths(root))
    for entry in manifest['files']:
        relative = entry['path']
        if relative not in tracked:
            raise MaintenanceError('backup_path_not_tracked')
        original, source = safe_path(root, relative), safe_path(backup / 'before', relative)
        if not original.is_file() or not source.is_file():
            raise MaintenanceError('backup_file_missing')
        before, current = source.read_bytes(), original.read_bytes()
        if sha256(before) != entry['before_sha256']:
            raise MaintenanceError('backup_corrupted')
        digest = sha256(current)
        if digest == entry['after_sha256']:
            changes.append((original, before, current))
        elif manifest['status'] == 'applied' or digest != entry['before_sha256']:
            raise MaintenanceError('file_changed_after_update')
    applied = []
    try:
        for path, before, current in changes:
            if path.read_bytes() != current:
                raise MaintenanceError('file_changed_during_rollback')
            atomic_write(path, before)
            applied.append((path, current, before))
    except BaseException:
        recovery_failed = False
        for path, current, before in reversed(applied):
            try:
                if path.read_bytes() != before:
                    recovery_failed = True
                    continue
                atomic_write(path, current)
            except Exception:
                recovery_failed = True
        if recovery_failed:
            manifest['status'] = 'recovery_required'
            write_json(backup / 'manifest.json', manifest)
        raise MaintenanceError('rollback_failed_recovery_required' if recovery_failed else 'rollback_failed_restored') from None
    manifest['status'] = 'rolled_back'
    manifest['rolled_back_at_utc'] = now()
    write_json(backup / 'manifest.json', manifest)
    latest = directory / 'latest.json'
    if latest.is_file():
        report = read_json(latest)
        if report.get('update', {}).get('backup_id') == backup_id:
            report['update']['status'] = 'rolled_back_locally'
            report['update']['rolled_back_at_utc'] = manifest['rolled_back_at_utc']
            write_report(root, report)
    return backup_id


def run_step(root, command, label, timeout=240):
    print('  验证步骤：' + label, flush=True)
    try:
        result = subprocess.run(command, cwd=root, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=timeout,
                                env=dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8'))
    except (OSError, subprocess.SubprocessError):
        raise MaintenanceError('step_unavailable:' + label) from None
    if result.returncode:
        # Deliberately do not copy process output (which could include environment details) to logs.
        raise MaintenanceError('step_failed:' + label)


def update(root, report=None):
    root = Path(root)
    base_head = ensure_clean(root)
    if not shutil.which('node'):
        raise MaintenanceError('node_not_installed')
    report = report if report is not None else check_upstreams(root)
    write_report(root, report)
    if not report['ok']:
        raise MaintenanceError('all_sources_not_checked')
    lock = read_json(root / 'research/sources.lock.json')
    target = report['repositories'].get(PRIMARY, {})
    if target.get('status') != 'ok':
        raise MaintenanceError('primary_upstream_unavailable')
    revision = target['head']
    relevant = [item for item in report['files'] if item['repository'] == PRIMARY and
                ('rules' in item['categories'] or 'license' in item['categories'])]
    if any(item['status'] == 'error' for item in relevant):
        raise MaintenanceError('required_source_unavailable')
    if any(item['status'] != 'unchanged' for item in relevant if 'license' in item['categories']):
        raise MaintenanceError('license_changed')
    if not any(item['status'] == 'rules-update' for item in relevant):
        report['update'] = {'status': 'no_rule_changes'}
        write_report(root, report)
        return None
    print('普通规则有变化，创建隔离副本；专项脚本保持原样。', flush=True)
    allowed = set(GENERATED) | {item['output'] for item in lock['resources']}
    with tempfile.TemporaryDirectory(prefix='jimmy-maintenance-') as temporary:
        candidate = Path(temporary) / 'candidate'
        # A local clone includes tracked public history, but not ignored private/ or .local/ files.
        run_step(root, ['git', '-c', 'core.autocrlf=false', 'clone', '--local', '--no-hardlinks', '--no-checkout', '--quiet',
                        str(root), str(candidate)], 'clone', timeout=120)
        git(candidate, 'config', 'core.autocrlf', 'false')
        hook_dir = candidate / '.git' / 'maintenance-no-hooks'
        hook_dir.mkdir()
        git(candidate, 'config', 'core.hooksPath', str(hook_dir))
        git(candidate, 'checkout', '--quiet', '--detach', base_head)
        run_step(candidate, [sys.executable, 'tools/refresh_rules.py', '--revision', revision, '--write'], 'refresh_rules')
        new_lock = read_json(candidate / 'research/sources.lock.json')
        expected = {(item['path'], item['pinned_revision']): item for item in relevant if 'rules' in item['categories']}
        deltas = []
        for old, new in zip(lock['resources'], new_lock['resources'], strict=True):
            baseline = expected.get((old['source_path'], parse_source_url(old['url'])[1]))
            if baseline is None or new['source_sha256'] != baseline['latest_sha256']:
                raise MaintenanceError('source_changed_after_check')
            before = rule_payload(safe_path(root, old['output']).read_bytes())
            after = rule_payload(safe_path(candidate, new['output']).read_bytes())
            for rule in after:
                validate_rule(rule)
            delta = dict(rule_delta(before, after), output=old['output'])
            deltas.append(delta)
            if delta['blocked']:
                report['update'] = {'status': 'blocked_rule_delta', 'deltas': deltas}
                write_report(root, report)
                raise MaintenanceError('large_rule_delta')
        run_step(candidate, [sys.executable, 'tools/build_ads.py', '--write'], 'build')
        run_step(candidate, [sys.executable, 'tools/build_ads.py'], 'generated_consistency')
        run_step(candidate, [sys.executable, 'tools/validate.py'], 'project_and_scripts', timeout=360)
        run_step(candidate, [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_private_config.py'], 'private_builder', timeout=600)
        if (candidate / 'tests/test_maintenance.py').is_file():
            run_step(candidate, [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_maintenance.py'], 'maintenance_tests')
        backup_id = apply_verified_changes(root, candidate, allowed, base_head)
    report['operation'] = 'update'
    report['update'] = {'status': 'updated_locally' if backup_id else 'no_output_changes',
                        'backup_id': backup_id, 'base_head': base_head,
                        'upstream_revision': revision, 'deltas': deltas,
                        'changed_files': [entry['path'] for entry in read_json(maintenance_dir(root) / 'backups' / backup_id / 'manifest.json')['files']] if backup_id else [],
                        'committed': False, 'pushed': False, 'device_tested': False}
    write_report(root, report)
    return backup_id


ERROR_TEXT = {
    'working_tree_not_clean': '仓库有未提交的修改；先审阅、提交或另存，工具不会覆盖。',
    'maintenance_already_running': '已有维护进程或残留锁；确认进程退出后再删除 .local/maintenance/run.lock。',
    'node_not_installed': '需要先安装 Node.js，再运行普通规则更新。',
    'all_sources_not_checked': '部分上游未检查成功，原文件保持不变；稍后重试并查看报告。',
    'license_changed': '上游许可证发生变化，需审查后才能采用。',
    'large_rule_delta': '规则变化超过保护阈值，已保留原文件；请看报告并人工审查。',
    'file_changed_after_update': '更新后你又修改了目标文件，回退已停止，避免覆盖你的修改。',
    'backup_not_found': '未找到可回退备份。',
    'backup_not_active': '该备份已经回退或未完成应用。',
}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', nargs='?', default='check', choices=['check', 'update', 'rollback'])
    parser.add_argument('--backup', help='rollback 使用的本地备份编号；省略则取最近成功更新')
    args = parser.parse_args(argv)
    if args.backup and args.command != 'rollback':
        parser.error('--backup 只用于 rollback')
    report = None
    try:
        with maintenance_lock(ROOT):
            if args.command == 'rollback':
                identifier = rollback(ROOT, args.backup)
                print('已在本地回退：' + identifier + '；没有提交或推送。')
                return 0
            print('正在检查清单内的公开上游；不读取私人机场或证书。', flush=True)
            if args.command == 'update':
                ensure_clean(ROOT)
            report = check_upstreams(ROOT)
            write_report(ROOT, report)
            for status, label in STATUS.items():
                print(f'{label}：{report["summary"][status]}')
            if args.command == 'update':
                backup = update(ROOT, report)
                print('普通规则已保存本地；备份：' + backup if backup else '普通规则无需变更。')
                print('专项变化见报告。未提交、未推送；手机订阅不会因本地运行而自行改变。')
            if not report['ok']:
                print('部分上游检查失败；已列出可确认的结果，不能视为全部资源检查成功。')
            print('中文报告：.local/maintenance/latest.md')
            print('检测到变化不等于已有效修复；没有进行 iPhone 效果验收。')
            return 0 if report['ok'] else 1
    except MaintenanceError as error:
        if report is not None:
            report['failure'] = error.code
            write_report(ROOT, report)
        print('已停止：' + ERROR_TEXT.get(error.code, '操作未通过，请根据固定错误码检查依赖、网络或验证步骤。'))
        print('错误码：' + error.code)
        return 1
    except KeyboardInterrupt:
        print('操作已取消；没有自动提交或推送。')
        return 1
    except Exception as error:
        # Never include exception messages/URLs/proxy details, even for malformed local data.
        print('已停止，错误类型：' + type(error).__name__)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
