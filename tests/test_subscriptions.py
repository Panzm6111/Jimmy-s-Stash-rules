"""Public upstream migration invariants; no private subscriptions or live network."""
import copy,json,subprocess,sys,tempfile,unittest,hashlib
from pathlib import Path
from unittest.mock import patch
import yaml
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import provider_sources as p
import cloud_update as cloud
import validate as v

class Subscriptions(unittest.TestCase):
    def test_policy_order_groups_and_http_unchanged_by_splitting_sets(self):
        old=yaml.safe_load(subprocess.check_output(['git','-C',str(ROOT),'show','a9d5630:config/stash.yaml']))
        new=v.load('config/stash.yaml');reverse={part['name']:name for name,parts in p.plan()['providers'].items() for part in parts}
        restored=[]
        for rule in new['rules']:
            f=rule.split(',')
            if f[0]=='RULE-SET':f[1]=reverse.get(f[1],f[1])
            value=','.join(f)
            if not restored or restored[-1]!=value:restored.append(value)
        self.assertEqual(restored,old['rules'])
        for key in ['proxy-groups','proxy-providers','dns','http','script-providers']:self.assertEqual(new[key],old[key],key)
        for name,parts in p.plan()['providers'].items():
            oldset=set(v.provider_rules(old)[name]);newset=set()
            for part in parts:newset.update(v.provider_rules(new)[part['name']])
            self.assertEqual(oldset,newset,name)

    def test_runtime_upstreams_are_mutable_but_offline_reference_is_explicit(self):
        config=v.load('config/clash-verge-auto.yaml')
        direct=[x for x in config['rule-providers'].values() if 'Panzm6111/' not in x['url']]
        self.assertEqual(len(direct),17)
        self.assertEqual(len(config['rule-providers']),25)
        for part in direct:
            self.assertIn(part['behavior'],{'domain','classical'})
            self.assertTrue((ROOT/p.reference_path(part['url'])).is_file())
        with self.assertRaises(ValueError):p.reference_path('https://unreviewed.example/rules.yaml')

    def test_native_fixture_conversion_does_not_widen_exact_domains(self):
        self.assertEqual(p.fixture_payload(['DOMAIN,one.invalid','DOMAIN-SUFFIX,two.invalid'],'domain'),['one.invalid','+.two.invalid'])
        with self.assertRaises(ValueError):p.fixture_payload(['IP-CIDR,1.1.1.0/24'],'domain')

    def test_cloud_converter_filters_only_reviewed_unsupported_kinds(self):
        rules,omitted=cloud.convert(b'payload: ["DOMAIN,one.invalid", "PROCESS-NAME,synthetic", "IP-ASN,123"]','classical_yaml')
        self.assertEqual(rules,['DOMAIN,one.invalid']);self.assertEqual(len(omitted),2)
        for data in [b'payload: []',b'payload: ["MATCH,DIRECT"]',b'payload: ["DOMAIN,one.invalid,DIRECT"]',b'payload: []\npayload: []']:
            with self.assertRaises((ValueError,cloud.m.MaintenanceError)):cloud.convert(data,'classical_yaml')

    def test_cloud_fetch_failure_cannot_write_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'plan.json').write_text('{}')
            with patch.object(cloud.m,'ensure_clean'),patch.object(cloud,'git',return_value='a'*40),patch.object(cloud,'plan',return_value={'cloud_sources':[{'manifest':'missing','output':'test','format':'classical_yaml'}]}):
                with self.assertRaises(FileNotFoundError):cloud.refresh(root)
            self.assertEqual(sorted(x.name for x in root.iterdir()),['plan.json'])

    def test_cloud_real_git_publication_and_no_change_second_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'repo';root.mkdir();remote=Path(tmp)/'remote.git'
            def cmd(*args):return subprocess.check_output(['git',*map(str,args)],stderr=subprocess.PIPE).decode().strip()
            cmd('init','--bare',remote);cmd('-C',root,'init','-b','main');cmd('-C',root,'config','user.name','Fixture');cmd('-C',root,'config','user.email','fixture@example.invalid');cmd('-C',root,'remote','add','origin',remote)
            cmd('-C',root,'config','core.autocrlf','false')
            for directory in ['tools','research','rules']:(root/directory).mkdir()
            (root/'tools/build_ads.py').write_text('# synthetic build: outputs already generated\n')
            (root/'LICENSE').write_text('fixture-license')
            (root/'PROGRESS.md').write_text('Fixture current\n<!-- sop-current-end -->\nHistory\n')
            (root/'research/last-cloud-update.json').write_text('{}')
            original=['DOMAIN,host'+str(i)+'.invalid' for i in range(10)]
            (root/'rules/fixture.yaml').write_text(yaml.safe_dump({'payload':original}))
            manifest={'upstream':{'license_file':'LICENSE'},'resources':[{'output':'rules/fixture.yaml','source_path':'rule/fixture.yaml'}]}
            (root/'research/sources.lock.json').write_text(json.dumps(manifest))
            (root/'research/community-sources.json').write_text(json.dumps({'resources':[],'aggregates':[]}))
            (root/'research/subscription-plan.json').write_text(json.dumps({'cloud_sources':[{'manifest':'research/sources.lock.json','output':'rules/fixture.yaml','format':'classical_yaml'}]}))
            (root/'.gitignore').write_text('.local/\n')
            files=['tools/build_ads.py','LICENSE','PROGRESS.md','research/last-cloud-update.json','rules/fixture.yaml','research/sources.lock.json','research/community-sources.json','research/subscription-plan.json','.gitignore']
            cmd('-C',root,'add','--',*files);cmd('-C',root,'commit','-m','baseline');cmd('-C',root,'push','origin','main')
            def fetch(url):return b'fixture-license' if url.endswith('/LICENSE') else yaml.safe_dump({'payload':original+['DOMAIN,new.invalid']}).encode()
            state=cloud.refresh(root,fetcher=fetch,resolver=lambda *_:'a'*40)
            self.assertEqual(state['status'],'updated')
            real_git=cloud.git
            def publication_git(path,*args):
                # actions/checkout uses the canonical remote without a .git suffix.
                if args==('remote','get-url','origin'):return 'https://github.com/Panzm6111/Jimmy-s-Stash-rules'
                return real_git(path,*args)
            with patch.object(cloud,'git',side_effect=publication_git):cloud.publish(root)
            self.assertEqual(cmd('-C',root,'rev-parse','HEAD'),cmd('--git-dir',remote,'rev-parse','refs/heads/main'))
            head=cmd('-C',root,'rev-parse','HEAD');self.assertEqual(cloud.refresh(root,fetcher=fetch,resolver=lambda *_:'a'*40)['status'],'no_changes');cloud.publish(root)
            self.assertEqual(cmd('-C',root,'rev-parse','HEAD'),head)

if __name__=='__main__':unittest.main()
