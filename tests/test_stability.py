import asyncio
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from stability_core import project_nodes,notice_labels,cached_generation_matches
from stability_runner import Plan, Runner, admit, candidates, level_change
from stability_stats import DDL, aggregate, classify, connect, period


class Measurements(unittest.TestCase):
    def test_01_single_flight(self):
        p = Plan(1,'n',0,1)
        states = []
        for i in range(4):
            self.assertEqual(p.due(i),(i,0))
            p.active = 0<i<2.4
            states.append(admit(p,i,0,0,30,0))
        self.assertEqual(states,[None,'SKIPPED_BUSY','SKIPPED_BUSY',None])

    def test_02_unknown_completion(self):
        p=Plan(1,'n',0,1,cool=8.25)
        for t in (5,6,7,8):
            self.assertEqual(admit(p,t,0,0,30,0),'SKIPPED_BUSY')
        self.assertIsNone(admit(p,9,0,0,30,0))

    def test_03_slow_hundred_fair(self):
        plans=[Plan(i,str(i),0) for i in range(100)]
        started=set()
        for tick in range(5):
            picked=[]
            for p in sorted(plans,key=lambda n:n.last):
                if not admit(p,tick,len(picked),0,30,0):
                    picked.append(p.node)
                    p.last=tick
            self.assertEqual(len(picked),30)
            started.update(picked)
        self.assertEqual(len(started),100)

    def test_04_capacity_and_target_budget(self):
        p=Plan(1,'n',0)
        self.assertEqual(admit(p,0,30,0,30,0),'SKIPPED_CAPACITY')
        self.assertEqual(admit(p,0,0,8,30,0),'SKIPPED_CAPACITY')
        p.interval=1
        self.assertEqual(admit(p,0,15,0,30,15),'SKIPPED_CAPACITY')
        p.interval=5
        self.assertIsNone(admit(p,0,15,0,30,15))

    def test_05_partial_node_failure(self):
        e={'api':True,'uplink':True,'direct':[(204,25),(204,40)]}
        self.assertEqual(classify('NODE_TIMEOUT',[(20,3),(18,0)],e,0),'NODE_TIMEOUT')
        self.assertEqual(classify('NODE_TIMEOUT',[(20,18),(18,18)],e,0),'UNKNOWN_ERROR')

    def test_06_api_loss_recovery(self):
        e={'api':False,'uplink':True,'direct':[(204,25),(204,40)]}
        self.assertEqual(classify('NODE_TEST_FAILED',[(20,1)]*2,e,0),'API_UNAVAILABLE')
        e['api']=True
        self.assertEqual(classify('NODE_TEST_FAILED',[(20,1)]*2,e,0),'NODE_TEST_FAILED')

    def test_07_suspend(self):
        p=Plan(1,'n',0)
        self.assertEqual(p.due(600.1),(600,120))
        self.assertIsNone(p.due(600.2))

    def test_08_target_and_network(self):
        e={'api':True,'uplink':True,'direct':[(503,25),(204,40)]}
        peers=[(20,20),(18,0)]
        self.assertEqual(classify('NODE_TEST_FAILED',peers,e,0),'TARGET_UNAVAILABLE')
        e['uplink']=False
        self.assertEqual(classify('NODE_TIMEOUT',peers,e,0),'LOCAL_NETWORK_DOWN')

    def test_09_inventory(self):
        def inventory(names,change=1,p='provider'):
            rows=[dict(name=n,type='ss',port=change) for n in names]
            return [n.key for n in project_nodes(p,rows,rows,b'salt')]
        a,b=inventory(['A','B'])
        self.assertEqual(inventory(['B','C'])[0],b)
        self.assertNotIn(a,inventory(['B','C']))
        self.assertNotEqual(a,inventory(['A'],2)[0])
        self.assertNotEqual(a,inventory(['A'],p='other')[0])
        with self.assertRaises(ValueError):
            inventory(['A','A'])

    def test_10_writer_lock(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'master.db'
            path.touch()
            a,b=connect(path,True),connect(path)
            c=sqlite3.connect(path,timeout=0)
            try:
                a.execute('begin immediate')
                with self.assertRaises(sqlite3.OperationalError):
                    c.execute('begin immediate')
                self.assertEqual(b.execute('select count(*) from st_run').fetchone()[0],0)
                a.commit()
                c.execute('begin immediate')
                c.commit()
            finally:
                a.close()
                b.close()
                c.close()

    def test_11_process_killed_recovery(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'master.db'
            path.touch()
            db=connect(path,True)
            db.execute("insert into st_run values(1,'pressure',0,1800,'running',x'01')")
            db.commit()
            code="""import sqlite3,sys,time
db=sqlite3.connect(sys.argv[1])
db.execute("insert into st_sample(run,node,slot,target,status,interval) values(1,1,0,0,'PENDING',5)")
db.commit()
db.execute("update st_sample set status='SUCCESS'")
print('ready',flush=True)
time.sleep(30)"""
            child=subprocess.Popen([sys.executable,'-c',code,str(path)],stdout=subprocess.PIPE)
            try:
                self.assertEqual(child.stdout.readline().strip(),b'ready')
                child.kill()
                child.wait()
                runner=Runner(db,db.execute('select * from st_run').fetchone())
                runner.recover()
                runner.recover()
                self.assertEqual(tuple(db.execute('select count(*),status from st_sample').fetchone()),(1,'UNKNOWN_ERROR'))
                self.assertEqual(db.execute('select sum(planned) from st_min').fetchone()[0],1)
                self.assertEqual(db.execute('pragma integrity_check').fetchone()[0],'ok')
            finally:
                child.kill()
                child.wait()
                child.stdout.close()
                db.close()

    def test_12_resume_no_backlog(self):
        plans=[Plan(i,str(i),.02*i) for i in range(100)]
        for p in plans:
            self.assertGreater(p.due(605)[1],100)
            self.assertIsNone(p.due(605))

    def test_13_daily_client_isolation(self):
        # Production interface only exposes inventory GET; isolated core has the only probe method.
        from stability_core import inventory,Sidecar
        from mihomo_readonly import CoreClient
        self.assertFalse(hasattr(CoreClient,'probe'))
        self.assertNotIn('put',Sidecar.probe.__code__.co_names)
        self.assertNotIn('getenv',Sidecar.probe.__code__.co_names)

    def test_14_unicode(self):
        name='中文 / % ? # : 👋'
        row={'name':name,'type':'ss'}
        n=project_nodes('一组',[row],[row],b'salt')[0]
        self.assertEqual(n.name,name)
        self.assertEqual(quote(n.key,safe=''),n.key)

    def test_subscription_notices_require_matching_adapter_settings(self):
        rows=[dict(type='ss',port=53,server='info.invalid',name=n) for n in
              ('剩余流量：1 GB','距离下次重置剩余 9 天','套餐到期：明年')]
        rows.append(dict(type='ss',port=443,server='real.invalid',name='测试地区'))
        self.assertEqual(notice_labels(rows),{x['name'] for x in rows[:3]})
        self.assertFalse(notice_labels([rows[0],rows[3]]))
        with self.assertRaises(ValueError):
            project_nodes('P',[dict(name='a',type='Vless')],[dict(name='a',type='ss')],b's')

    def test_stale_local_provider_cache_is_quarantined(self):
        cache=[dict(name=n,type='ss') for n in ('剩余流量：100GB','真实出口')]
        self.assertTrue(cached_generation_matches(cache,cache))
        newer=[dict(name='剩余流量：90GB',type='ss'),cache[1]]
        self.assertFalse(cached_generation_matches(newer,cache))

    def test_15_hysteresis(self):
        rows=[dict(id=i,eligible=True,score=99-i*.05) for i in range(12)]
        self.assertEqual(candidates(rows,{10,11}),set(range(8))|{10,11})
        self.assertFalse(candidates([dict(id=1,eligible=False,score=100)],set()))
        self.assertEqual(level_change(1,2,0,60),1)
        self.assertEqual(level_change(1,2,0,121),2)
        self.assertEqual(level_change(2,0,5,301),1)


if __name__=='__main__':
    unittest.main()
