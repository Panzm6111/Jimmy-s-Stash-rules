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
from build_clash import render

class ClashChecks(unittest.TestCase):
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
        self.assertEqual(len(clash['rule-providers']),14)
        self.assertEqual(len({p['path'] for p in clash['rule-providers'].values()}),14)
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

if __name__ == '__main__':
    unittest.main()
