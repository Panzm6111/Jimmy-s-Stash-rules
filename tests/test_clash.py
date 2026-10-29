"""Synthetic subscription conversion regressions; no personal data or network."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_clash import render,global_merge,remote_profile
from prepare_clash_bootstrap import prepare

class ClashChecks(unittest.TestCase):
    def test_private_bootstrap_preserves_settings_and_removes_null_node_fields(self):
        node={'name':'US fixture','type':'vless','flow':None,'port':443,'tls':False}
        private={'dns':{'enable':True},'proxy-providers':{'机场':{'url':'https://airport.example/fixture'}}}
        result=prepare({'proxies':[node]},private)
        self.assertEqual(result['dns'],private['dns'])
        provider=result['proxy-providers']['机场']
        self.assertEqual(provider['proxy'],'Jimmy · 手动节点')
        self.assertNotIn('flow',provider['payload'][0])
        self.assertFalse(provider['payload'][0]['tls'])
        self.assertNotIn('payload',private['proxy-providers']['机场'])
        self.assertIsNone(node['flow'])
        with self.assertRaises(ValueError):prepare({'proxies':[]},private)
        with self.assertRaises(ValueError):prepare({'proxies':[node]},{})

    def transform(self, source):
        runner = 'const fs=require("fs"),vm=require("vm");const c=vm.createContext({});vm.runInContext(fs.readFileSync("config/clash-verge.js","utf8"),c);process.stdout.write(JSON.stringify(c.main(JSON.parse(fs.readFileSync(0,"utf8")))));'
        result = subprocess.run(['node', '-e', runner], input=json.dumps(source), text=True,
                                encoding='utf-8', capture_output=True, cwd=ROOT)
        return result

    def test_generated_and_all_routes_preserved(self):
        for name, body in render().items():
            self.assertEqual((ROOT/name).read_text(encoding='utf-8'), body)
        stash = yaml.safe_load((ROOT/'config/stash.yaml').read_text(encoding='utf-8'))
        clash = yaml.safe_load((ROOT/'config/clash-verge.yaml').read_text(encoding='utf-8'))
        self.assertEqual(clash['rules'], stash['rules'])
        self.assertEqual(clash['proxy-groups'], stash['proxy-groups'])
        self.assertNotIn('http', clash)
        self.assertNotIn('script-providers', clash)
        self.assertEqual(clash['rule-providers']['基础广告']['url'], stash['rule-providers']['基础广告']['url'])
        self.assertEqual(len(clash['rule-providers']),19)
        self.assertEqual(len({p['path'] for p in clash['rule-providers'].values()}),19)
        self.assertTrue(all(p['type']=='http' and p['interval']==86400 for p in clash['rule-providers'].values()))
        self.assertTrue(all(r.split(',')[0] in {'RULE-SET','GEOIP','MATCH'} for r in clash['rules']))

    def test_nodes_protocol_fields_and_providers_preserved(self):
        source = {'proxies':[{'name':'US synthetic','type':'socks5','server':'127.0.0.1','port':9}],
                  'proxy-providers':{'original':{'type':'inline','payload':[{'name':'JP synthetic','type':'socks5','server':'127.0.0.1','port':10}]}},
                  'rules':['MATCH,DIRECT']}
        result = self.transform(source)
        self.assertEqual(result.returncode, 0, result.stderr)
        out = json.loads(result.stdout)
        self.assertEqual(out['proxies'], source['proxies'])
        self.assertEqual(out['proxy-providers']['original'], source['proxy-providers']['original'])
        self.assertEqual(out['proxy-providers']['Jimmy-inline-nodes']['payload'], source['proxies'])
        groups = {g['name']:g for g in out['proxy-groups']}
        self.assertIn('日本+美国', groups['海外AI']['proxies'])
        self.assertEqual(groups['日本+美国']['use'], ['original','Jimmy-inline-nodes'])
        self.assertEqual(out['rules'][-1], 'MATCH,未匹配流量')

    def test_no_nodes_and_conflicts_fail_explicitly(self):
        self.assertNotEqual(self.transform({}).returncode, 0)
        self.assertNotEqual(self.transform({'proxies':[{'name':'美国'}]}).returncode, 0)

    def test_global_merge_preserves_airport_and_application_settings(self):
        overlay=yaml.safe_load(render()['config/clash-verge-merge.yaml'])
        self.assertEqual(set(overlay),{'rules','proxy-groups','rule-providers'})
        airport={'proxies':[{'name':'台湾','type':'socks5','server':'127.0.0.1','port':9}],
                 'proxy-providers':{'original':{'type':'inline','payload':[]}},
                 'dns':{'enable':False},'tun':{'enable':False},'mixed-port':12345,
                 'rules':['MATCH,DIRECT'],'proxy-groups':[{'name':'airport-original'}]}
        merged=copy.deepcopy(airport)
        for key,value in overlay.items():
            if isinstance(value,dict):merged.setdefault(key,{}).update(value)
            else:merged[key]=copy.deepcopy(value)
        for key in ['proxies','proxy-providers','dns','tun','mixed-port']:
            self.assertEqual(merged[key],airport[key])
        names={g['name'] for g in merged['proxy-groups']}
        self.assertEqual(len(names),20)
        self.assertTrue(all(name.startswith('Jimmy · ') for name in names))
        self.assertNotIn('台湾',names)

    def test_merge_routes_and_provider_contents_follow_same_source(self):
        source=yaml.safe_load((ROOT/'config/clash-verge.yaml').read_text(encoding='utf-8'))
        before=copy.deepcopy(source);overlay=global_merge(source)
        self.assertEqual(source,before)
        reverse={'Jimmy · '+g['name']:g['name'] for g in source['proxy-groups']}
        restored=[]
        for rule in overlay['rules']:
            parts=rule.split(',');index=1 if parts[0]=='MATCH' else 2
            parts[index]=reverse.get(parts[index],parts[index]);restored.append(','.join(parts))
        self.assertEqual(restored,source['rules'])
        self.assertEqual(set(overlay['rule-providers']),set(source['rule-providers']))
        for name,provider in overlay['rule-providers'].items():
            self.assertEqual(provider['url'],source['rule-providers'][name]['url'])
            self.assertEqual(provider['interval'],86400)
            self.assertEqual(provider['proxy'],'Jimmy · 自动节点')
        for group in overlay['proxy-groups']:
            self.assertNotIn('use',group)
            if group.get('include-all'):self.assertEqual(group['empty-fallback'],'REJECT')
        groups={g['name']:g for g in overlay['proxy-groups']}
        self.assertEqual(groups['Jimmy · 总代理']['proxies'][0],'Jimmy · 自动节点')
        self.assertIn('Jimmy · 日本+美国',groups['Jimmy · 海外AI']['proxies'])

    def test_merge_refuses_unknown_route_syntax(self):
        source=yaml.safe_load((ROOT/'config/clash-verge.yaml').read_text(encoding='utf-8'))
        source['rules'].append('AND,unknown,REJECT')
        with self.assertRaises(ValueError):global_merge(source)

    def test_full_remote_profile_has_all_structure_and_basic_maintained_ads(self):
        source=yaml.safe_load(render()['config/clash-verge.yaml'])
        full=yaml.safe_load(render()['config/clash-verge-auto.yaml'])
        overlay=global_merge(source)
        self.assertEqual(full['proxy-groups'],overlay['proxy-groups'])
        self.assertEqual(len(full['proxy-groups']),20)
        self.assertEqual(len(full['rule-providers']),17)
        removed={'广告路径例外','App广告域名'}
        expected=[r for r in overlay['rules'] if not (r.startswith('RULE-SET,') and r.split(',')[1] in removed)]
        self.assertEqual(full['rules'],expected)
        self.assertNotIn('http',full);self.assertNotIn('script-providers',full)
        self.assertTrue(full['rule-providers']['基础广告']['url'].endswith('/rules/vendor/clash-ads-community.yaml'))
        self.assertEqual(full['proxy-providers']['机场']['proxy'],'DIRECT')
        self.assertEqual(full['proxy-providers']['机场']['header'],{'User-Agent':['clash-verge/v2.5.8']})
        self.assertEqual(full['proxy-providers']['机场']['interval'],86400)
        self.assertEqual(full['proxy-providers']['机场']['url'],'https://example.invalid/REPLACE_ON_DEVICE')

    def test_new_remote_structure_is_not_frozen_in_local_private_merge(self):
        source=yaml.safe_load(render()['config/clash-verge.yaml'])
        private={'proxy-providers':{'机场':{'url':'https://airport.example.invalid/private'}},'dns':{'enable':False}}
        # Simulate a later published structural revision, including a new group/provider/order.
        source['proxy-groups'].append({'name':'新增测试组','type':'select','proxies':['美国']})
        source['rule-providers']['新增测试集']=copy.deepcopy(source['rule-providers']['海外AI'])
        source['rules'].insert(0,'RULE-SET,新增测试集,新增测试组')
        updated=remote_profile(source)
        updated['proxy-providers']['机场'].update(private['proxy-providers']['机场'])
        updated['dns'].update(private['dns'])
        self.assertEqual(updated['rules'][0],'RULE-SET,新增测试集,Jimmy · 新增测试组')
        self.assertIn('Jimmy · 新增测试组',{g['name'] for g in updated['proxy-groups']})
        self.assertEqual(updated['proxy-providers']['机场']['url'],private['proxy-providers']['机场']['url'])
        self.assertFalse(updated['dns']['enable'])

    def test_remote_profile_keeps_social_functional_routes_ahead_of_basic_ads(self):
        from validate import route
        config=yaml.safe_load(render()['config/clash-verge-auto.yaml'])
        for host in ['ttcdn-us.com','ttlivecdn.com','ttoverseaus.net','ttwstatic.com',
                     'roovza-launches.appsflyersdk.com','roovza.inapps.appsflyersdk.com',
                     'roovza.launches.appsflyersdk.com','roovza.skadsdk.appsflyersdk.com',
                     'www.instagram.com','x.com','www.facebook.com','discord.com','web.whatsapp.com']:
            self.assertEqual(route(config,host,country='CN'),'Jimmy · TikTok',host)
        self.assertEqual(route(config,'analytics.tiktok.com'),'Jimmy · 广告拦截')
        self.assertEqual(route(config,'github.com'),'Jimmy · 总代理')

if __name__ == '__main__':
    unittest.main()
