"""Subscription selection and persisted experiment isolation; no public traffic."""
import json
import sys
import tempfile
import time
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import yaml

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import stability_core as core
from stability import create
from stability_runner import Runner
from stability_stats import connect, run_config


class Scope(unittest.TestCase):
    def test_installed_profile_is_pinned_and_never_falls_back_to_current(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'profiles').mkdir()
            registry={'current':'ncloud','items':[
                {'uid':'adsl','name':'ADSL','type':'remote','file':'adsl.yaml'},
                {'uid':'ncloud','name':'NCloud','type':'remote','file':'ncloud.yaml'}]}
            (root/'profiles.yaml').write_text(yaml.safe_dump(registry))
            row={'name':'test SSR','type':'ssr','server':'127.0.0.1','port':1234,'password':'fake'}
            target=root/'profiles'/'adsl.yaml'
            target.write_text(yaml.safe_dump({'proxies':[row]}))
            with patch.object(core,'ROOT',root),patch.object(core,'live_get',side_effect=AssertionError('daily inventory used')):
                source=core.profile_source('ADSL')
                nodes,issues=core.inventory_snapshot(b'salt',source)
                self.assertEqual([(n.provider,n.kind) for n in nodes],[('ADSL','ShadowsocksR')])
                self.assertEqual(issues,[])
                row['port']=1235
                target.write_text(yaml.safe_dump({'proxies':[row]}))
                changed,_=core.inventory_snapshot(b'salt',source)
                self.assertNotEqual(nodes[0].key,changed[0].key)
                registry['items']=registry['items'][1:]
                (root/'profiles.yaml').write_text(yaml.safe_dump(registry))
                with self.assertRaises(ValueError):
                    core.inventory_snapshot(b'salt',source)

    def test_no_partial_or_ambiguous_profile_inventory(self):
        with self.assertRaisesRegex(ValueError,'ambiguous'):
            core.project_nodes('ADSL',[{'name':'same','type':'ShadowsocksR'}],
                [{'name':'same','type':'ssr'},{'name':'same','type':'ssr'}],b'salt')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'profiles').mkdir()
            (root/'profiles.yaml').write_text(yaml.safe_dump({'items':[
                {'uid':'a','name':'ADSL','type':'remote','file':'../outside.yaml'}]}))
            with patch.object(core,'ROOT',root),self.assertRaisesRegex(ValueError,'path'):
                core.profile_inventory(b'salt',{'kind':'installed-profile','uid':'a','name':'ADSL'})

    def test_duration_disabled_gpt_and_rate_history_survive_phase_transition(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'test.sqlite'
            path.touch()
            with closing(connect(path,True)) as db:
                old=create(db,'pressure',b'old',{'experiment_id':'NCloud'})
                db.execute('insert into st_env(run,at,data) values(?,?,?)',
                    (old['id'],time.time(),json.dumps({'ordinary':15,'candidate':5})))
                cfg={'subscription':'ADSL','experiment_id':'adsl','formal_hours':48,
                     'chatgpt_enabled':False,'guest_enabled':False}
                pressure=create(db,'pressure',b'new',cfg)
                formal=create(db,'formal',pressure['salt'],run_config(db,pressure['id']))
                self.assertEqual(pressure['end']-pressure['start'],1800)
                self.assertEqual(formal['end']-formal['start'],48*3600)
                self.assertEqual(run_config(db,formal['id']),cfg)
                runner=Runner(db,formal)
                runner.calibrate()
                self.assertEqual(runner.level,0)  # Do not inherit NCloud's pressure.
                with patch('stability_runner.gpt.probe',side_effect=AssertionError('GPT requested')):
                    runner.start_gpt(time.monotonic())
                self.assertIsNone(runner.special)
                runner.recover()
                self.assertEqual(db.execute('select count(*) from st_chatgpt where run=?',(formal['id'],)).fetchone()[0],0)
                self.assertEqual(db.execute("select count(*) from st_event where run=? and kind='CHATGPT_TEST_CONDITIONS'",(formal['id'],)).fetchone()[0],0)
                self.assertEqual(db.execute('select state from st_run where id=?',(old['id'],)).fetchone()[0],'running')
                from stability_view import report
                with patch('stability_view.PRIVATE',Path(folder)):
                    report(db,formal['id'])
                html=(Path(folder)/f"report-{formal['id']}.html").read_text(encoding='utf-8')
                self.assertIn('订阅：ADSL',html)
                self.assertIn('按用户要求取消',html)
                self.assertNotIn('<h2>ChatGPT 匿名新连接',html)
