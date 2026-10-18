#!/usr/bin/env python3
"""Build a device-local package from the single maintained project. Never reads private data."""
from __future__ import annotations
import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile
import yaml
from validate import ROOT, RAW, RULE_KINDS, load, merged, merge_model, route, validate_structure
from scan_secrets import inspect

MAIN = 'Jimmy-Stash.yaml'
ADS = '广告增强.stoverride'
EXPANDED = '扩展域名.stoverride'
AUDIT = 'research/local-bundle-audit.json'

class Literal(str): pass
class BundleDumper(yaml.SafeDumper): pass
BundleDumper.add_representer(Literal, lambda dumper, value: dumper.represent_scalar('tag:yaml.org,2002:str', value, style='|'))

def dump(data):
    return yaml.dump(data, Dumper=BundleDumper, allow_unicode=True, sort_keys=False, width=120)

def flatten(config):
    result = copy.deepcopy(config)
    providers = result.pop('rule-providers', {})
    rules = []
    for rule in result['rules']:
        fields = rule.split(',')
        if fields[0] == 'RULE-SET':
            provider = providers[fields[1]]
            if not provider['url'].startswith(RAW): raise ValueError('non-project rule source')
            for entry in load(provider['url'][len(RAW):])['payload']:
                parts = entry.split(',')
                if parts[0] not in RULE_KINDS: raise ValueError('unsupported classical rule')
                # A payload's optional no-resolve follows the policy in flat rules.
                rules.append(','.join(parts[:2] + [fields[2]] + parts[2:] + fields[3:]))
        else:
            rules.append(rule)
            if fields[0] == 'MATCH': break  # later rules were already unreachable
    result['rules'] = list(dict.fromkeys(rules))
    return result

def inline_scripts(config):
    result = copy.deepcopy(config)
    for name, provider in result.get('script-providers', {}).items():
        url = provider.get('url', '')
        if not url.startswith(RAW): raise ValueError('non-project script source')
        path = ROOT / url[len(RAW):]
        if path.parent != ROOT / 'scripts/ads' or path.suffix != '.js': raise ValueError('unexpected script path')
        result['script-providers'][name] = {'content': Literal(path.read_text())}
    if 'mitm' in result.get('http', {}):
        result['http']['mitm'] = list(dict.fromkeys(result['http']['mitm']))
    return result

def documents():
    # The simple default uses the same basic domain policy as the maintained core.
    main = flatten(merged())
    main.pop('http', None)
    main.pop('script-providers', None)
    # Put the one device-only field at the beginning of the editor.
    main = {'proxy-providers': main.pop('proxy-providers'), **main}
    files = {MAIN: ('# 本地导入；只在iPhone替换下面的机场URL，然后选择总代理地区。\n'
                    '# 已内嵌分流和基础广告规则；不需要下载本仓库远程规则。\n'
                    '# 代理连接/地区失效行为仍需Stash设备验收，初始总代理为REJECT。\n'
                    '# 第三方规则保持原许可；完整来源、许可和可读源码见同包“源码”目录。\n' + dump(main))}
    combined = {}
    for path in sorted((ROOT / 'modules/ads').glob('*.stoverride')):
        if path.stem == 'expanded': continue
        original = load(path.relative_to(ROOT))
        local = inline_scripts(original)
        # Keep per-App packages for independent switches when desired.
        files['按App单独开关/' + path.name] = ('# 独立资源保持各自许可，见包内源码/licenses与docs/SOURCES.md。\n' + dump(local))
        combined = merge_model(combined, local)
    combined['http']['mitm'] = list(dict.fromkeys(combined['http']['mitm']))
    enhanced = {'name': 'Jimmy 广告增强（本地整合）',
                'desc': '40款专项一次导入；需设备自建CA。不解密银行支付。异常先关闭本覆写；逐款开关可改用包内单App覆写。', **combined}
    files[ADS] = ('# 由原40个独立模块组装，内嵌11份独立JS资源；不下载远程脚本。\n'
                  '# 不与“按App单独开关”中的同款重复启用；各独立资源按原许可分发。\n' + dump(enhanced))
    expanded = flatten(merged('modules/ads/expanded.stoverride'))
    files[EXPANDED] = ('# 可选；完整规则顺序含局域网/系统例外，不能只把38,066条前插。\n'
                       '# 本覆写优先于主配置、低于广告增强/私人白名单；默认不导入。\n' + dump({'name': 'Jimmy 扩展域名（本地快照）',
                                          'desc': '更多广告域名，可能误拦；不需要MITM。广告增强应在更高优先级。',
                                          'rules': expanded['rules']}))
    files['先看这里.txt'] = (ROOT / 'docs/LOCAL-IMPORT.md').read_text()
    return files

def verify(files):
    configs = {name: yaml.safe_load(text) for name, text in files.items() if name.endswith(('.yaml', '.stoverride'))}
    main, enhanced, expanded = configs[MAIN], configs[ADS], configs[EXPANDED]
    assert 'http' not in main and 'script-providers' not in main
    assert main['proxy-providers']['机场']['url'] == 'https://example.invalid/REPLACE_ON_DEVICE'
    assert len(main['proxy-groups']) == 18
    assert main['rules'][-1] == 'MATCH,未匹配流量'
    source_by_name = {}
    addon_paths = []
    for path in sorted((ROOT / 'modules/ads').glob('*.stoverride')):
        if path.stem == 'expanded': continue
        addon_paths.append(str(path.relative_to(ROOT)))
        for name, provider in load(path.relative_to(ROOT)).get('script-providers', {}).items():
            source_by_name[name] = (ROOT / provider['url'][len(RAW):]).read_text()
    for name, script in enhanced['script-providers'].items():
        assert script == {'content': source_by_name[name]}, 'inline script changed'
    assert len(source_by_name) == 11
    assert len(enhanced['http']['script']) == 12
    assert len(enhanced['http']['rewrite']) == 32
    assert len(enhanced['http']['mitm']) == len(set(enhanced['http']['mitm'])) == 41
    for config in configs.values():
        assert not config.get('rule-providers')
        for script in config.get('script-providers', {}).values():
            assert set(script) == {'content'}
        for rule in config.get('rules', []): assert not rule.startswith('RULE-SET,')
        for host in config.get('http', {}).get('mitm', []): assert '*' not in host
    # Routing equivalence includes critical direct exceptions, extra ad hosts,
    # mock GeoIP, and both basic/expanded packages with the ad layer applied.
    fixtures = json.loads((ROOT / 'tests/fixtures/routes.json').read_text())
    fixtures += [{'domain': host} for host in ['ads.95516.com', 'ad.12306.cn', 'dsp-x.jd.com', 'api.m.jd.com', 'guide-acs.m.taobao.com']]
    scenarios = [(merged(), main),
                 (merged(*addon_paths), merge_model(main, enhanced)),
                 (merged('modules/ads/expanded.stoverride', *addon_paths), merge_model(merge_model(main, expanded), enhanced))]
    for original, local in scenarios:
        validate_structure(local)
        for case in fixtures:
            args = (case.get('domain', ''), case.get('ip', ''), case.get('country', ''))
            assert route(original, *args) == route(local, *args), 'flattened route changed'
    return {'main_rules': len(main['rules']), 'expanded_rules': len(expanded['rules']),
            'per_app_overrides': len(addon_paths), 'inline_scripts': len(source_by_name),
            'script_handlers': 12, 'rewrite_rules': 32, 'mitm_unique': 41,
            'route_comparisons': len(fixtures) * len(scenarios)}

def public_sources():
    paths = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT).decode().split('\0')
    result = {}
    for name in sorted(set(paths)):
        if not name or name == AUDIT: continue  # avoid self-referential archive hashes
        path = ROOT / name
        if path.is_symlink() or not path.is_file(): raise ValueError('unexpected source member')
        if not path.resolve().is_relative_to(ROOT) or '.git' in path.parts: raise ValueError('unsafe source member')
        result['源码/' + name] = path.read_bytes()
    return result

def archive(files):
    data = {name: body.encode() for name, body in files.items()}
    data.update(public_sources())
    findings = []
    for name, body in data.items(): findings.extend(inspect(body.decode('utf-8'), name))
    if findings:
        for name, line, kind in findings: print(f'BLOCKED {name}:{line} {kind}')
        raise ValueError('sensitive pattern in package')
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, body in sorted(data.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, body, compresslevel=9)
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(set(z.namelist()))
        assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
    return output.getvalue(), len(data)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    files = documents()
    report = verify(files)
    zipped, members = archive(files)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, body in files.items():
        destination = args.output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(body)
    (args.output / 'Jimmy-Stash.zip').write_bytes(zipped)
    report.update({'archive_members': members, 'zip_bytes': len(zipped), 'zip_sha256': hashlib.sha256(zipped).hexdigest(),
                   'archive_secret_findings': 0, 'native_stash_tested': False, 'iphone_tested': False,
                   'script_inline_reference': 'jinzaizhichi/stash-example@c0f273b8539b0aa648e0cab90cae7e5b4922a098 config.yaml script-providers.content（历史原生例；非当前文档/最低版本证明）',
                   'files_sha256': {name: hashlib.sha256(body.encode()).hexdigest() for name, body in files.items()}})
    (ROOT / AUDIT).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({**{k: v for k, v in report.items() if k != 'files_sha256'}, 'output': str(args.output)}, ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
