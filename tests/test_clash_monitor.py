"""Meaningful replay checks: attribution, uncertainty, privacy and missing intervals."""
import csv
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from clash_monitor import Recorder, Store, classify_switch, node_health, parse_log, resolve, transition_state
from clash_monitor_report import render


class MonitorChecks(unittest.TestCase):
    def setUp(self):
        self.groups={'AI':{'type':'Selector','now':'pool'},
                     'pool':{'type':'URLTest','now':'new','all':['old','new'],
                             'testUrl':'https://probe.invalid/204','monitor_tolerance':50}}
        self.before={**self.groups,'pool':{**self.groups['pool'],'now':'old'}}
    def node(self,delay,alive=True):
        return {'alive':True,'extra':{'https://probe.invalid/204':{'alive':alive,
            'history':[{'time':'2026-11-08T10:00:00+08:00','delay':delay}]}}}
    def classify(self,old_node,new_node,**kwargs):
        return classify_switch(['AI','pool','old'],['AI','pool','new'],self.before,self.groups,
            {},{'old':old_node,'new':new_node},kwargs.get('errors',False),kwargs.get('context',False))
    def test_nested_automatic_switch_is_not_mislabeled_manual(self):
        result=self.classify(self.node(300),self.node(60))
        self.assertEqual(result['reason'],'latency_advantage')
        self.assertEqual(result['certainty'],'inferred')
    def test_unhealthy_specific_url_wins_over_global_alive(self):
        self.assertEqual(self.classify(self.node(0,False),self.node(60))['reason'],'health_failure')
    def test_small_delay_difference_does_not_invent_a_cause(self):
        self.assertEqual(self.classify(self.node(90),self.node(70))['reason'],'unknown')
    def test_context_change_prevents_node_blame(self):
        self.assertEqual(self.classify(self.node(0,False),self.node(60),context=True)['reason'],'context_changed')
    def test_explicit_selector_change_cannot_identify_the_actor(self):
        groups={**self.groups,'AI':{'type':'Selector','now':'new'}}
        r=classify_switch(['AI','pool','old'],['AI','new'],self.before,groups,{}, {},False,False)
        self.assertEqual(r['reason'],'selection_changed')
        self.assertIn('无法区分',r['detail'])
    def test_node_removed_is_observed(self):
        self.groups['pool']['all']=['new']
        self.assertEqual(self.classify(self.node(90),self.node(70))['reason'],'node_removed')
    def test_selected_cycles_are_bounded(self):
        self.assertEqual(resolve({'a':{'now':'b'},'b':{'now':'a'}},'a'),['a','b'])
    def test_transition_evidence_saves_order_pin_and_probe_times_without_unused_node_names(self):
        self.groups['pool']['all']=['old','unused-private-node','new']
        self.groups['pool']['fixed']=''
        self.before['pool']['all']=['old','unused-private-node','new']
        self.before['pool']['fixed']='old'
        state=transition_state(['AI','pool','old'],['AI','pool','new'],self.before,self.groups,
            {'old':self.node(200)}, {'old':self.node(90),'new':self.node(70)})
        pool=next(g for g in state['group_states'] if g['group']=='pool')
        self.assertEqual(pool['before']['fixed'],'old');self.assertEqual(pool['after']['fixed'],'')
        self.assertEqual(pool['after']['old_node_index'],0);self.assertEqual(pool['after']['new_node_index'],2)
        self.assertEqual(state['old_health_before']['delay_ms'],200)
        self.assertEqual(state['old_health_after']['delay_ms'],90)
        self.assertEqual(state['new_health_after']['delay_ms'],70)
        self.assertIsNotNone(state['old_health_after']['probe_at'])
        self.assertNotIn('unused-private-node',json.dumps(state))
    def test_success_log_omits_host_source_and_process(self):
        msg='[TCP] 192.168.1.5:1234 --> chatgpt.com:443 match RuleSet(private) using AI[[Vless] 日本]'
        result=parse_log({'payload':msg},self.groups)
        self.assertEqual(result['node'],'[Vless] 日本');self.assertEqual(result['scope'],'AI')
        serialized=json.dumps(result)
        for secret in ['192.168','chatgpt.com','private']:self.assertNotIn(secret,serialized)
    def test_warning_is_only_selection_attributed_not_a_confirmed_node_failure(self):
        msg='[TCP] dial AI (match RuleSet/private) 192.168.1.5:33 --> chatgpt.com:443 error: dial tcp 1.2.3.4:443: i/o timeout'
        r=parse_log({'payload':msg},self.groups)
        self.assertEqual(r['category'],'timeout');self.assertEqual(r['node'],'new')
        self.assertIn('not_confirmed',r['attribution']);self.assertNotIn('1.2.3.4',json.dumps(r))
    def test_direct_and_subscription_traffic_excluded(self):
        for chain in ['DIRECT','Jimmy · 订阅更新[new]']:
            self.assertIsNone(parse_log({'payload':'[TCP] a --> x:443 using '+chain},self.groups))
    def test_intervals_split_at_hour_boundary_without_counting_missing_time(self):
        with tempfile.TemporaryDirectory() as directory:
            store=Store(directory)
            store.interval(3598,3603,node='n',scope='AI',context='c',active_s=True)
            store.coverage(3598,3603,True);store.close()
            db=sqlite3.connect(Path(directory)/'monitor.sqlite')
            self.assertEqual(db.execute('SELECT minute,active_s FROM minutes ORDER BY minute').fetchall(),[(3540,2.0),(3600,3.0)])
            self.assertEqual(db.execute('SELECT sum(api_s) FROM coverage').fetchone()[0],5)
            db.close()
    def test_offline_report_escapes_untrusted_node_names_and_has_no_remote_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);(folder/'session.json').write_text(json.dumps({'start':1,'end':100}),encoding='utf-8')
            store=Store(folder);store.metric(10,'</script><script>alert(1)</script>','AI','c',opens=1);store.close();render(folder)
            page=(folder/'report.html').read_text(encoding='utf-8')
            self.assertNotIn('</script><script>alert(1)',page)
            self.assertIn('\\u003c/script>',page);self.assertNotIn('<script src=',page);self.assertNotIn('fetch(',page)
    def test_paused_report_uses_actual_stop_and_context_at_probe_time(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder/'session.json').write_text(json.dumps({'start':1,'end':86400}), encoding='utf-8')
            store = Store(folder)
            store.event(60, 'recorder_start')
            store.event(70, 'context', epoch='e', context='first')
            store.event(150, 'context', epoch='e', context='second')
            for at in (65, 100, 150):
                store.db.execute('INSERT INTO health VALUES(?,?,?,?,?,?,?)', ('e','node','AI',str(at),at,85,1))
            store.event(240, 'recorder_stop', deadline_reached=False)
            store.close()
            render(folder)
            with (folder/'health.csv').open(encoding='utf-8-sig', newline='') as f:
                self.assertEqual([r['context'] for r in csv.DictReader(f)], ['unknown','first','second'])
            report = (folder/'report.html').read_text(encoding='utf-8')
            self.assertIn('01月01日 08:01 起 · 采集已停止于 01月01日 08:04', report)

    def test_real_sampler_excludes_unobserved_gap_traffic_and_old_health(self):
        class FakeCore:
            downloaded=100
            def identity(self):return 'one-production-core'
            def get(self,path):
                if path=='/proxies':return {'proxies':{'Jimmy · 海外AI':{'type':'Selector','now':'node'}}}
                if path=='/providers/proxies':return {'providers':{'airport':{'proxies':[{'name':'node','alive':True,
                    'history':[{'time':'1970-01-01T00:01:30+00:00','delay':30}]}]}}}
                if path=='/connections':return {'connections':[{'id':'c','chains':['node','Jimmy · 海外AI'],
                    'download':self.downloaded,'upload':0,'metadata':{'host':'chatgpt.com'}}]}
                raise AssertionError('Unexpected or mutating endpoint '+path)
        with tempfile.TemporaryDirectory() as directory:
            r=Recorder({'folder':directory,'start':100,'end':300,'poll_seconds':5})
            r.client=FakeCore();r.last_meta=10000;r.tolerance={};r.context='c';r.epoch='e'
            r.poll(100);r.client.downloaded=200;r.poll(105);r.client.downloaded=99999;r.poll(200)
            r.store.db.commit()
            self.assertEqual(r.store.db.execute('SELECT sum(down) FROM minutes').fetchone()[0],100)
            self.assertEqual(r.store.db.execute('SELECT sum(api_s) FROM coverage').fetchone()[0],5)
            self.assertEqual(r.store.db.execute('SELECT count(*) FROM health').fetchone()[0],0)
            self.assertEqual(r.store.db.execute("SELECT count(*) FROM events WHERE kind='coverage_gap'").fetchone()[0],1)
            r.store.close()


if __name__=='__main__':unittest.main()
