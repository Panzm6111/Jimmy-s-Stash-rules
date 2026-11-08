#!/usr/bin/env python3
"""Render the stable public Stash URL from the maintained project; no private input."""
import argparse
import json
from pathlib import Path
import yaml
from config_helpers import flatten, dump, script_references
from validate import ROOT, RAW, load, merged, merge_model, route, validate_structure
from scan_secrets import inspect

OUTPUT = 'config/stash.yaml'
URL = RAW + OUTPUT
VERSION = 'AD-20261020.5'
PROTECTED = 'RULE-SET,东方财富直连,DIRECT'
ADOBE = 'RULE-SET,Adobe服务,Adobe'
MOBILE_ADS = '手机广告补充'

def integrated():
    """The user-facing integrated entry; module files remain maintained sources."""
    modules = sorted(p.relative_to(ROOT) for p in (ROOT / 'modules/ads').glob('*.stoverride')
                     if p.stem != 'expanded')
    config = merged(*modules, 'modules/ads/expanded.stoverride', 'modules/diagnostics/self-check.stoverride')
    # Keep LAN/system exceptions ahead of all ad routes. The module merge model
    # prepends routes; place those reviewed ad-only domains at the core ad slot.
    special = list(dict.fromkeys(r for p in modules for r in load(p).get('rules', [])))
    core_rules = merged()['rules']
    slot = core_rules.index('RULE-SET,基础广告,广告拦截')
    # The expanded snapshot lists these hosts as whole-domain ads. Keep shared
    # Meituan material working, and let reviewed native fixed replies own their
    # paths instead of introducing a competing route-level rejection.
    exceptions = load('modules/ads/expanded.stoverride').get('rules', [])
    config['rules'] = [r for r in core_rules[:slot] if r not in {PROTECTED, ADOBE}] + exceptions + special + [PROTECTED, ADOBE] + core_rules[slot:]
    return config

def remote_payload_documents():
    original = integrated()
    core = merged()
    slot = core['rules'].index('RULE-SET,基础广告,广告拦截')
    exceptions = load('modules/ads/expanded.stoverride').get('rules', [])
    special = list(dict.fromkeys(r for p in sorted((ROOT/'modules/ads').glob('*.stoverride'))
                               if p.stem != 'expanded' for r in load(p.relative_to(ROOT)).get('rules', [])))
    def payload(rules, policy):
        result = []
        for rule in rules:
            parts = rule.split(',')
            assert parts[2] == policy
            result.append(','.join(parts[:2] + parts[3:]))
        return '# Generated from reviewed project sources; preserve SOURCES.md licenses.\n' + dump({'payload':list(dict.fromkeys(result))})
    return {
        'rules/system-direct.yaml':payload([r for r in core['rules'][:slot] if r not in {PROTECTED, ADOBE}], 'DIRECT'),
        'rules/ad-exceptions.yaml':payload(exceptions, 'DIRECT'),
        'rules/app-ads.yaml':payload(special, '广告拦截'),
    }


def remote_integrated():
    config = script_references(integrated())
    core = merged()
    slot = core['rules'].index('RULE-SET,基础广告,广告拦截')
    extra = [('系统直连例外','rules/system-direct.yaml','DIRECT'),
             ('广告路径例外','rules/ad-exceptions.yaml','DIRECT'),
             ('TikTok广告','rules/vendor/tiktok-tracking.yaml','广告拦截'),
             ('TikTok核心','rules/vendor/tiktok-core.yaml','TikTok'),
             ('App广告域名','rules/app-ads.yaml','广告拦截'),
             ('小红书直连','rules/vendor/xiaohongshu-community.yaml','DIRECT'),
             ('抖音直连','rules/vendor/douyin-community.yaml','DIRECT'),
             ('抖音补充','rules/vendor/douyin-bm7.yaml','DIRECT'),
             ('东方财富直连','rules/vendor/eastmoney-community.yaml','DIRECT'),
             ('国内游戏直连','rules/vendor/games-cn-community.yaml','DIRECT'),
             ('国服游戏平台','rules/vendor/games-cn-tagged.yaml','DIRECT'),
             ('Adobe服务','rules/adobe.yaml','Adobe')]
    for name, path, policy in extra:
        config['rule-providers'][name] = {'type':'http','behavior':'classical','url':RAW+path,'interval':86400}
    for provider in config['rule-providers'].values():
        provider.update(type='http',behavior='classical',interval=86400)
    config['rules'] = [f'RULE-SET,{name},{policy}' for name,_,policy in extra] + core['rules'][slot:]
    # Shared Tencent login/CDN/game infrastructure follows reviewed ad and
    # dedicated application rules, but cannot inherit a manual domestic proxy.
    config['rule-providers']['腾讯服务直连'] = {
        'type':'http','behavior':'classical','url':RAW+'rules/vendor/tencent-direct.yaml','interval':86400}
    domestic = config['rules'].index('RULE-SET,国内服务,DIRECT')
    config['rules'].insert(domestic, 'RULE-SET,腾讯服务直连,DIRECT')
    # Literal Chinese destinations (including game UDP) keep a direct fallback.
    # Earlier domain/application decisions still win; never bypass all UDP.
    config['rules'] = ['GEOIP,CN,DIRECT' if r == 'GEOIP,CN,国内直连' else r for r in config['rules']]
    terminal=next(i for i,r in enumerate(config['rules']) if r.startswith('MATCH,'))
    config['rules']=config['rules'][:terminal+1]
    # Supplemental mobile ads may only replace MATCH. Every existing domain,
    # service, private-network and China-IP decision retains higher priority.
    config['rule-providers'][MOBILE_ADS] = {
        'type':'http','behavior':'classical','url':RAW+'rules/vendor/mobile-ads-awa.yaml','interval':86400}
    config['rules'].insert(-1, f'RULE-SET,{MOBILE_ADS},广告拦截')
    from provider_sources import apply
    from stash_ai_guard import apply as guard_ai
    return guard_ai(apply(config))


def render():
    config = remote_integrated()
    # Keep one user-facing config, using Stash's native URL script providers.
    # A historical content-only example was rejected by the user's current core.
    config = {'proxy-providers': config.pop('proxy-providers'), **config}
    return ('#SUBSCRIBED ' + URL + '\n'
            '# Jimmy Stash 公共订阅入口；由 tools/build_subscription.py 生成。\n'
            '# 固定地址：' + URL + '\n'
            '# JIMMY-STASH ' + VERSION + '；21个策略组（含三地区ai、TikTok）、私人订阅接入保留。\n'
            '# JIMMY-ROUTING ROUTE-20261108.1；AI加密DNS跟随海外AI，核心域名本地保护；36个远程规则集。\n'
            '# AI-DNS-20261108.1；需Stash iOS 3.6+；节点解析独立，测速不代表ChatGPT地区可用。\n'
            '# JIMMY-MOBILE-AD MOBILE-AD-20261102.1；秋风纯广告整集补充，仅在所有既有规则之后、MATCH之前生效。\n'
            '# 已整合40款现有专项，11份响应JS使用原生URL加载；扩展域名规则默认启用。\n'
            '# Safari打开https://example.com/jimmy-stash-check可手动开始15分钟排查；默认不记录。\n'
            '# 新增example.com精确MITM仅供自检；自检成功不代表App开屏已去除。\n'
            '# 脚本URL带公开版本参数以区分旧缓存，首次加载仍需联网。\n'
            '# 请在客户端启用本远程配置的自动更新；规则内容/机场/JS按24小时尝试刷新。\n'
            '# 策略组、匹配顺序、HTTP主机或handler结构的变化仍由主配置刷新取得。\n'
            '# 不需另加App或expanded覆写；停用已额外添加的广告覆写，保留私人订阅/白名单。\n'
            '# 当前需求统一为整合入口，不再要求逐App开关；原模块保留作维护来源与旧安装兼容。\n'
            '# 各独立模块/JS保持原许可；来源与完整源码：https://github.com/Panzm6111/Jimmy-s-Stash-rules/blob/main/docs/SOURCES.md\n'
            '# 私人机场URL只在设备本地覆写，不放到GitHub。总代理首次REJECT，需选择出口。\n'
            '# 当前仅离线验证；真实Stash解析、MITM、脚本执行与广告效果待iPhone验收。\n'
            + dump(config))

def verify(text):
    assert text.splitlines()[0] == '#SUBSCRIBED ' + URL
    config = yaml.safe_load(text)
    validate_structure(config)
    assert set(config['rule-providers']) == set(remote_integrated()['rule-providers'])
    assert len(config['rule-providers']) == 36
    assert config['rules'][-2] == f'RULE-SET,{MOBILE_ADS},广告拦截'
    assert config['rules'][-3] == 'GEOIP,CN,DIRECT'
    assert config['rules'].count('RULE-SET,基础广告,广告拦截') == 1
    from provider_sources import plan
    assert config['rule-providers']['基础广告']['url'] == plan()['providers']['基础广告'][0]['url']
    assert len(config['http']['url-rewrite']) == 43
    assert len(config['http']['script']) == 12
    assert sum(h['type'] == 'response' for h in config['http']['script']) == 11
    assert len(config['http']['mitm']) == 59
    assert len(config['script-providers']) == 12
    for name, provider in script_references(integrated())['script-providers'].items():
        assert config['script-providers'][name] == provider
        assert set(provider) == {'url', 'interval'} and provider['interval'] == 86400
    assert len(config['proxy-groups']) == 21
    assert config['proxy-providers']['机场']['url'] == 'https://example.invalid/REPLACE_ON_DEVICE'
    original = integrated()
    # The published profile now has an intentionally fixed China-IP fallback.
    original['rules'] = ['GEOIP,CN,DIRECT' if r == 'GEOIP,CN,国内直连' else r for r in original['rules']]
    from stash_ai_guard import for_clash
    expected_guard = remote_integrated()
    for key in ('proxy-groups', 'proxy-providers', 'dns'):
        assert config[key] == expected_guard[key], 'unexpected AI guard change'
    assert for_clash(config, merged())['dns'] == merged()['dns']
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
    for name, body in remote_payload_documents().items():
        path = ROOT/name
        if args.write:
            path.write_text(body,encoding='utf-8',newline='\n')
        elif not path.is_file() or path.read_text(encoding='utf-8') != body:
            raise ValueError('remote payload drift: '+name)
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
