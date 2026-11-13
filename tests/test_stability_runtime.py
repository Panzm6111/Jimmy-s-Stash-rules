"""Exercise the production dispatcher and HTTP client against local fake Mihomo."""
import asyncio
import json
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path

import aiohttp
from aiohttp import web

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from stability_core import Sidecar,TARGETS
from stability_runner import Plan,Runner
from stability_stats import connect,ranking


class Runtime(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        path=Path(self.tmp.name)/'master.db'
        path.touch()
        self.db=connect(path,True)
        self.wall=time.time()
        self.tick=time.monotonic()
        self.db.execute("insert into st_run values(1,'pressure',?,?,'running',x'01')",(self.wall,self.wall+1800))
        self.runner=Runner(self.db,self.db.execute('select * from st_run').fetchone())
        self.runner.available=True
        self.runner.save_env({'api':True,'uplink':True,'direct':[(204,20),(204,15)]})
        self.inflight=0
        self.peak=0
        self.per_node={}
        self.max_per_node=0
        self.responses={}
        self.active_tasks=set()
        self.release=asyncio.Event()
        self.mode='slow'
        async def delay(req):
            n=req.match_info['name']
            self.inflight+=1
            self.peak=max(self.peak,self.inflight)
            self.per_node[n]=self.per_node.get(n,0)+1
            self.max_per_node=max(self.max_per_node,self.per_node[n])
            try:
                if self.mode=='slow':
                    await self.release.wait()
                if self.mode=='timeout':
                    await asyncio.sleep(3.05)
                    return web.json_response({'message':'timeout'},status=504)
                if self.mode=='503':
                    return web.json_response({},status=503)
                self.responses[n,req.query['url']]=self.mode!='wrong-status'
                return web.json_response({'delay':200})
            finally:
                self.inflight-=1
                self.per_node[n]-=1
        async def proxy(req):
            n=req.match_info['name']
            return web.json_response({'extra':{t:{'alive':self.responses.get((n,t),False),
                'history':[{'delay':200}]} for t in TARGETS}})
        self.app=web.Application()
        self.app.router.add_get('/proxies/{name}/delay',delay)
        self.app.router.add_get('/proxies/{name}',proxy)
        self.server=web.AppRunner(self.app)
        await self.server.setup()
        self.site=web.TCPSite(self.server,'127.0.0.1',0)
        await self.site.start()
        self.core=Sidecar([],'test')
        self.core.api=self.server.addresses[0][1]
        self.core.session=aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5),
                                               connector=aiohttp.TCPConnector(limit=32))
        self.runner.core=self.core

    async def asyncTearDown(self):
        self.release.set()
        await asyncio.gather(*(t for _,t in self.runner.tasks.values()),return_exceptions=True)
        await self.core.close()
        await self.server.cleanup()
        self.db.close()
        self.tmp.cleanup()

    def add(self,count,interval):
        for i in range(count):
            self.db.execute('insert into st_node values(?,?,?,?,?)',(i,str(i),'p',str(i),'mock'))
            self.db.execute('insert into st_active values(1,?,?,NULL)',(i,self.wall))
            self.runner.plans[i]=Plan(i,str(i),self.tick,interval,turn=i%2)
        self.db.commit()

    def dispatch(self,delta):
        self.runner.dispatch(self.tick+delta,self.wall+delta)

    async def finish(self):
        await asyncio.gather(*(t for _,t in self.runner.tasks.values()))
        self.runner.collect()
        self.runner.flush(time.time(),True)

    async def test_real_2p4s_single_flight(self):
        self.add(1,1)
        self.dispatch(0)
        await asyncio.sleep(1)
        self.dispatch(1)
        await asyncio.sleep(1)
        self.dispatch(2)
        await asyncio.sleep(.4)
        self.release.set()
        await self.finish()
        self.dispatch(3)
        await self.finish()
        result=dict(self.db.execute('select status,count(*) from st_sample group by status'))
        self.assertEqual(result,{'SKIPPED_BUSY':2,'SUCCESS':2})
        self.assertEqual(self.max_per_node,1)
        row=self.db.execute("select start,end,elapsed,delay from st_sample where status='SUCCESS' order by slot limit 1").fetchone()
        self.assertGreater(row['elapsed'],2350)
        self.assertEqual(row['delay'],200)
        self.assertGreater(row['end']-row['start'],2.35)

    async def test_hundred_slow_entries_no_backlog(self):
        self.add(100,5)
        from unittest.mock import patch
        # Raise public-target budget only inside this synthetic localhost test to exercise global cap.
        with patch('stability_runner.PER_TARGET',100):
            self.dispatch(0)
            async with asyncio.timeout(3):
                while self.peak<30:
                    await asyncio.sleep(.01)
            self.assertEqual(len(self.runner.tasks),30)
            self.assertEqual(self.peak,30)
            self.dispatch(5)
            self.assertEqual(len(self.runner.tasks),30)
            self.release.set()
            await self.finish()
            for tick in (10,15,20,25):
                self.dispatch(tick)
                await self.finish()
            self.dispatch(26.1)
            await self.finish()
        self.assertEqual(self.max_per_node,1)
        self.assertEqual(self.db.execute("select count(distinct node) from st_sample where status='SUCCESS'").fetchone()[0],100)
        self.assertEqual(self.db.execute('select sum(planned) from st_min').fetchone()[0],600)
        scores=ranking(self.db,self.runner.run,now=self.wall+30)
        self.assertEqual(sum(x['actual'] for x in scores),150)
        self.assertEqual(sum(x['n'] for x in scores),150)

    async def test_staggered_slots_wait_only_inside_their_window(self):
        self.add(3,5)
        self.runner.limit=1
        self.runner.plans[1].next=self.tick+.1
        self.runner.plans[2].next=self.tick+.2
        self.dispatch(0)
        self.dispatch(.1)
        self.dispatch(.2)
        self.assertEqual(set(self.runner.waiting),{1,2})
        self.release.set()
        await self.finish()
        self.runner.debt[2]=.4
        self.dispatch(.3)
        self.assertEqual(set(self.runner.tasks),{2})
        await self.finish()
        self.dispatch(1.2)
        await self.finish()
        self.assertEqual(self.db.execute("select status from st_sample where node=1").fetchone()[0],'SKIPPED_CAPACITY')
        self.assertFalse(self.runner.waiting)
        self.assertEqual(self.peak,1)

    async def test_timeout_actual(self):
        self.mode='timeout'
        r=await self.core.probe('1',0)
        self.assertEqual(r[:3],('NODE_TIMEOUT',None,'504'))

    async def test_positive_delay_wrong_204_and_api_recovery(self):
        self.mode='wrong-status'
        self.assertEqual((await self.core.probe('1',0))[0],'UNKNOWN_ERROR')
        self.mode='503'
        self.assertEqual((await self.core.probe('1',1))[0],'NODE_TEST_FAILED')
        saved=self.core.api
        self.core.api=1
        lost=await self.core.probe('1',0)
        self.assertEqual((lost[0],lost[3]),('API_UNAVAILABLE',True))
        self.core.api=saved
        self.mode='fast'
        self.assertEqual((await self.core.probe('1',0))[0],'SUCCESS')

    async def test_counts_exclude_censored_and_preserve_calendar_gap(self):
        self.add(1,5)
        self.mode='fast'
        self.dispatch(0)
        await self.finish()
        self.runner.available=False
        self.dispatch(5)
        await self.finish()
        self.runner.available=True
        self.dispatch(605)
        await self.finish()
        r=ranking(self.db,self.runner.run,now=self.wall+610)[0]
        self.assertEqual((r['actual'],r['n'],r['success']),(2,2,1))
        self.assertAlmostEqual(r['coverage'],10/610,places=4)
        self.assertFalse(r['eligible'])
        missed=self.db.execute("select data from st_event where kind='MISSED_SLOTS'").fetchone()
        self.assertEqual(json.loads(missed[0])['count'],119)

    async def test_failed_admission_commit_never_sends(self):
        self.add(1,5)
        class RefuseCommit:
            def __init__(self,db):
                self.execute=db.execute
            def commit(self):
                raise sqlite3.OperationalError('simulated disk full on commit')
        self.runner.db=RefuseCommit(self.db)
        with self.assertRaises(sqlite3.OperationalError):
            self.dispatch(0)
        self.db.rollback()
        await asyncio.sleep(.01)
        self.assertEqual(len(self.runner.tasks),0)
        self.assertEqual(self.peak,0)
        self.assertEqual(self.db.execute('select count(*) from st_sample').fetchone()[0],0)

    async def test_writer_unavailable_between_intent_and_send(self):
        self.add(1,5)
        self.db.execute('pragma busy_timeout=0')
        self.dispatch(0)
        other=sqlite3.connect(Path(self.tmp.name)/'master.db')
        try:
            other.execute('begin immediate')
            await asyncio.gather(*(t for _,t in self.runner.tasks.values()))
            self.assertEqual(self.peak,0)
            other.commit()
            await self.finish()
            row=self.db.execute('select start,end,status,raw from st_sample').fetchone()
            self.assertEqual(tuple(row),(None,None,'SKIPPED_CAPACITY','SKIPPED_CAPACITY/storage-before-send'))
            self.mode='fast'
            self.dispatch(5)
            await self.finish()
            self.assertEqual(self.peak,1)
        finally:
            other.close()
