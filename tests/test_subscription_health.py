"""Fault injection for monitoring, domestic/TikTok conflict and comment exclusions."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import yaml
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import verify_subscriptions as h
import app_route_audit as a
import validate as v


class HealthChecks(unittest.TestCase):
    def test_invalid_empty_duplicate_and_unreviewed_formats_rejected(self):
        for data in [b'payload: []',b'<html>failure</html>',b'payload: [1]',
                     b'payload: []\npayload: []',b'payload: ["MATCH,DIRECT"]']:
            for behavior in ('domain','classical'):
                with self.assertRaises((ValueError,h.m.MaintenanceError)):
                    h.parsed_rules(data,behavior)

    def test_failure_and_large_removal_reported_without_exception_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);rules=['DOMAIN,api'+str(n)+'.example.invalid' for n in range(20)]
            (root/'snapshot.yaml').write_text(yaml.safe_dump({'payload':rules}))
            part=dict(name='fixture',url='https://raw.githubusercontent.com/fixture/rules/main/a.yaml',behavior='classical',snapshot='snapshot.yaml')
            good=h.check(part,root,lambda _:yaml.safe_dump({'payload':rules}).encode())
            self.assertEqual(good['health'],'ok');self.assertEqual(good['delta']['added'],0)
            reduced=h.check(part,root,lambda _:yaml.safe_dump({'payload':rules[:2]}).encode())
            self.assertEqual(reduced['health'],'review_required')
            def fail(_):raise OSError('DO-NOT-ECHO-response-body')
            error=h.check(part,root,fail)
            self.assertEqual(error['health'],'error');self.assertNotIn('cached_file',error)
            self.assertNotIn('DO-NOT-ECHO',json.dumps(error))

    def test_complete_app_route_and_comment_samples(self):
        report=a.audit_profiles()
        self.assertTrue(report['ok'],[x for p in report['profiles'] for x in p['results'] if not x['ok']])

    def test_guard_detects_domestic_capture_and_overbroad_comment_rewrite(self):
        config=v.load('config/stash.yaml');sets=v.provider_rules(config)
        cases=json.loads((ROOT/'tests/fixtures/app-routes.json').read_text(encoding='utf-8'))['cases']
        broken=copy.deepcopy(config)
        broken['rules'].insert(0,'RULE-SET,TikTok,TikTok')
        failures=[x for x in a.audit(broken,sets,cases) if not x['ok']]
        self.assertTrue(any(x['host']=='aweme.snssdk.com' for x in failures))
        broken=copy.deepcopy(config)
        broken['http']['url-rewrite'].append(r'^https://edith\.xiaohongshu\.com/ - reject-dict')
        self.assertTrue(any(x['http_handlers'] for x in a.audit(broken,sets,cases)))

    def test_every_published_direct_source_is_monitored(self):
        monitored={x['url'] for x in h.direct_parts()}
        for filename in ['config/stash.yaml','config/clash-verge-auto.yaml']:
            config=v.load(filename)
            direct={p['url'] for p in config['rule-providers'].values() if 'Panzm6111/' not in p['url']}
            self.assertTrue(direct<=monitored)

    def test_game_direct_routing_cannot_inherit_domestic_group_proxy(self):
        for filename,prefix in [('config/stash.yaml',''),('config/clash-verge-auto.yaml','Jimmy · ')]:
            config=v.load(filename)
            domestic=next(g for g in config['proxy-groups'] if g['name']==prefix+'国内直连')
            domestic['proxies']=[prefix+'ai','DIRECT']
            for host in ['pvp.qq.com','sgame.qq.com','dlied1.qq.com','msdk.qq.com','www.yuanshen.com']:
                self.assertEqual(v.route(config,host),'DIRECT',host)
            # Synthetic IP/country inputs, not claimed real game server addresses.
            for address in ['203.0.113.5','2001:db8::5']:
                self.assertEqual(v.route(config,address=address,country='CN'),'DIRECT')
                self.assertEqual(v.route(config,address=address,country='JP'),prefix+'未匹配流量')
            # Domain-specific foreign routes retain priority even with a CN IP.
            for host,policy in [('www.steampowered.com','总代理'),('api.openai.com','海外AI'),('www.tiktok.com','TikTok')]:
                self.assertEqual(v.route(config,host,'203.0.113.5','CN'),prefix+policy)


if __name__=='__main__':unittest.main()
