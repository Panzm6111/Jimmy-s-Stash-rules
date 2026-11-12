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
    def test_stash_ai_dns_has_no_domestic_race_and_pins_resolver_transport(self):
        from stash_ai_guard import AI_SUFFIXES, AI_RESOLVERS, BOOTSTRAP
        config=v.load('config/stash.yaml')
        dns=config['dns']
        self.assertTrue(dns['follow-rule'])
        self.assertEqual(dns['default-nameserver'],list(BOOTSTRAP))
        self.assertEqual(dns['proxy-server-nameserver'],list(BOOTSTRAP))
        self.assertNotIn('fallback',dns)
        for host in AI_SUFFIXES:
            self.assertEqual(dns['nameserver-policy']['+.'+host],list(AI_RESOLVERS))
        self.assertEqual(dns['nameserver-policy']['rule-set:海外AI,海外AI补充'],list(AI_RESOLVERS))
        # Deliberately inject CN GeoIP and competing rejecting rule providers.
        # Resolver transport must still use the exact AI selector, fail closed
        # through its existing REJECT sentinel, and not inherit MATCH/ads.
        poisoned={name:['IP-CIDR,0.0.0.0/0'] for name in config['rule-providers']}
        with patch.object(v,'provider_rules',return_value=poisoned):
            for address in ['1.1.1.1','8.8.8.8']:
                self.assertEqual(v.route(config,address=address,country='CN'),'海外AI')
        for host in ['dns.alidns.com','doh.pub']:
            self.assertEqual(v.route(config,host,country='ZZ'),'DIRECT')
        groups={g['name']:g for g in config['proxy-groups']}
        for name in ['ai','美国','日本','台湾']:
            self.assertEqual(groups[name]['proxies'],['REJECT'])
        self.assertFalse(config['ipv6'])

    def test_both_published_profiles_use_the_same_pool_tolerances(self):
        expected = dict.fromkeys(('自动节点','美国','日本','香港','台湾','新加坡','其他地区'), 50)
        expected.update({'ai':250, 'AI最速':100, '最速节点':50})
        for path, prefix in [('config/stash.yaml',''), ('config/clash-verge-auto.yaml','Jimmy · ')]:
            with self.subTest(path=path):
                pools = {g['name']: g['tolerance'] for g in v.load(path)['proxy-groups'] if g['type']=='url-test'}
                self.assertEqual(pools, {prefix + name: ms for name, ms in expected.items()})

    def test_stash_chatgpt_core_survives_unloaded_or_rejecting_remote_sets(self):
        from stash_ai_guard import AI_SUFFIXES
        from app_route_audit import decision
        config=v.load('config/stash.yaml')
        for failed in [[],['DOMAIN-SUFFIX,chatgpt.com','DOMAIN-SUFFIX,openai.com']]:
            payload={name:failed for name in config['rule-providers']}
            with patch.object(v,'provider_rules',return_value=payload):
                # Keep the deliberate system/LAN exceptions, not a broad bypass.
                payload['系统直连例外']=[]
                for host in AI_SUFFIXES:
                    for prefix in ['', 'auth.', 'ws.']:
                        self.assertEqual(v.route(config,prefix+host,country='CN'),'海外AI')
                        self.assertEqual(decision(config,payload,prefix+host)[0],'海外AI')
                self.assertNotEqual(v.route(config,'chatgpt.com.attacker.invalid',country='CN'),'海外AI')
        self.assertEqual(v.route(config,'chatgpt.com','192.168.1.1'),'DIRECT')

    def test_stash_service_override_is_private_and_reproducible(self):
        from service_health import MANAGED, render_private_override
        src = (ROOT/'examples/stash-service-health.stoverride').read_text(encoding='utf-8')
        self.assertEqual(src, render_private_override(ROOT))
        config = yaml.safe_load(src)
        self.assertNotIn('cron', v.load('config/stash.yaml'))
        self.assertNotIn('cron', v.load('config/clash-verge-auto.yaml'))
        self.assertEqual(config['arguments-version'], 1)
        self.assertTrue(config['arguments']['secret']['required'])
        self.assertNotIn('default', config['arguments']['secret'])
        cron, = config['cron']['script']
        self.assertEqual(cron['cron'], '* * * * *')
        self.assertEqual(cron['argument'], '{"port":${args.port|json},"secret":${args.secret|json}}')
        params = config['script-providers'][cron['name']]
        self.assertEqual(set(params), {'payload'})
        self.assertEqual(params['payload'], (ROOT/'scripts/service-health.js').read_text(encoding='utf-8'))
        groups = {g['name']:g for g in v.load('config/stash.yaml')['proxy-groups']}
        import re
        for selector, pool in MANAGED.items():
            for candidate in ['新加坡 A','荷兰','英国 B','日本 A','美国 D','HKG A','DIRECT','无关']:
                self.assertEqual(bool(re.search(groups[selector]['filter'],candidate)),
                                 bool(re.search(groups[pool]['filter'],candidate)))
            self.assertRegex(pool, groups[selector]['filter'])
            self.assertNotRegex('REJECT', groups[selector]['filter'])

    def test_both_service_routes_retain_offline_coverage_and_ad_priority(self):
        from stash_ai_guard import AI_SUFFIXES, TIKTOK_ENTRY_HOSTS
        from app_route_audit import decision
        for config_name, prefix in [('stash', ''), ('clash-verge-auto', 'Jimmy · ')]:
            cfg = v.load('config/' + config_name + '.yaml')
            data = {k: [] for k in cfg['rule-providers']}
            for key in AI_SUFFIXES:
                self.assertEqual(decision(cfg, data, 'auth.' + key)[0], prefix + '海外AI')
            for host in TIKTOK_ENTRY_HOSTS:
                self.assertEqual(decision(cfg, data, host)[0], prefix + 'TikTok')
            self.assertNotEqual(decision(cfg, data, 'www.tiktok.com.example.invalid')[0], prefix + 'TikTok')
            data['TikTok广告'] = ['DOMAIN,www.tiktok.com']
            self.assertEqual(decision(cfg, data, 'www.tiktok.com')[0], prefix + '广告拦截')

    def test_stash_guard_isolated_from_clash_and_private_provider(self):
        from stash_ai_guard import apply, for_clash
        from build_subscription import remote_integrated
        source=remote_integrated();before=copy.deepcopy(source)
        restored=for_clash(source,v.merged())
        # Reapplying to the pre-guard source neither mutates nor loses secrets
        # in a synthetic device map; no actual credentials are accessed.
        fixture=copy.deepcopy(restored)
        fixture['proxy-providers']['机场']['url']='https://device.example.invalid/private'
        untouched=copy.deepcopy(fixture)
        guarded=apply(fixture)
        self.assertEqual(fixture,untouched)
        self.assertEqual(guarded['proxy-providers'],fixture['proxy-providers'])
        self.assertEqual(source,before)
        clash=v.load('config/clash-verge-auto.yaml')
        self.assertNotIn('follow-rule',clash['dns'])
        self.assertNotIn('nameserver-policy',clash['dns'])
        self.assertEqual(restored['dns'],v.merged()['dns'])

    def test_policy_order_groups_and_http_unchanged_by_splitting_sets(self):
        from build_subscription import remote_integrated
        # Compare source semantics before/after provider splitting; no old Git commit required.
        with patch.object(p,'apply',side_effect=lambda config:config):old=remote_integrated()
        new=v.load('config/stash.yaml');reverse={part['name']:name for name,parts in p.plan()['providers'].items() for part in parts}
        restored=[]
        for rule in new['rules']:
            f=rule.split(',')
            if f[0]=='RULE-SET':f[1]=reverse.get(f[1],f[1])
            value=','.join(f)
            if not restored or restored[-1]!=value:restored.append(value)
        self.assertEqual(restored,old['rules'])
        for key in ['proxy-groups','proxy-providers','http','script-providers']:self.assertEqual(new[key],old[key],key)
        # DNS rule-set references expand with the same provider split.
        old_dns=copy.deepcopy(old['dns'])
        policy=old_dns['nameserver-policy']
        servers=policy.pop('rule-set:海外AI')
        policy['rule-set:海外AI,海外AI补充']=servers
        self.assertEqual(new['dns'],old_dns)
        for name,parts in p.plan()['providers'].items():
            oldset=set(v.provider_rules(old)[name]);newset=set()
            for part in parts:newset.update(v.provider_rules(new)[part['name']])
            if name=='国内服务':
                additions=set(v.load('rules/vendor/china-geolocation.yaml')['payload'])|set(v.load('rules/vendor/qcloud.yaml')['payload'])
                self.assertEqual(oldset|additions,newset,name)
            else:self.assertEqual(oldset,newset,name)

    def test_runtime_upstreams_are_mutable_but_offline_reference_is_explicit(self):
        config=v.load('config/clash-verge-auto.yaml')
        direct=[x for x in config['rule-providers'].values() if 'Panzm6111/' not in x['url']]
        self.assertEqual(len(direct),25)
        self.assertEqual(len(config['rule-providers']),33)
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
