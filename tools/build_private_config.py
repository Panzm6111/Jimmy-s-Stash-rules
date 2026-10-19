#!/usr/bin/env python3
"""Combine an outside-repository node export with the maintained public config.

No network requests, subscription URL, credential logging, or public output.
This checks a local model, not the Stash parser or live node connectivity.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import uuid

import yaml

from build_local_bundle import dump
from validate import BUILTINS, RAW, ROOT, UniqueLoader, load, route

REGIONS = ('美国', '日本', '香港', '新加坡', '台湾')
AUTO_POOLS = ('自动节点', *REGIONS, '其他地区')
PROBE_SETTINGS = {'url': 'https://www.gstatic.com/generate_204', 'interval': 1800}
PROBE_FIELDS = (*PROBE_SETTINGS, 'tolerance', 'lazy')


class BuildError(ValueError):
    """Messages must never contain values or parser excerpts from private input."""


def require(condition, message):
    if not condition:
        raise BuildError(message)


def check_nodes(nodes, group_names, allow_name_conflicts=False):
    require(isinstance(nodes, list) and bool(nodes), '需要非空的 proxies 节点列表。')
    names = set()
    for index, node in enumerate(nodes, 1):
        label = f'第 {index} 个节点'
        require(isinstance(node, dict), label + '格式不是映射。')
        name = node.get('name')
        require(isinstance(name, str) and bool(name.strip()), label + '缺少名称。')
        require(name not in names, '存在重复节点名；未打印名称或凭据。')
        require(allow_name_conflicts or name not in group_names | BUILTINS, '节点名与策略名称冲突。')
        names.add(name)
        require(isinstance(node.get('server'), str) and bool(node['server']), label + '缺少服务器。')
        port = node.get('port')
        require(type(port) is int and 1 <= port <= 65535, label + '端口无效。')
        require(not node.get('skip-cert-verify'), label + '关闭了 TLS 验证，需先修正来源。')
        if node.get('type') == 'ss':
            require(isinstance(node.get('cipher'), str) and bool(node['cipher']), label + '缺少 SS 加密方式。')
            require(isinstance(node.get('password'), str) and bool(node['password']), label + '缺少 SS 密码。')
        elif node.get('type') == 'vless':
            try:
                uuid.UUID(node.get('uuid', ''))
            except (ValueError, AttributeError, TypeError):
                raise BuildError(label + '的 VLESS UUID 无效。') from None
        else:
            raise BuildError(label + '使用尚未审查的协议；未静默删除节点。')
    # References to source groups cannot survive replacing those groups. Local
    # node chains are also deliberately rejected rather than silently changed.
    for node in nodes:
        require(not any(node.get(k) for k in ('dialer-proxy', 'underlying-proxy')),
                '节点带有链式代理依赖，需单独审查；未删除该依赖。')


def verify(config, template, expected_nodes):
    require(config.get('proxies') == expected_nodes, '节点参数发生改变。')
    require(not config.get('proxy-providers') and not config.get('rule-providers'), '仍有未展开的代理或规则集。')
    groups = config['proxy-groups']
    names = [g['name'] for g in groups]
    node_names = {n['name'] for n in expected_nodes}
    require(len(names) == len(set(names)) == 18, '策略组数量或唯一性异常。')
    require(not (set(names) & node_names), '节点与策略重名。')
    targets = set(names) | node_names | BUILTINS
    graph = {}
    for group in groups:
        require('use' not in group and 'filter' not in group, '仍依赖运行时代理集或筛选。')
        require(group['type'] in {'select', 'url-test'}, '未知策略组类型。')
        require(bool(group.get('proxies')), '存在空策略组。')
        require(set(group['proxies']) <= targets, '存在缺失的策略或节点引用。')
        require(len(group['proxies']) == len(set(group['proxies'])), '策略候选重复。')
        graph[group['name']] = [n for n in group['proxies'] if n in names]
    def visit(name, ancestors):
        require(name not in ancestors, '策略组循环引用。')
        for child in graph[name]:
            visit(child, ancestors | {name})
    for name in names:
        visit(name, set())
    by_name = {g['name']: g for g in groups}
    template_groups = {g['name']: g for g in template['proxy-groups']}
    require(not ({'全部节点', 'OpenAI'} & set(names)), '仍有旧策略组名称。')
    for name in AUTO_POOLS:
        group = by_name[name]
        members = group['proxies']
        require(set(members) <= node_names | {'REJECT'}, '自动池引用其他策略或直连。')
        require(members[-1] == 'REJECT', '自动池缺少末尾阻断。')
        if members == ['REJECT']:
            require(group['type'] == 'select', '空池没有改为阻断选择组。')
            require(not any(key in group for key in PROBE_FIELDS), '空池残留测速参数。')
        else:
            require(group['type'] == 'url-test', '非空池未使用自动测速。')
            require(all(group.get(key) == value for key, value in PROBE_SETTINGS.items()),
                    '自动池测速地址或频率改变。')
            require(not any(key in group for key in ('tolerance', 'lazy')), '自动池包含未核实的测速设置。')
    union = set()
    for name in REGIONS:
        members = by_name[name]['proxies']
        require(set(members) <= node_names | {'REJECT'}, '地区引用其他地区或直连。')
        require(members[-1] == 'REJECT', '地区缺少末尾阻断。')
        expected_members = {n for n in node_names if re.search(template_groups[name]['filter'], n)}
        require(set(members) - {'REJECT'} == expected_members, '地区包含错误节点或遗漏节点。')
        union.update(n for n in members if n in node_names)
    require(set(by_name['自动节点']['proxies']) - {'REJECT'} == node_names, '自动节点有遗漏。')
    require(by_name['手动节点']['type'] == 'select' and
            set(by_name['手动节点']['proxies']) - {'REJECT'} == node_names, '手动节点有遗漏或类型改变。')
    require(set(by_name['其他地区']['proxies']) - {'REJECT'} == node_names - union,
            '其他地区不是五地区的补集。')
    require(by_name['总代理']['proxies'][0] == 'REJECT', '首次出口选择不再中立。')
    require(by_name['海外AI']['proxies'][0] == '美国', '海外 AI 未默认选择美国。')
    for name in ('Netflix', 'YouTube', 'Telegram', '未匹配流量'):
        require(by_name[name]['proxies'][0] == '总代理', '软件未默认跟随总代理。')
    for name in ('Apple', 'Microsoft'):
        require(by_name[name]['proxies'][0] == 'DIRECT', '系统软件默认直连改变。')
    # Business logic is reused exactly. This is stronger than sampling just a
    # few routing decisions and also preserves script timeouts/failure behavior.
    for key in ('rules', 'dns', 'http', 'script-providers'):
        require(config.get(key) == template.get(key), '公共规则、DNS 或广告逻辑改变。')
    for rule in config['rules']:
        parts = rule.split(',')
        require((parts[1] if parts[0] == 'MATCH' else parts[2]) in targets, '规则目标缺失。')
    require(config['rules'][-1] == 'MATCH,未匹配流量', '缺少末尾规则。')
    scripts = config.get('script-providers', {})
    for item in config.get('http', {}).get('script', []):
        require(item['name'] in scripts, 'HTTP 引用缺失的脚本。')
        require(item['type'] in {'request', 'response'} and item['timeout'] <= 10, '脚本处理或超时异常。')
        require(item['require-body'] is (item['type'] == 'response'), '脚本正文读取方式异常。')
    for provider in scripts.values():
        require(set(provider) == {'url', 'interval'}, '脚本声明格式异常。')
        require(provider['url'].startswith(RAW), '存在外部脚本。')
        require((ROOT / provider['url'][len(RAW):]).is_file(), '脚本文件缺失。')
    for case in json.loads((ROOT / 'tests/fixtures/routes.json').read_text()):
        args = (case.get('domain', ''), case.get('ip', ''), case.get('country', ''))
        require(route(config, *args) == route(template, *args), '代表性域名路由改变。')


def compose(source, template=None):
    template = copy.deepcopy(template if template is not None else load('config/stash.yaml'))
    require(isinstance(source, dict), '来源不是 YAML 配置映射。')
    require(not source.get('proxy-providers'), '来源含远程代理集；请提供已包含实际节点的导出。')
    group_names = {g['name'] for g in template['proxy-groups']}
    nodes = source.get('proxies')
    check_nodes(nodes, group_names, allow_name_conflicts=True)
    definitions = {g['name']: g for g in template['proxy-groups']}
    include = re.compile(definitions['自动节点']['filter'])
    eligible = [copy.deepcopy(n) for n in nodes if include.search(n['name'])]
    require(bool(eligible), '过滤提示条目后没有真实节点。')
    original_eligible = copy.deepcopy(eligible)
    # Bare country names can be both real node names and our group names.
    # Rename only that display field; never alter any connection parameter.
    used = group_names | BUILTINS | {n['name'] for n in eligible}
    renamed = 0
    for node in eligible:
        if node['name'] in group_names | BUILTINS:
            stem = '节点 · ' + node['name']
            alias = stem
            index = 2
            while alias in used:
                alias = stem + f' [{index}]'
                index += 1
            node['name'] = alias
            used.add(alias)
            renamed += 1
    check_nodes(eligible, group_names)
    for before, after in zip(original_eligible, eligible):
        require({k: v for k, v in before.items() if k != 'name'} ==
                {k: v for k, v in after.items() if k != 'name'}, '连接参数在处理重名时改变。')
    all_names = [n['name'] for n in eligible]
    region_nodes = {name: [n for n in all_names if re.search(definitions[name]['filter'], n)]
                    for name in REGIONS}
    assigned = set().union(*(set(v) for v in region_nodes.values()))
    other_nodes = [n for n in all_names if n not in assigned]
    pool_nodes = {'自动节点': all_names, **region_nodes, '其他地区': other_nodes}
    result = copy.deepcopy(template)
    result.pop('proxy-providers', None)
    result['proxies'] = eligible
    for group in result['proxy-groups']:
        name = group['name']
        expanded = group.pop('use', [])
        group.pop('filter', None)
        if name in AUTO_POOLS:
            group['proxies'] = pool_nodes[name] + ['REJECT']
            if not pool_nodes[name]:
                group['type'] = 'select'
                for key in PROBE_FIELDS:
                    group.pop(key, None)
        elif name == '手动节点':
            group['proxies'] = all_names + ['REJECT']
        elif expanded:
            group['proxies'] = list(dict.fromkeys(group['proxies'] + all_names))
    # Keep private node definitions at the beginning, with a clear warning.
    result = {'proxies': result.pop('proxies'), **result}
    verify(result, template, eligible)
    report = {
        'source_entries': len(nodes), 'connection_candidates': len(eligible),
        'metadata_entries_excluded': len(nodes) - len(eligible),
        'display_names_aliased_for_conflict': renamed,
        'protocol_counts': dict(Counter(n['type'] for n in eligible)),
        'region_counts': {name: len(v) for name, v in region_nodes.items()},
        'other_region_count': len(other_nodes), 'groups': len(result['proxy-groups']),
        'rules': len(result['rules']), 'remote_scripts': len(result.get('script-providers', {})),
        'native_stash_tested': False, 'connectivity_tested': False,
        'subscription_auto_update': False,
    }
    return result, report


def render(config):
    return ('# JIMMY-STASH 本机私人节点快照；含连接凭据，不公开、不提交、不转发。\n'
            '# 本文件可直接作为主配置导入，不需要私人覆写或替换订阅URL。\n'
            '# 首次导入：总代理选择自动节点或有节点的地区；使用规则模式。\n'
            '# 自动节点和地区池按 URL 测试延迟选最快节点；其他地区为五地区以外的全部候选。\n'
            '# 海外AI 默认美国，Apple 默认直连；测速不代表解锁，不跨地区兜底。\n'
            '# 不含机场旧DNS/分流/控制端口；连接字段原样保留，重名节点仅加显示前缀。\n'
            '# 本地节点和内嵌规则不会自动跟随机场/公共配置更新，需要重新合成。\n'
            '# 12份广告脚本由Stash从本项目下载；开屏专项仍需设备自建证书。\n'
            '# 原生解析、Reality/Vision支持、连接、解锁和广告效果仍须手机测试。\n'
            '# 来源与许可证：https://github.com/Panzm6111/Jimmy-s-Stash-rules/blob/main/docs/SOURCES.md\n'
            + dump(config))


def write_private(destination, text):
    path = destination.expanduser().resolve()
    require(not path.is_relative_to(ROOT), '含凭据输出必须放在仓库外。')
    # Some managed roots contain empty .git sandbox markers, not repositories.
    require(not any((p / '.git').is_file() or (p / '.git/HEAD').is_file() for p in path.parents),
            '含凭据输出不能放在其他 Git 仓库内。')
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.jimmy-private-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        source_path = args.input.expanduser().resolve()
        require(not source_path.is_relative_to(ROOT), '私人输入必须放在仓库外。')
        require(source_path != args.output.expanduser().resolve(), '输出不能覆盖原始输入。')
        try:
            source = yaml.load(source_path.read_text(), Loader=UniqueLoader)
        except (yaml.YAMLError, ValueError, UnicodeError):
            raise BuildError('私人 YAML 解析失败；为避免泄露，不输出解析器原文。') from None
        config, report = compose(source)
        text = render(config)
        require(yaml.load(text, Loader=UniqueLoader) == config, '最终 YAML 往返校验失败。')
        write_private(args.output, text)
        # Only aggregate counts and booleans; no node names, addresses or paths.
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (BuildError, OSError) as error:
        print('FAIL: ' + (str(error) if isinstance(error, BuildError) else '私人文件读写失败。'), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
