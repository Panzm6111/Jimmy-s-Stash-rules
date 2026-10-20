#!/usr/bin/env python3
"""Render the stable public Stash URL from the maintained project; no private input."""
import argparse
import json
from pathlib import Path
import yaml
from build_local_bundle import flatten, dump, inline_scripts
from validate import ROOT, RAW, load, merged, merge_model, route, validate_structure
from scan_secrets import inspect

OUTPUT = 'config/stash.yaml'
URL = RAW + OUTPUT
VERSION = 'AD-20261020.2'

def integrated():
    """The user-facing integrated entry; module files remain maintained sources."""
    modules = sorted(p.relative_to(ROOT) for p in (ROOT / 'modules/ads').glob('*.stoverride')
                     if p.stem != 'expanded')
    config = merged(*modules, 'modules/ads/expanded.stoverride')
    # Keep LAN/system exceptions ahead of all ad routes. The module merge model
    # prepends routes; place those reviewed ad-only domains at the core ad slot.
    special = list(dict.fromkeys(r for p in modules for r in load(p).get('rules', [])))
    core_rules = merged()['rules']
    slot = core_rules.index('RULE-SET,基础广告,广告拦截')
    # The expanded snapshot lists these hosts as whole-domain ads. Keep shared
    # Meituan material working, and let reviewed native fixed replies own their
    # paths instead of introducing a competing route-level rejection.
    exceptions = load('modules/ads/expanded.stoverride').get('rules', [])
    config['rules'] = core_rules[:slot] + exceptions + special + core_rules[slot:]
    return config

def render():
    config = inline_scripts(flatten(integrated(), keep_providers={'基础广告'}))
    # Embed the reviewed scripts so refreshing this file updates declarations
    # and code together, without a second script cache to refresh on the phone.
    config = {'proxy-providers': config.pop('proxy-providers'), **config}
    return ('# Jimmy Stash 公共订阅入口；由 tools/build_subscription.py 生成。\n'
            '# 固定地址：' + URL + '\n'
            '# JIMMY-STASH ' + VERSION + '；18个原策略组、DNS、私人订阅接入保留。\n'
            '# 已整合40款现有专项与11份响应JS，扩展域名规则默认启用；诊断默认关闭。\n'
            '# 建议每周手动刷新本配置，修复发布后立即刷新；规则集与机场每24小时尝试刷新。\n'
            '# 不需另加App或expanded覆写；停用已额外添加的广告覆写，保留私人订阅/白名单。\n'
            '# 当前需求统一为整合入口，不再要求逐App开关；原模块保留作维护来源与旧安装兼容。\n'
            '# 各独立模块/JS保持原许可；来源与完整源码：https://github.com/Panzm6111/Jimmy-s-Stash-rules/blob/main/docs/SOURCES.md\n'
            '# 私人机场URL只在设备本地覆写，不放到GitHub。总代理首次REJECT，需选择出口。\n'
            '# 当前仅离线验证；真实Stash解析、MITM、脚本执行与广告效果待iPhone验收。\n'
            + dump(config))

def verify(text):
    config = yaml.safe_load(text)
    validate_structure(config)
    assert set(config['rule-providers']) == {'基础广告'}
    assert config['rules'].count('RULE-SET,基础广告,广告拦截') == 1
    assert config['rule-providers']['基础广告']['url'] == RAW + 'rules/vendor/ads-expanded.yaml'
    assert len(config['http']['url-rewrite']) == 38
    assert len(config['http']['script']) == 11
    assert len(config['http']['mitm']) == 45
    assert len(config['script-providers']) == 11
    for name, provider in integrated()['script-providers'].items():
        assert config['script-providers'][name] == {'content': (ROOT / provider['url'][len(RAW):]).read_text()}
    assert len(config['proxy-groups']) == 18
    assert config['proxy-providers']['机场']['url'] == 'https://example.invalid/REPLACE_ON_DEVICE'
    original = integrated()
    for key in ('proxy-groups', 'proxy-providers', 'dns'):
        assert config[key] == merged()[key], 'non-ad configuration changed'
    expanded = merge_model(config, load('modules/ads/expanded.stoverride'))
    assert route(expanded, 'ad.12306.cn') == '广告拦截'
    for case in json.loads((ROOT / 'tests/fixtures/routes.json').read_text()):
        args = (case.get('domain', ''), case.get('ip', ''), case.get('country', ''))
        assert route(config, *args) == route(original, *args)
    # A public refresh never carries a real URL; applying the same device-private
    # map after each download preserves that value in the expected merge model.
    device = {'proxy-providers': {'机场': {'url': 'https://subscription.example.invalid/DEVICE_ONLY'}}}
    initial = merge_model(config, device)
    refreshed = merge_model(yaml.safe_load(text), device)
    assert initial['proxy-providers'] == refreshed['proxy-providers']
    assert [g['name'] for g in initial['proxy-groups']] == [g['name'] for g in refreshed['proxy-groups']]
    assert not inspect(text, OUTPUT), 'sensitive pattern in subscription entry'
    return config

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    text = render()
    verify(text)
    path = ROOT / OUTPUT
    same = path.is_file() and path.read_text() == text
    if args.write:
        path.write_text(text, encoding='utf-8', newline='\n')
        print('WROTE ' + OUTPUT)
    else:
        print(('PASS ' if same else 'DRIFT ') + OUTPUT)
    print(URL)
    return 0 if args.write or same else 1

if __name__ == '__main__': raise SystemExit(main())
