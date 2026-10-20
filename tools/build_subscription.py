#!/usr/bin/env python3
"""Render the stable public Stash URL from the maintained project; no private input."""
import argparse
import json
from pathlib import Path
import yaml
from build_local_bundle import flatten, dump
from validate import ROOT, RAW, load, merged, merge_model, route, validate_structure
from scan_secrets import inspect

OUTPUT = 'config/stash.yaml'
URL = RAW + OUTPUT

def render():
    config = flatten(merged(), keep_providers={'基础广告'})
    # Keep the private device-only edit at the top. Public script providers use
    # the same URL declaration as the reviewed native Stash modules, while the
    # optional offline bundle separately retains content-based providers.
    config = {'proxy-providers': config.pop('proxy-providers'), **config}
    return ('# Jimmy Stash 公共订阅入口；由 tools/build_subscription.py 生成。\n'
            '# 固定地址：' + URL + '\n'
            '# JIMMY-STASH AD-20261020.1；18个原策略组、DNS、私人订阅接入保留。\n'
            '# 通用广告：基础广告 RULE-SET 有实际引用；可选 expanded 覆写现在有效。\n'
            '# App专项独立启停：本主配置不内置HTTP处理；按 docs/AD-MODULES.md 导入所需原模块。\n'
            '# 已装旧版须刷新主配置及所选App覆写，不要叠加旧整合广告增强。\n'
            '# 私人机场URL只在设备本地覆写，不放到GitHub。总代理首次REJECT，需选择出口。\n'
            '# 当前仅离线验证；真实Stash解析、MITM、脚本执行与广告效果待iPhone验收。\n'
            + dump(config))

def verify(text):
    config = yaml.safe_load(text)
    validate_structure(config)
    assert set(config['rule-providers']) == {'基础广告'}
    assert config['rules'].count('RULE-SET,基础广告,广告拦截') == 1
    assert 'http' not in config and not config.get('script-providers')
    assert len(config['proxy-groups']) == 18
    assert config['proxy-providers']['机场']['url'] == 'https://example.invalid/REPLACE_ON_DEVICE'
    original = merged()
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
        path.write_text(text)
        print('WROTE ' + OUTPUT)
    else:
        print(('PASS ' if same else 'DRIFT ') + OUTPUT)
    print(URL)
    return 0 if args.write or same else 1

if __name__ == '__main__': raise SystemExit(main())
