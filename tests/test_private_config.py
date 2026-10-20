"""Private builder regressions using public dummy nodes only."""
import copy
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from build_private_config import AUTO_POOLS, PROBE_SETTINGS, BuildError, compose, render, verify, write_private
from validate import ROOT, load


class PrivateConfigChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = load('config/stash.yaml')
        cls.source = load('examples/provider-simulated.yaml')
        extra = copy.deepcopy(cls.source['proxies'][0])
        extra['name'] = '未收录的远方线路'
        cls.source['proxies'].append(extra)
        metadata = copy.deepcopy(extra)
        metadata['name'] = '剩余流量：1024.5 GB'
        cls.source['proxies'].append(metadata)

    def test_nodes_retained_and_old_settings_removed(self):
        source = copy.deepcopy(self.source)
        source.update({'dns': {'nameserver': ['tls://dot.pub']},
                       'external-controller': '0.0.0.0:9090',
                       'rules': ['MATCH,DIRECT'], 'http': {'mitm': ['*']}})
        before = copy.deepcopy(source)
        config, report = compose(source)
        self.assertEqual(source, before)
        self.assertEqual(config['proxies'], source['proxies'][:3])
        self.assertEqual(report['metadata_entries_excluded'], 1)
        self.assertEqual(config['dns'], self.template['dns'])
        self.assertNotIn('external-controller', config)
        self.assertNotIn('proxy-providers', config)
        self.assertEqual(config.get('http'), self.template.get('http'))
        self.assertEqual(report['inline_scripts'], 0)
        self.assertEqual(report['remote_scripts'], 11)
        for provider in config['script-providers'].values():
            self.assertEqual(set(provider), {'url', 'interval'})
            self.assertTrue(provider['url'])

    def test_region_and_complement_and_neutral_defaults(self):
        config, report = compose(self.source)
        groups = {g['name']: g for g in config['proxy-groups']}
        self.assertEqual(groups['香港'], {'name': '香港', 'type': 'select', 'proxies': ['REJECT']})
        self.assertEqual(groups['美国']['proxies'], [self.source['proxies'][0]['name'], 'REJECT'])
        self.assertEqual(groups['其他地区']['proxies'], ['未收录的远方线路', 'REJECT'])
        self.assertEqual(len(groups['自动节点']['proxies']), 4)
        self.assertEqual(groups['总代理']['proxies'][0], 'REJECT')
        self.assertEqual(groups['海外AI']['proxies'][0], '美国')
        self.assertEqual(groups['Apple']['proxies'][0], 'DIRECT')
        self.assertFalse(report['subscription_auto_update'])
        self.assertFalse(report['native_stash_tested'])
        self.assertFalse(report['connectivity_tested'])
        self.assertNotIn('全部节点', groups)
        self.assertNotIn('OpenAI', groups)
        for group in groups.values():
            self.assertNotIn('filter', group)
            self.assertNotIn('use', group)
            self.assertNotIn('全部节点', group['proxies'])
            self.assertNotIn('OpenAI', group['proxies'])

    def test_all_seven_nonempty_pools_use_url_test_and_manual_stays_select(self):
        source = copy.deepcopy(self.source)
        for name in ('HKG02', '新加坡 SG 02', '台湾 TW 02'):
            node = copy.deepcopy(source['proxies'][0])
            node['name'] = name
            source['proxies'].append(node)
        config, _ = compose(source)
        groups = {g['name']: g for g in config['proxy-groups']}
        for name in AUTO_POOLS:
            with self.subTest(pool=name):
                group = groups[name]
                self.assertEqual(group['type'], 'url-test')
                self.assertGreater(len(group['proxies']), 1)
                self.assertEqual({key: group[key] for key in PROBE_SETTINGS}, PROBE_SETTINGS)
        self.assertEqual(groups['手动节点']['type'], 'select')
        self.assertEqual(groups['手动节点']['proxies'], groups['自动节点']['proxies'])
        for name in ('Netflix', 'YouTube', 'Telegram', '未匹配流量'):
            self.assertEqual(groups[name]['proxies'][0], '总代理')

    def test_empty_other_region_has_only_reject_and_no_probe_settings(self):
        source = load('examples/provider-simulated.yaml')
        config, _ = compose(source)
        group = next(g for g in config['proxy-groups'] if g['name'] == '其他地区')
        self.assertEqual(group, {'name': '其他地区', 'type': 'select', 'proxies': ['REJECT']})

    def test_empty_pools_strip_legacy_probe_settings(self):
        template = copy.deepcopy(self.template)
        for group in template['proxy-groups']:
            if group['name'] in {'香港', '其他地区'}:
                group.update({'tolerance': 50, 'lazy': True})
        config, _ = compose(load('examples/provider-simulated.yaml'), template=template)
        groups = {g['name']: g for g in config['proxy-groups']}
        for name in ('香港', '其他地区'):
            self.assertEqual(groups[name], {'name': name, 'type': 'select', 'proxies': ['REJECT']})

    def test_country_pools_cannot_fall_back_to_other_nodes_or_direct(self):
        config, _ = compose(self.source)
        # Structural boundary only: native Stash decides how a failed url-test
        # pool behaves. The export supplies neither a different country nor
        # DIRECT as an escape route; this is not a simulated connectivity test.
        for forbidden in ('DIRECT', '自动节点', self.source['proxies'][1]['name']):
            broken = copy.deepcopy(config)
            group = next(g for g in broken['proxy-groups'] if g['name'] == '美国')
            group['proxies'].insert(0, forbidden)
            with self.subTest(forbidden=forbidden), self.assertRaises(BuildError):
                verify(broken, self.template, config['proxies'])

    def test_probe_settings_and_service_defaults_are_validated(self):
        config, _ = compose(self.source)
        for name, key, value in (('自动节点', 'type', 'select'), ('美国', 'tolerance', 50),
                                 ('其他地区', 'interval', 60), ('香港', 'tolerance', 0),
                                 ('海外AI', 'proxies', ['总代理', '美国']),
                                 ('Apple', 'proxies', ['总代理', 'DIRECT'])):
            broken = copy.deepcopy(config)
            next(g for g in broken['proxy-groups'] if g['name'] == name)[key] = value
            with self.subTest(group=name, field=key), self.assertRaises(BuildError):
                verify(broken, self.template, config['proxies'])

    def test_reality_vision_and_unknown_fields_unchanged(self):
        source = copy.deepcopy(self.source)
        node = source['proxies'][1]
        node.update({'flow': 'xtls-rprx-vision', 'client-fingerprint': 'chrome',
                     'reality-opts': {'public-key': 'EXAMPLE_NOT_A_SECRET', 'short-id': 'abcd'},
                     'extra-field': {'nested': ['untouched']}})
        config, _ = compose(source)
        self.assertEqual(config['proxies'][1], node)
        self.assertEqual(yaml.safe_load(render(config)), config)

    def test_name_conflicts_aliased_without_connection_changes(self):
        for bad_name in ('总代理', 'REJECT', '美国', '自动节点', '海外AI'):
            source = copy.deepcopy(self.source)
            source['proxies'][0]['name'] = bad_name
            config, report = compose(source)
            actual = config['proxies'][0]
            self.assertEqual(actual['name'], '节点 · ' + bad_name)
            self.assertEqual({k: v for k, v in actual.items() if k != 'name'},
                             {k: v for k, v in source['proxies'][0].items() if k != 'name'})
            self.assertEqual(report['display_names_aliased_for_conflict'], 1)
        source = copy.deepcopy(self.source)
        source['proxies'][0]['name'] = self.source['proxies'][1]['name']
        with self.assertRaises(BuildError):
            compose(source)

    def test_bad_nodes_fail_without_values(self):
        for update in ({'skip-cert-verify': True}, {'dialer-proxy': 'removed-source-group'},
                       {'underlying-proxy': 'removed-source-group'}, {'type': 'unreviewed'}, {'port': 0}):
            source = copy.deepcopy(self.source)
            source['proxies'][0].update(update)
            with self.assertRaises(BuildError):
                compose(source)

    def test_broken_reference_and_cycle_detected(self):
        config, _ = compose(self.source)
        broken = copy.deepcopy(config)
        broken['proxy-groups'][0]['proxies'].append('undefined')
        with self.assertRaises(BuildError):
            verify(broken, self.template, config['proxies'])
        broken = copy.deepcopy(config)
        next(g for g in broken['proxy-groups'] if g['name'] == '自动节点')['proxies'].append('总代理')
        with self.assertRaises(BuildError):
            verify(broken, self.template, config['proxies'])

    def test_private_output_permissions_and_repository_guard(self):
        with self.assertRaises(BuildError):
            write_private(ROOT / 'dist/should-not-write.yaml', 'no private content')
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'config.yaml'
            output.write_text('old content')
            os.chmod(output, 0o644)
            write_private(output, 'new content')
            self.assertEqual(output.read_text(), 'new content')
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            (Path(directory) / '.git').mkdir()
            (Path(directory) / '.git/HEAD').write_text('ref: refs/heads/main\n')
            with self.assertRaises(BuildError):
                write_private(output, 'blocked')


if __name__ == '__main__':
    unittest.main()
