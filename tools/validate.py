#!/usr/bin/env python3
"""Repository structural checks and routing model. This is NOT a Stash core validator."""
from __future__ import annotations
import argparse
import copy
from functools import lru_cache
import hashlib
import itertools
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW = 'https://raw.githubusercontent.com/Panzm6111/Jimmy-s-Stash-rules/main/'
BUILTINS = {'DIRECT', 'REJECT'}
RULE_KINDS = {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD', 'IP-CIDR', 'IP-CIDR6'}

def local_public_path(url):
    """Resolve only this project's public files and reviewed JS revision queries."""
    assert isinstance(url, str), 'unexpected public URL'
    if not url.startswith(RAW):
        from provider_sources import reference_path
        return reference_path(url)
    path, separator, query = url[len(RAW):].partition('?')
    assert path and '..' not in path and '#' not in path and '\\' not in path and not path.startswith('/'), 'unsafe public path'
    if separator:
        assert path.startswith('scripts/ads/') and path.endswith('.js')
        assert re.fullmatch(r'v=AD-\d{8}\.\d+', query), 'unreviewed public query'
    return path

class UniqueLoader(getattr(yaml, "CSafeLoader", yaml.SafeLoader)):
    pass

def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError('duplicate YAML key')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result

UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)

def load(path):
    return yaml.load((ROOT / path).read_text(), Loader=UniqueLoader)

def merge_model(base, override, path=()):
    """Documented project expectation, requiring comparison with actual Stash merged preview.
    Maps deep-merge; rules and http.script/mitm arrays prepend; other arrays replace.
    The shipped layers have no overlapping group definitions; ad handlers match disjoint endpoints.
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in {'name', 'desc'}:
            continue
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_model(result[key], value, path + (key,))
        elif key == 'rules' or (path == ('http',) and key in {'script', 'mitm', 'url-rewrite'}):
            result[key] = copy.deepcopy(value) + result.get(key, [])
        else:
            result[key] = copy.deepcopy(value)
    return result

def merged(*optional):
    result = merge_model(load('config/main.yaml'), load('config/core.stoverride'))
    for file in optional:
        result = merge_model(result, load(file))
    # Same shape as the device-private overlay, using a public dummy value only.
    private = load('examples/private-provider.stoverride')
    return merge_model(result, private)

@lru_cache(maxsize=32)
def rule_payload_snapshot(path, mtime_ns, size):
    # Routing fixtures share large, unchanged YAML lists. Keep an immutable
    # snapshot per file version; a source edit invalidates its cache key.
    return tuple(load(path)['payload'])

def provider_rules(config):
    result = {}
    for name, provider in config.get('rule-providers', {}).items():
        url = provider['url']
        path = local_public_path(url)
        stat = (ROOT / path).stat()
        # Each caller gets its own list so adversarial-fixture mutations cannot
        # contaminate another route or module combination.
        result[name] = list(rule_payload_snapshot(path, stat.st_mtime_ns, stat.st_size))
    return result

def matches(rule, domain='', address=''):
    parts = rule.split(',')
    kind, value = parts[:2]
    domain = domain.lower().rstrip('.')
    if kind == 'DOMAIN': return domain == value.lower()
    if kind == 'DOMAIN-SUFFIX': return domain == value.lower() or domain.endswith('.' + value.lower())
    if kind == 'DOMAIN-KEYWORD': return value.lower() in domain
    if kind in {'IP-CIDR', 'IP-CIDR6'} and address:
        return ipaddress.ip_address(address) in ipaddress.ip_network(value, strict=False)
    return False

def route(config, domain='', address='', country=''):
    # country is an injected fixture; this code does not perform real GeoIP/DNS.
    sets = provider_rules(config)
    for rule in config['rules']:
        parts = rule.split(',')
        if parts[0] == 'MATCH': return parts[1]
        if parts[0] == 'RULE-SET':
            if any(matches(item, domain, address) for item in sets[parts[1]]): return parts[2]
        elif parts[0] == 'GEOIP':
            if country == parts[1]: return parts[2]
        elif matches(','.join(parts[:2]), domain, address):
            return parts[2]
    raise ValueError('no terminal route')

def validate_provider_sources(config):
    """Check the reported native source requirement, not a replacement Stash parser."""
    for section in ('proxy-providers', 'rule-providers', 'script-providers'):
        for provider in config.get(section, {}).values():
            assert isinstance(provider, dict), 'provider must be a mapping'
            assert 'content' not in provider, 'unsupported content provider field'
            def populated(value):
                return bool(value.strip()) if isinstance(value, str) else isinstance(value, (list, dict)) and bool(value)
            assert any(populated(provider.get(key)) for key in ('url', 'payload', 'path')), \
                'provider source missing: url, payload and path are empty'


def validate_structure(config):
    validate_provider_sources(config)
    groups = config['proxy-groups']
    names = [g['name'] for g in groups]
    assert len(names) == len(set(names)), 'duplicate groups'
    defined = set(names) | BUILTINS
    provider_names = set(config['proxy-providers'])
    graph = {}
    for group in groups:
        assert group['type'] in {'select', 'fallback', 'url-test'}, 'unverified group type'
        assert group.get('proxies'), 'empty static candidate list'
        assert set(group.get('use', [])) <= provider_names, 'missing proxy provider'
        assert set(group['proxies']) <= defined, 'missing policy target'
        graph[group['name']] = [n for n in group['proxies'] if n not in BUILTINS]
        if 'filter' in group: re.compile(group['filter'])
    def visit(name, ancestors):
        assert name not in ancestors, 'policy cycle'
        for child in graph[name]: visit(child, ancestors | {name})
    for name in graph: visit(name, set())
    for rule in config['rules']:
        p = rule.split(',')
        assert p[0] in RULE_KINDS | {'RULE-SET', 'GEOIP', 'MATCH'}, 'unverified rule kind'
        if p[0] == 'RULE-SET': assert p[1] in config['rule-providers'], 'missing rule provider'
        assert (p[1] if p[0] == 'MATCH' else p[2]) in defined, 'missing rule target'
    assert any(r.startswith('MATCH,') for r in config['rules'])
    for name, payload in provider_rules(config).items():
        assert payload and len(payload) == len(set(payload)), 'empty or duplicate rules'
        for rule in payload:
            p = rule.split(',')
            assert p[0] in RULE_KINDS and len(p) in (2, 3), 'invalid provider format'
            if p[0] in {'IP-CIDR', 'IP-CIDR6'}: ipaddress.ip_network(p[1], strict=False)
    scripts = config.get('script-providers', {})
    assert 'rewrite' not in config.get('http', {}), 'legacy HTTP rewrite key must not reappear'
    for item in config.get('http', {}).get('url-rewrite', []):
        pattern, action = item.rsplit(' - ', 1)
        assert action in {'reject', 'reject-200', 'reject-dict', 'reject-array', 'reject-img'}, 'unreviewed rewrite action'
        re.compile(pattern)
    for item in config.get('http', {}).get('script', []):
        assert item['name'] in scripts, 'missing script provider'
        assert item['type'] in {'request', 'response'}
        assert item['require-body'] is (item['type'] == 'response')
        assert item['timeout'] <= 10
        provider = scripts[item['name']]
        assert set(provider) == {'url', 'interval'}, 'unreviewed script provider format'
        assert isinstance(provider['url'], str) and provider['url'].strip(), 'empty script URL'
        assert provider['interval'] == 86400, 'unexpected script refresh interval'
        assert (ROOT / local_public_path(provider['url'])).is_file()
    for url in [x['url'] for x in config.get('rule-providers', {}).values()] + [x['url'] for x in scripts.values() if 'url' in x]:
        assert (ROOT / local_public_path(url)).is_file(), 'broken local public URL'

class ProjectChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = merged()
        cls.groups = {g['name']: g for g in cls.config['proxy-groups']}

    def test_all_yaml_has_unique_keys(self):
        for ext in ('*.yaml', '*.yml', '*.stoverride'):
            for file in ROOT.rglob(ext):
                if '.git' not in file.parts: self.assertIsNotNone(load(file.relative_to(ROOT)))

    def test_all_provider_sources_reject_empty_and_content_only_declarations(self):
        # Reproduce the user's failure shape, including unreferenced providers.
        for section in ('proxy-providers', 'rule-providers', 'script-providers'):
            for provider in ({}, {'interval': 86400}, {'url': '', 'path': '', 'payload': []},
                             {'url': '   '}, {'content': '// historical inline source'}):
                with self.subTest(section=section, provider=provider), self.assertRaises(AssertionError):
                    validate_provider_sources({section: {'example': provider}})
        valid = merged('modules/ads/taobao.stoverride')
        validate_provider_sources(valid)
        broken = copy.deepcopy(valid)
        broken['script-providers']['unused'] = {'content': '// not a recognized source'}
        with self.assertRaisesRegex(AssertionError, 'content'):
            validate_structure(broken)

    def test_layer_combinations(self):
        options = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'modules/ads').glob('*.stoverride'))
        # Full validation of each single module and the complete configuration.
        # Exhaustive 2^N enumeration is impractical as independently scoped apps grow.
        for layers in [[], *[[item] for item in options], options, list(reversed(options))]:
            config = merged(*layers, 'examples/private-allowlist.stoverride')
            validate_structure(config)
            expected = sum(len(load(item).get('http', {}).get('script', [])) for item in layers)
            self.assertEqual(len(config.get('http', {}).get('script', [])), expected)

    def test_all_module_pairs_preserve_independent_actions(self):
        # Test every pair in both orders with a small merge, then test the full merge
        # above. Endpoint tests separately reject overlaps and business URLs.
        modules = [(p, load(p)) for p in sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'modules/ads').glob('*.stoverride'))]
        for (pa, a), (pb, b) in itertools.permutations(modules, 2):
            config = merge_model(a, b)
            for key in ('script', 'mitm', 'url-rewrite'):
                self.assertEqual(config.get('http', {}).get(key, []), b.get('http', {}).get(key, []) + a.get('http', {}).get(key, []), (pa, pb, key))
            self.assertEqual(config.get('rules', []), b.get('rules', []) + a.get('rules', []), (pa, pb))
            self.assertEqual(set(config.get('script-providers', {})), set(a.get('script-providers', {})) | set(b.get('script-providers', {})))

    def test_reviewed_ad_catalog_and_generated_files(self):
        from generate_ad_modules import rendered
        catalog = json.loads((ROOT / 'research/ad-catalog.json').read_text())
        lock = json.loads((ROOT / 'research/sources.lock.json').read_text())
        source_hashes = {s['url']: s['sha256'] for s in lock['ad_supporting_sources']}
        for source in catalog['sources'].values():
            self.assertEqual(source_hashes[source['url']], source['sha256'])
        for file, body in rendered(catalog).items(): self.assertEqual((ROOT / file).read_text(), body)
        all_modules = [load(p.relative_to(ROOT)) for p in (ROOT / 'modules/ads').glob('*.stoverride')]
        patterns = [r.rsplit(' - ', 1)[0] for m in all_modules for r in m.get('http', {}).get('url-rewrite', [])]
        patterns += [s['match'] for m in all_modules for s in m.get('http', {}).get('script', [])]
        for item in catalog['modules']:
            module = load(item['file'])
            self.assertFalse(item['default_enabled'])
            self.assertFalse(item['device_tested'])
            self.assertEqual(module.get('http', {}).get('mitm', []), item['mitm'])
            self.assertTrue((ROOT / catalog['sources'][item['source']]['license_file']).is_file())
            cases = item['rewrite'] + ([item['script']] if item['script'] else [])
            for case in cases:
                self.assertRegex(case['positive'], case.get('match'))
                self.assertEqual(sum(bool(re.search(pattern, case['positive'])) for pattern in patterns), 1, case['positive'])
                for url in case['negative']:
                    self.assertEqual(sum(bool(re.search(pattern, url)) for pattern in patterns), 0, url)
                # Never accept same-prefix foreign domains or arbitrary appended paths.
                from urllib.parse import urlsplit
                parsed = urlsplit(case['positive'])
                deceptive = case['positive'].replace(parsed.netloc, parsed.hostname + '.evil.example')
                self.assertEqual(sum(bool(re.search(pattern, deceptive)) for pattern in patterns), 0)
        protected_hosts = {'wallet.95516.com', 'tysdk.95516.com', 'ms.jr.jd.com', 'mobilegw.alipay.com', 'ccbj.ccb.com.cn', 'ebsnew.boc.cn'}
        self.assertTrue(protected_hosts.isdisjoint(h for item in catalog['modules'] for h in item['mitm']))

    def test_generated_ad_runtime_and_native_fixed_actions(self):
        from build_ad_scripts import rendered
        for file, body in rendered().items(): self.assertEqual((ROOT / file).read_text(), body)
        from build_ad_diagnostics import rendered as probe_rendered
        for file, body in probe_rendered().items(): self.assertEqual((ROOT / file).read_text(), body)
        self.assertFalse((ROOT / 'scripts/ads/empty-response.js').exists())
        all_paths = sorted(p.relative_to(ROOT) for p in (ROOT / 'modules/ads').glob('*.stoverride') if p.stem != 'expanded')
        config = merged(*all_paths)
        self.assertTrue(all(h['type'] == 'response' for h in config['http']['script']))
        self.assertTrue(all(h.get('argument') == 'diagnostic=0' for h in config['http']['script']))
        # Native actions own fixed responses. No JS handler may also own them.
        for item in json.loads((ROOT / 'research/ad-catalog.json').read_text())['modules']:
            for case in item['rewrite']:
                self.assertFalse(any(re.search(h['match'], case['positive']) for h in config['http']['script']))

    def test_public_expanded_provider_is_reachable_and_ordered(self):
        base = load('config/stash.yaml')
        expanded = base  # integrated public entry includes the expanded package
        self.assertNotEqual(route(merged(), 'ad.12306.cn'), '广告拦截')
        self.assertEqual(route(expanded, 'ad.12306.cn'), '广告拦截')
        for host in ['api.push.apple.com', 'login.microsoftonline.com']:
            self.assertEqual(route(expanded, host), 'DIRECT')
        self.assertEqual(route(expanded, address='192.168.17.1'), 'DIRECT')
        allowed = merge_model(expanded, {'rules':['DOMAIN,ad.12306.cn,DIRECT']})
        self.assertEqual(route(allowed, 'ad.12306.cn'), 'DIRECT')
        self.assertLess(base['rules'].index('RULE-SET,基础广告,广告拦截'), base['rules'].index('MATCH,未匹配流量'))
        self.assertEqual(set(base['rule-providers']), {r.split(',')[1] for r in base['rules'] if r.startswith('RULE-SET,')})

    def test_each_app_switch_removes_its_actions_without_touching_routing(self):
        # Per-App switches belong to the existing layered installation only.
        base = merged()
        paths = sorted(p for p in (ROOT / 'modules/ads').glob('*.stoverride') if p.stem != 'expanded')
        self.assertNotIn('http', base)
        self.assertNotIn('script-providers', base)
        for path in paths:
            module = load(path.relative_to(ROOT))
            on = merge_model(base, module)
            off = copy.deepcopy(base)  # native UI excludes the disabled override
            self.assertEqual(on['proxy-providers'], off['proxy-providers'])
            self.assertEqual(on['proxy-groups'], off['proxy-groups'])
            self.assertEqual(on['dns'], off['dns'])
            self.assertFalse(off.get('http'))
            for key in ('script', 'url-rewrite'):
                self.assertEqual(on.get('http', {}).get(key, []), module.get('http', {}).get(key, []))
        # Toggle Taobao with Weibo still enabled: no second Taobao match survives.
        weibo = load('modules/ads/weibo.stoverride')
        off = merge_model(base, weibo)
        taobao = load('modules/ads/taobao.stoverride')
        url = 'https://guide-acs.m.taobao.com/gw/mtop.taobao.wireless.home.splash.awesome.get/1.0/'
        self.assertFalse(any(re.search(h['match'], url) for h in off['http']['script']))
        self.assertEqual(len(off['http']['script']), len(weibo['http']['script']))

    def test_screenshot_inventory_complete_and_scoped(self):
        inventory = json.loads((ROOT / 'research/app-inventory.json').read_text())
        apps = inventory['apps']
        self.assertEqual(len(apps), 135)
        self.assertEqual(len({a['name'] for a in apps}), 135)
        self.assertNotIn('隐藏的 App', {a['name'] for a in apps})
        for app in apps:
            self.assertTrue(app['decision'])
            self.assertTrue(app['reason'])
            self.assertFalse(app['device_tested'])
            for file in app['modules']: self.assertTrue((ROOT / file).is_file())

    def test_ad_domain_modules_route_and_allowlist(self):
        catalog = json.loads((ROOT / 'research/ad-catalog.json').read_text())
        for module in catalog['modules']:
            if not module['domains']: continue
            config = merged(module['file'])
            if not module['mitm']: self.assertNotIn('http', load(module['file']))
            for host in module['domains']:
                self.assertEqual(route(config, host), '广告拦截')
                whitelist = {'rules': ['DOMAIN,' + host + ',DIRECT']}
                self.assertEqual(route(merge_model(config, whitelist), host), 'DIRECT')
        all_config = merged(*[m['file'] for m in catalog['modules']])
        for host in ['login.microsoftonline.com', 'api.push.apple.com']:
            self.assertEqual(route(all_config, host), 'DIRECT')

    def test_generated_research_matches_inventory(self):
        from render_app_research import render
        for file, text in render().items(): self.assertEqual((ROOT / file).read_text(), text)
        from render_ad_architecture import rendered
        for file, text in rendered().items():
            self.assertEqual((ROOT / file).read_text(), text)
            self.assertNotIn('](../modules' + chr(92), text)

    def test_added_ad_scene_urls_do_not_catch_business_or_duplicate_handlers(self):
        tb = next(r for r in load('modules/ads/taobao.stoverride')['http']['url-rewrite'] if 'noah' in r).rsplit(' - ',1)[0]
        prefix='https://acs.m.taobao.com/gw/mtop.etao.noah.query/1.0/'
        for query in ['?scene=tao_splash', '?data=%7B%22scene%22%3A%22tao_splash%22%7D']:
            self.assertRegex(prefix+query, tb)
        for url in [prefix+'?scene=normal_coupon',prefix+'?scene=not_tao_splash',prefix+'?scene=tao_splash_extra',
                    prefix.replace('.query/','.queryExtra/')+'?scene=tao_splash',
                    prefix.replace('acs.m.taobao.com','acs.m.taobao.com.evil.example')+'?scene=tao_splash']:
            self.assertNotRegex(url, tb)
        for module, hosts, normal in [
            ('xiaohongshu',['ads-img-qc.xhscdn.com','ads-video-al.xhscdn.com'],'sns-img-qc.xhscdn.com'),
            ('weibo',['sdkapp.uve.weibo.com','wbapp.uve.weibo.com','adimg.uve.weibo.com'],'api.weibo.cn')]:
            config=merged('modules/ads/'+module+'.stoverride')
            for host in hosts:self.assertEqual(route(config,host),'广告拦截')
            self.assertNotEqual(route(config,normal),'广告拦截')

    def test_local_download_bundle(self):
        import io
        import zipfile
        from build_local_bundle import documents, verify, archive
        files = documents()
        report = verify(files)
        self.assertEqual(report['per_app_overrides'], 40)
        zipped, count = archive(files)
        with zipfile.ZipFile(io.BytesIO(zipped)) as bundle:
            self.assertEqual(count, len(bundle.namelist()))
            self.assertIn('Jimmy-Stash.yaml', bundle.namelist())
            self.assertIn('广告增强.stoverride', bundle.namelist())
            self.assertTrue(any(n.startswith('源码/licenses/') for n in bundle.namelist()))
            for file, body in files.items(): self.assertEqual(bundle.read(file).decode(), body)

    def test_public_subscription_entry(self):
        from build_subscription import render, verify, OUTPUT
        text = render()
        self.assertEqual((ROOT / OUTPUT).read_text(), text)
        verify(text)

    def test_region_names_and_nonmatches(self):
        fixtures = json.loads((ROOT / 'tests/fixtures/regions.json').read_text())
        for region, names in fixtures['positive'].items():
            for name in names:
                self.assertRegex(name, self.groups[region]['filter'], msg=region)
                hits = [n for n in fixtures['positive'] if re.search(self.groups[n]['filter'], name)]
                self.assertEqual(hits, [region], msg=name)
        for name in fixtures['negative']:
            self.assertFalse(any(re.search(self.groups[n]['filter'], name) for n in fixtures['positive']), name)

    def test_other_and_all_nodes_do_not_hide_connection_candidates(self):
        fixtures = json.loads((ROOT / 'tests/fixtures/regions.json').read_text())
        self.assertEqual(len(self.groups), 21)
        other = self.groups['其他地区']
        all_nodes = self.groups['自动节点']
        self.assertEqual(other['type'], 'url-test')
        self.assertEqual(other['proxies'], ['REJECT'])
        self.assertEqual(other['use'], ['机场'])
        self.assertEqual(all_nodes['type'], 'url-test')
        self.assertEqual(all_nodes['proxies'], ['REJECT'])
        self.assertEqual(all_nodes['use'], ['机场'])
        for name in fixtures['other']:
            self.assertRegex(name, other['filter'])
        # Traffic units such as "1024.5 GB" must not be treated as Great Britain.
        for name in ['剩余流量：1024.5 GB', 'Remaining Traffic: 100GB', 'Traffic Remaining 20 GB']:
            self.assertNotRegex(name, other['filter'])
        # The positive other-country list is explicitly not a strict complement.
        # Flat all-nodes must retain every ordinary and unclassified node name.
        for name in [n for values in fixtures['positive'].values() for n in values] + fixtures['other'] + fixtures['unclassified']:
            self.assertRegex(name, all_nodes['filter'], name)
        self.assertNotRegex('Custom-Node-007', other['filter'])
        for app in ['总代理', '海外AI', 'Netflix', 'YouTube', 'Telegram', 'Apple', 'Microsoft', '未匹配流量']:
            for choice in ['其他地区', '自动节点', '手动节点']:
                self.assertIn(choice, self.groups[app]['proxies'])
        self.assertEqual(self.groups['手动节点']['use'], ['机场'])

    def test_info_names_cannot_be_selected_from_flat_or_app_node_lists(self):
        from generate_node_filters import check, SELECTORS
        fixtures = json.loads((ROOT / 'tests/fixtures/regions.json').read_text())
        self.assertTrue(check(load('config/core.stoverride')))
        for selector in SELECTORS:
            group = self.groups[selector]
            for info in fixtures['info']:
                self.assertNotRegex(info, group['filter'], selector)
            # Filtering dynamic nodes must not hide builtins or static groups.
            for candidate in group['proxies']:
                self.assertRegex(candidate, group['filter'], selector)
            for node in fixtures['unclassified']:
                self.assertRegex(node, group['filter'], selector)
        for group in self.groups.values():
            self.assertNotIn('exclude-filter', group)
            for extension in ['(?!', '(?=', '(?<=', '(?<!', r'\1', '\\ ']:
                self.assertNotIn(extension, group.get('filter', ''))

    def test_public_entry_has_project_dns_and_no_foreign_groups(self):
        config = load('config/stash.yaml')
        self.assertEqual(config['dns']['nameserver'], [
            'https://dns.alidns.com/dns-query', 'https://doh.pub/dns-query'])
        self.assertNotIn('fallback', config['dns'])
        self.assertNotIn('dot.pub', json.dumps(config['dns']))
        self.assertTrue({'Google', 'NCloud'}.isdisjoint(g['name'] for g in config['proxy-groups']))
        for provider in config.get('script-providers', {}).values():
            self.assertEqual(set(provider), {'url', 'interval'})
            self.assertTrue(provider['url'].startswith(RAW + 'scripts/ads/'))
            self.assertEqual(provider['interval'], 86400)

    def test_integrated_entry_has_all_modules_and_preserves_non_ad_priority(self):
        from build_subscription import integrated, verify
        config = verify((ROOT / 'config/stash.yaml').read_text())
        expected = integrated()
        self.assertEqual(config['http'], {
            **expected['http'], 'mitm': list(dict.fromkeys(expected['http']['mitm']))})
        self.assertEqual(len(config['script-providers']), 12)
        # A LAN destination keeps the earlier direct exception even with an ad
        # hostname; private whitelist prepends and can override public ads.
        self.assertEqual(route(config, 'ads-img-al.xhscdn.com', '192.168.17.1'), 'DIRECT')
        self.assertEqual(route(config, 'ads-img-al.xhscdn.com'), '广告拦截')
        before = merge_model(config, {'rules': ['DOMAIN,ads-img-al.xhscdn.com,DIRECT']})
        self.assertEqual(route(before, 'ads-img-al.xhscdn.com'), 'DIRECT')
        # Expanded domains must not short-circuit reviewed HTTP responses or
        # whole-block shared media hosts used by path-specific rewrites.
        for host in config['http']['mitm']:
            self.assertNotEqual(route(config, host), '广告拦截', host)
        for host in ['flowplus.meituan.net', 'bootpreload.uve.weibo.com']:
            self.assertEqual(route(config, host), 'DIRECT')
        self.assertTrue(any(re.search(item.rsplit(' - ', 1)[0],
            'https://flowplus.meituan.net/v1/normal/linglong/advert.jpg')
            for item in config['http']['url-rewrite']))

    def test_self_check_is_exact_and_scripts_use_public_revision_queries(self):
        from build_ad_scripts import VERSION
        config = load('config/stash.yaml')
        requests = [h for h in config['http']['script'] if h['type'] == 'request']
        self.assertEqual(len(requests), 1)
        check = requests[0]
        self.assertEqual(check['name'], 'jimmy_ads_self_check')
        self.assertFalse(check['require-body'])
        self.assertIn('example.com', config['http']['mitm'])
        for url in ['https://example.com/jimmy-stash-check', 'http://example.com/jimmy-stash-check?start=1']:
            self.assertRegex(url, check['match'])
        for url in ['https://example.com/', 'https://example.com.evil.invalid/jimmy-stash-check',
                    'https://example.com/jimmy-stash-check-extra', 'https://example.com:8443/jimmy-stash-check']:
            self.assertNotRegex(url, check['match'])
        for provider in config['script-providers'].values():
            self.assertTrue(provider['url'].endswith('?v=' + VERSION))
            self.assertTrue((ROOT / local_public_path(provider['url'])).is_file())
        for url in [RAW + 'scripts/ads/taobao.js?token=EXAMPLE_NOT_A_SECRET',
                    RAW + '../private.yaml', RAW + '/private.yaml',
                    RAW + 'rules/ads-basic.yaml?v=' + VERSION]:
            with self.assertRaises(AssertionError):
                local_public_path(url)

    def test_automatic_pools_probe_and_fail_closed_references(self):
        # Structural evidence only; Stash owns latency selection and failed-probe handling.
        pools = {'自动节点', '美国', '日本', '香港', '新加坡', '台湾', '其他地区', 'ai'}
        self.assertEqual({g['name'] for g in self.groups.values() if g['type'] == 'url-test'}, pools)
        for name in pools:
            group = self.groups[name]
            self.assertEqual(group['url'], 'https://www.gstatic.com/generate_204')
            self.assertEqual(group['interval'], 1800)
            self.assertEqual(group['proxies'], ['REJECT'])
            self.assertRegex('REJECT', group['filter'])
            self.assertEqual(group['use'], ['机场'])
            self.assertNotIn('DIRECT', group['proxies'])
        self.assertEqual(self.groups['手动节点']['type'], 'select')
        self.assertEqual(self.groups['手动节点']['filter'], self.groups['自动节点']['filter'])
        self.assertEqual(self.groups['海外AI']['proxies'][0], '美国')
        self.assertEqual(self.groups['Apple']['proxies'][0], 'DIRECT')
        self.assertEqual(self.groups['Microsoft']['proxies'][0], 'DIRECT')
        self.assertEqual(self.groups['总代理']['proxies'][0], 'REJECT')

    def test_independent_software_choices(self):
        choices = {'海外AI': '美国', 'Netflix': '日本', 'YouTube': '香港'}
        for app, value in choices.items(): self.assertIn(value, self.groups[app]['proxies'])
        before = dict(choices)
        choices['海外AI'] = '台湾'
        self.assertEqual(choices['Netflix'], before['Netflix'])
        self.assertEqual(choices['YouTube'], before['YouTube'])
        for name in ['Netflix', 'YouTube', 'Telegram', '未匹配流量']:
            self.assertEqual(self.groups[name]['proxies'][0], '总代理')
            self.assertEqual(self.groups[name]['use'], ['机场'])
        self.assertIn('总代理', self.groups['海外AI']['proxies'])
        self.assertEqual(self.groups['海外AI']['use'], ['机场'])

    def test_renamed_groups_have_no_stale_references(self):
        obsolete = {'全部节点', 'OpenAI'}
        for config in [self.config, load('config/stash.yaml')]:
            self.assertTrue(obsolete.isdisjoint(g['name'] for g in config['proxy-groups']))
            for group in config['proxy-groups']:
                self.assertTrue(obsolete.isdisjoint(group['proxies']))
            for rule in config['rules']:
                self.assertTrue(obsolete.isdisjoint(rule.split(',')))
            self.assertTrue(obsolete.isdisjoint(config.get('rule-providers', {})))

    def test_representative_route_order(self):
        fixtures = json.loads((ROOT / 'tests/fixtures/routes.json').read_text())
        for case in fixtures:
            self.assertEqual(route(self.config, case.get('domain', ''), case.get('ip', ''), case.get('country', '')), case['policy'], case)

    def test_expanded_ad_critical_route_order(self):
        config = merged('modules/ads/expanded.stoverride')
        fixtures = json.loads((ROOT / 'tests/fixtures/routes.json').read_text())
        for case in fixtures:
            self.assertEqual(route(config, case.get('domain', ''), case.get('ip', ''), case.get('country', '')), case['policy'], case)

    def test_basic_ads_cover_reviewed_sdks_but_preserve_business_and_allowlist(self):
        for host in ['v2.gdt.qq.com', 'adsmind.gdtimg.com', 'ads.pgdt.gtimg.cn',
                     'ads.pangolin-sdk-toutiao.com', 'sf1.pglstatp-toutiao.com',
                     'mobads.baidu.com', 'config.unityads.unitychina.cn']:
            self.assertEqual(route(self.config, host), '广告拦截', host)
            allowed = merge_model(self.config, {'rules': ['DOMAIN,' + host + ',DIRECT']})
            self.assertEqual(route(allowed, host), 'DIRECT')
        for host in ['api.m.jd.com', 'guide-acs.m.taobao.com', 'acs.m.taobao.com',
                     'bootrealtime.uve.weibo.com', 'mp.weixin.qq.com', 'wallet.95516.com',
                     'mobilegw.alipay.com', 'login.microsoftonline.com', 'api.push.apple.com']:
            self.assertNotEqual(route(self.config, host), '广告拦截', host)

    def test_expanded_preserves_lan_and_service_exceptions(self):
        from unittest.mock import patch
        config = merged('modules/ads/expanded.stoverride')
        exceptions = ['DOMAIN,flowplus.meituan.net,DIRECT',
                      'DOMAIN,bootpreload.uve.weibo.com,DIRECT']
        self.assertEqual(config['rules'], exceptions + self.config['rules'])
        self.assertEqual(load('modules/ads/expanded.stoverride')['rules'], exceptions)
        for host in ['flowplus.meituan.net', 'bootpreload.uve.weibo.com']:
            self.assertEqual(route(config, host), 'DIRECT')
        sets = provider_rules(config)
        self.assertTrue(set(provider_rules(self.config)['基础广告']) <= set(sets['基础广告']))
        # A future over-broad upstream entry must not outrank built-in safety exceptions.
        sets['基础广告'] += ['DOMAIN-SUFFIX,push.apple.com', 'DOMAIN,login.microsoftonline.com', 'IP-CIDR,192.168.0.0/16']
        with patch(__name__ + '.provider_rules', return_value=sets):
            self.assertEqual(route(config, 'api.push.apple.com'), 'DIRECT')
            self.assertEqual(route(config, 'login.microsoftonline.com'), 'DIRECT')
            self.assertEqual(route(config, address='192.168.17.1'), 'DIRECT')

    def test_native_handler_patterns(self):
        config = merged(*sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'modules/ads').glob('*.stoverride')))
        cases = [('https://app.bilibili.com/x/v2/splash/list?x=1', 1),
                 ('https://app.bilibili.com/x/v2/feed/index', 1),
                 ('https://tiebac.baidu.com/c/f/ad/getSplashAd', 1),
                 ('https://app.bilibili.com/account/login', 0),
                 ('https://app.bilibili.com/x/v2/splash/listFake', 0),
                 ('https://app.bilibili.com.evil.example/x/v2/splash/list', 0),
                 ('https://edith.xiaohongshu.com/api/sns/v1/system_service/splash_config?x=1', 1),
                 ('https://guide-acs.m.taobao.com/gw/mtop.taobao.wireless.home.splash.awesome.get/1.0/?x=1', 1),
                 ('https://bootrealtime.uve.weibo.com/v1/ad/realtime?x=1', 1),
                 ('https://bootpreload.uve.weibo.com/v1/ad/preload?x=1', 1),
                 ('https://guide-acs.m.taobao.com/gw/mtop.taobao.trade.order.create/1.0/?x=1', 0),
                 ('https://edith.xiaohongshu.com/api/sns/v1/note/feed?x=1', 0)]
        for url, count in cases:
            patterns = [item['match'] for item in config['http']['script']] + [r.rsplit(' - ',1)[0] for r in config['http']['url-rewrite']]
            self.assertEqual(sum(bool(re.search(p, url)) for p in patterns), count)

    def test_provider_checker_rejects_invalid_fixtures(self):
        from check_provider import check
        valid = load('examples/provider-simulated.yaml')
        self.assertEqual(check(valid), {'ss': 1, 'vless': 1})
        invalid = copy.deepcopy(valid)
        invalid['proxies'][1]['name'] = invalid['proxies'][0]['name']
        with self.assertRaises(ValueError): check(invalid)
        for node in [{'name': 'dummy', 'type': 'ss', 'server': 'example.invalid', 'port': 443},
                     {'name': 'dummy', 'type': 'vless', 'server': 'example.invalid', 'port': 443, 'uuid': 'not-a-uuid'}]:
            with self.assertRaises(ValueError): check({'proxies': [node]})

    def test_allowlist_precedes_ads_in_merge_model(self):
        private_rule = {'rules': ['DOMAIN,ad.doubleclick.net,DIRECT']}
        self.assertEqual(route(self.config, 'ad.doubleclick.net'), '广告拦截')
        config = merge_model(self.config, private_rule)
        self.assertEqual(route(config, 'ad.doubleclick.net'), 'DIRECT')

    def test_private_map_survives_public_update_in_merge_model(self):
        local = {'proxy-providers': {'机场': {'url': 'https://subscription.example.invalid/DEVICE_ONLY'}}}
        initial = merge_model(merge_model(load('config/main.yaml'), load('config/core.stoverride')), local)
        updated = load('config/core.stoverride')
        updated['desc'] = 'public update fixture'
        future = merge_model(merge_model(load('config/main.yaml'), updated), local)
        self.assertEqual(initial['proxy-providers'], future['proxy-providers'])
        self.assertEqual([g['name'] for g in initial['proxy-groups']], [g['name'] for g in future['proxy-groups']])
        # Native UI choice persistence is intentionally not asserted here.

    def test_upstream_lock_integrity(self):
        lock = json.loads((ROOT / 'research/sources.lock.json').read_text())
        for item in lock['resources'] + lock['ad_scripts']:
            self.assertEqual(hashlib.sha256((ROOT / item['output']).read_bytes()).hexdigest(), item['output_sha256'])

    def test_ai_source_manifest_and_narrow_domain_scope(self):
        from community_rules import verify,generated_documents
        verify(ROOT)
        self.assertEqual(load('rules/openai.yaml')['payload'],yaml.safe_load(generated_documents()['rules/openai.yaml'])['payload'])
        # Whole maintained sets determine service classification; no local additions.
        for host in ['google.com','accounts.google.com','googleapis.com','www.microsoft.com','login.microsoftonline.com','github.com','cdn.cloudflare.net']:
            self.assertFalse(any(matches(rule,host) for rule in load('rules/openai.yaml')['payload']),host)

    def test_tiktok_maintained_core_precedes_generic_ads(self):
        config=load('config/stash.yaml')
        self.assertLess(config['rules'].index('RULE-SET,TikTok核心,TikTok'),config['rules'].index('RULE-SET,基础广告,广告拦截'))
        for host in ['ttcdn-us.com','ttlivecdn.com','ttoverseaus.net','ttwstatic.com','roovza-launches.appsflyersdk.com','roovza.inapps.appsflyersdk.com','roovza.launches.appsflyersdk.com','roovza.skadsdk.appsflyersdk.com']:
            self.assertEqual(route(config,host,country='CN'),'TikTok',host)
        self.assertEqual(route(config,'analytics.tiktok.com'),'广告拦截')
        for host in ['www.facebook.com','discord.com','web.whatsapp.com','line.me','signal.org']:
            self.assertEqual(route(config,host),'TikTok',host)
        self.assertEqual(route(config,'github.com'),'总代理')
        self.assertEqual(route(config,'api.github.com'),'海外AI')

    def test_ai_four_region_pool_and_choices(self):
        fixtures = json.loads((ROOT / 'tests/fixtures/regions.json').read_text())
        defaults = {'总代理':'REJECT', '手动节点':'REJECT', '海外AI':'美国',
                    'TikTok':'美国', 'Netflix':'总代理', 'YouTube':'总代理',
                    'Telegram':'总代理', 'Apple':'DIRECT', 'Microsoft':'DIRECT', 'Adobe':'美国',
                    '未匹配流量':'总代理', '国内直连':'DIRECT', '广告拦截':'REJECT'}
        for config in [self.config, load('config/stash.yaml')]:
            validate_structure(config)
            groups = {g['name']: g for g in config['proxy-groups']}
            self.assertNotIn('日本+美国', groups)
            pool = groups['ai']
            self.assertEqual(pool['type'], 'url-test')
            self.assertEqual(pool['proxies'], ['REJECT'])
            for region, names in fixtures['positive'].items():
                for name in names:
                    self.assertEqual(bool(re.search(pool['filter'], name)), region != '香港', name)
            for name in fixtures['other'] + fixtures['negative'] + fixtures['info'] + ['DIRECT', 'ai']:
                self.assertNotRegex(name, pool['filter'])
            self.assertEqual({g['name']:g['proxies'][0] for g in groups.values()
                              if g['type']=='select'}, defaults)
            for group in groups.values():
                self.assertNotIn('日本+美国', group['proxies'])
                self.assertEqual(group['proxies'].count('ai'), int(group['type']=='select' and group['name']!='手动节点'))

    def test_social_routes_share_tiktok_policy(self):
        self.assertEqual(self.groups['TikTok']['proxies'][0], '美国')
        config = load('config/stash.yaml')
        for domain in ['www.tiktok.com', 'api.tiktokv.com', 'www.instagram.com', 'scontent.cdninstagram.com', 'x.com', 'api.twitter.com', 'video.twimg.com']:
            self.assertEqual(route(config, domain), 'TikTok', domain)
        for domain in ['www.douyin.com', 'www.example.org']:
            self.assertNotEqual(route(config, domain), 'TikTok', domain)

    def test_checkin_stays_deferred(self):
        plan = json.loads((ROOT / 'research/checkin-plan.json').read_text())
        self.assertEqual(len(plan['scope']), 24)
        self.assertEqual(len(set(plan['scope'])), 24)
        self.assertEqual(plan['enabled'], [])
        self.assertFalse(plan['runtime_scripts_created'])
        self.assertFalse(plan['cron_entries_created'])
        self.assertTrue(set(plan['scope']).isdisjoint(plan['excluded']))
        self.assertEqual(plan['status'], 'deferred-by-user')
        self.assertTrue(plan['resume_requires_explicit_request'])
        self.assertFalse(list((ROOT / 'scripts').glob('checkin/**/*')))
        for file in [*(ROOT / 'config').glob('*.yaml'), ROOT / 'config/core.stoverride', *(ROOT / 'modules').rglob('*.stoverride')]:
            self.assertNotRegex(file.read_text(), r'(?m)^\s*(cron|cron-expression):')

    def test_subscription_example(self):
        example = load('examples/provider-simulated.yaml')
        self.assertEqual({x['type'] for x in example['proxies']}, {'ss', 'vless'})
        self.assertEqual(len({x['name'] for x in example['proxies']}), len(example['proxies']))
        for node in example['proxies']:
            self.assertFalse(node.get('skip-cert-verify', False))

    def test_bad_policy_graph_is_rejected(self):
        cyclic = copy.deepcopy(self.config)
        cyclic['proxy-groups'][0]['proxies'] = ['海外AI']
        with self.assertRaises(AssertionError): validate_structure(cyclic)
        broken = copy.deepcopy(self.config)
        broken['proxy-groups'][0]['proxies'] = ['nonexistent-policy']
        with self.assertRaises(AssertionError): validate_structure(broken)

    def test_fmz_native_additions_and_handler_separation(self):
        from urllib.parse import urlsplit
        config = load('config/stash.yaml')
        rewrites = [line.rsplit(' - ', 1) for line in config['http']['url-rewrite']]
        handlers = config['http']['script']
        cases = [
            ('https://acs.m.taobao.com/gw/mtop.alibaba.advertisementservice.getadv/1.0/', 'reject-dict'),
            ('http://www.xiaohongshu.com/api/sns/v1/ads/resource?x=1', 'reject-dict'),
            ('https://api.zhihu.com/commercial_api/article/123/bottom-v2', 'reject-dict'),
            ('http://interface9.music.163.com/eapi/ad/get', 'reject-dict'),
            ('https://flowplus.meituan.net/v1/mss_test/linglong/video.mp4', 'reject-200'),
        ]
        for url, action in cases:
            self.assertEqual([a for pattern, a in rewrites if re.search(pattern, url)], [action], url)
            self.assertFalse(any(re.search(h['match'], url) for h in handlers), url)
            self.assertIn(urlsplit(url).hostname, config['http']['mitm'])
        for url in [
            'https://acs.m.taobao.com/gw/mtop.alibaba.advertisementservice.getadvExtra',
            'https://www.xiaohongshu.com/api/sns/v1/ads/resourceExtra',
            'https://issuecdn.baidupcs.com/issue/netdisk/download/file',
            'https://api.zhihu.com/articles/123',
            'https://interface9.music.163.com/eapi/song/enhance/player/url',
            'https://flowplus.meituan.net/v1/mss_test/product/video.mp4',
        ]:
            self.assertFalse(any(re.search(pattern, url) for pattern, _ in rewrites), url)

    def test_fmz_http_compatibility_keeps_narrow_hosts_and_paths(self):
        catalog = json.loads((ROOT / 'research/ad-catalog.json').read_text())
        for item in catalog['modules']:
            for rule in item['rewrite']:
                if not rule['match'].startswith('^https?://'):
                    continue
                self.assertRegex(rule['positive'].replace('https:', 'http:', 1), rule['match'])
                for url in rule['negative']:
                    self.assertNotRegex(url.replace('https:', 'http:', 1), rule['match'])

    def test_no_tls_bypass_or_wildcard_mitm(self):
        catalog = json.loads((ROOT / 'research/ad-catalog.json').read_text())
        reviewed_hosts = {h for item in catalog['modules'] for h in item['mitm']}
        reviewed_hosts.update({'app.bilibili.com', 'tiebac.baidu.com', 'edith.xiaohongshu.com', 'guide-acs.m.taobao.com', 'bootrealtime.uve.weibo.com', 'bootpreload.uve.weibo.com', 'api.weibo.cn', 'mapi.weibo.cn', 'api.weibo.com', 'mapi.weibo.com', 'rec.xiaohongshu.com', 'www.xiaohongshu.com'})
        # One separately reviewed manual self-check host, never an App wildcard.
        self.assertEqual(load('modules/diagnostics/self-check.stoverride')['http']['mitm'], ['example.com'])
        reviewed_hosts.add('example.com')
        for file in [*ROOT.rglob('*.yaml'), *ROOT.rglob('*.stoverride')]:
            data = load(file.relative_to(ROOT))
            self.assertNotIn('skip-cert-verify: true', file.read_text())
            for domain in data.get('http', {}).get('mitm', []):
                self.assertNotIn('*', domain)
                self.assertIn(domain, reviewed_hosts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emit-merged', type=Path, help='write PLACEHOLDER-only merge model outside checkout')
    args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ProjectChecks))
    if not result.wasSuccessful(): return 1
    node = subprocess.run(['node', '--test', *[str(p) for p in sorted((ROOT / 'tests').glob('ads*.test.cjs'))]], cwd=ROOT,
                          env=dict(os.environ, PYTHON=sys.executable, PYTHONUTF8='1'))
    if node.returncode: return node.returncode
    scan = subprocess.run([sys.executable, str(ROOT / 'tools/scan_secrets.py'), '--history'], cwd=ROOT)
    if scan.returncode: return scan.returncode
    if args.emit_merged:
        destination = args.emit_merged.resolve()
        if destination.is_relative_to(ROOT): raise ValueError('merged output must stay outside checkout')
        destination.write_text(yaml.safe_dump(merged(*sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'modules/ads').glob('*.stoverride')), 'examples/private-allowlist.stoverride'), allow_unicode=True, sort_keys=False))
    print('PASS: structural checks + merge/routing models + ad unit tests + secret-pattern scan.')
    print('NOT RUN: actual Stash parser/merge, iPhone connection, service unlock, real ads, account check-in, native choice persistence.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
