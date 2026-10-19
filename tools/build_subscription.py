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
    addons = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'modules/ads').glob('*.stoverride') if p.stem != 'expanded')
    config = flatten(merged(*addons))
    config['http']['mitm'] = list(dict.fromkeys(config['http']['mitm']))
    # Keep the private device-only edit at the top. Public script providers use
    # the same URL declaration as the reviewed native Stash modules, while the
    # optional offline bundle separately retains content-based providers.
    config = {'proxy-providers': config.pop('proxy-providers'), **config}
    return ('# Jimmy Stash 公共订阅入口；由tools/build_subscription.py生成，维护原文件即可。\n'
            '# 固定地址：' + URL + '\n'
            '# 私人机场URL请放在设备本地覆写，不在GitHub填写，不拼接到此公开地址。\n'
            '# 识别标记：JIMMY-STASH；18组，含全部节点/其他地区；无Google或NCloud组。\n'
            '# 内含分流、38条基础域名广告及40款候选专项；12份脚本由Stash按本仓库URL下载。\n'
            '# HTTP/MITM和CA需在设备设置；DNS为DoH，不使用dot.pub或fallback DNS。\n'
            '# 广告修订2026-10-19：18个请求handler、10个响应handler、16条拒绝重写、41个精确MITM主机。\n'
            '# 广告组DIRECT只放行域名规则；HTTP处理须用Stash对应开关停用。\n'
            '# 源码与独立许可：https://github.com/Panzm6111/Jimmy-s-Stash-rules/blob/main/docs/SOURCES.md\n'
            '# 各脚本独立执行、保持原许可；无凭据、无证书私钥、无签到任务。\n'
            '# 当前仅离线验证；实际Stash导入、地区失效语义和广告效果待设备验收。\n' + dump(config))

def verify(text):
    config = yaml.safe_load(text)
    validate_structure(config)
    assert not config.get('rule-providers')
    assert len(config['proxy-groups']) == 18
    assert config['proxy-providers']['机场']['url'] == 'https://example.invalid/REPLACE_ON_DEVICE'
    assert len(config['script-providers']) == 12
    assert len(config['http']['script']) == 28
    assert sum(s['type'] == 'request' for s in config['http']['script']) == 18
    assert len(config['http']['rewrite']) == 16
    assert len(config['http']['mitm']) == len(set(config['http']['mitm'])) == 41
    addons = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'modules/ads').glob('*.stoverride') if p.stem != 'expanded')
    original = merged(*addons)
    for name, provider in original['script-providers'].items():
        assert config['script-providers'][name] == provider
        assert set(provider) == {'url', 'interval'}
        assert provider['interval'] == 86400
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
