import asyncio
import json
import sys
import tempfile
import time
import unittest
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import stability_chatgpt as gpt
from stability_runner import Plan,Runner
from stability_stats import connect
from stability_view import chatgpt_counts,gpt_comparison


class ChatGPT(unittest.IsolatedAsyncioTestCase):
    def test_web_outcomes(self):
        cases=[
            (200,{'content-type':'text/html'},b'<title>ChatGPT</title>','WEB_ENTRY_OK'),
            (200,{'content-type':'text/html'},b'<title>Something else</title>','HTTP_REACHED'),
            (200,{'cf-mitigated':'challenge'},b'','CHALLENGE'),
            (403,{},b'<title>Just a moment...</title>','CHALLENGE'),
            (403,{},b'{"error":{"code":"unsupported_country_region_territory"}}','REGION_RESTRICTED'),
            (403,{'cf-ray':'opaque'},b'Forbidden','FORBIDDEN'),
            (401,{},b'','AUTH_REQUIRED'),(429,{},b'','RATE_LIMITED'),
            (503,{},b'','SERVER_ERROR'),(302,{'location':'/elsewhere'},b'','REDIRECT')]
        for code,h,b,expected in cases:
            with self.subTest(code=code,expected=expected):
                self.assertEqual(gpt.classify(code,h,b),expected)

    async def test_transport_limits_and_no_site_credentials(self):
        sent=[]
        class Writer:
            transport=SimpleNamespace(abort=lambda:None)
            def write(self,b): sent.append(b)
            async def drain(self): pass
            async def start_tls(self,ctx,**kw):
                assert ctx.check_hostname and kw['server_hostname']=='chatgpt.com' and kw['ssl_handshake_timeout']==5
                await asyncio.sleep(3.15)
            def get_extra_info(self,k): return SimpleNamespace(version=lambda:'TLSv1.3')
        class SlowBody(asyncio.StreamReader):
            async def read(self,size):
                await asyncio.sleep(2.1)
                return await super().read(size)
        reader=SlowBody()
        reader.feed_data(b'HTTP/1.1 200 Established\r\n\r\nHTTP/1.1 200 OK\r\nContent-Type: text/html\r\nSet-Cookie: private\r\n\r\n<title>ChatGPT</title>'+b'a'*20000)
        reader.feed_eof()
        with patch('asyncio.open_connection',AsyncMock(return_value=(reader,Writer()))):
            out=await gpt.probe(9999,'local','credential')
        self.assertTrue(out['tls'])
        self.assertEqual(out['bytes_read'],8192)
        self.assertEqual(out['status'],'WEB_ENTRY_OK')
        self.assertIn(b'Proxy-Authorization',sent[0])
        self.assertNotIn(b'Authorization',sent[1])
        self.assertNotIn(b'Cookie',sent[1])
        self.assertNotIn('private',json.dumps(out))
        self.assertGreaterEqual(out['end'],out['start'])
        self.assertTrue(3000<out['handshake_ms']<=5000)
        self.assertTrue(5000<out['elapsed']<7000)
        self.assertEqual((out['tls_limit_s'],out['total_limit_s']),(5,7))

    def test_old_rows_event_and_paired_comparison(self):
        db=sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.execute('create table st_event(run,at,kind,data)')
        db.executescript(gpt.SCHEMA.replace(',\n tls_limit_s INTEGER NOT NULL DEFAULT 3',''))
        old=json.dumps({'phase':'tls','error':'ConnectionAbortedError'})
        db.execute("insert into st_chatgpt(run,node,status,elapsed,evidence) values(7,11,'TRANSPORT_ERROR',3016,?)",(old,))
        before=db.execute('select * from st_chatgpt').fetchall()
        self.assertEqual(chatgpt_counts(db,7)[11]['conditions'][3]['old_timeout'],1)
        gpt.register_conditions(db,7)
        gpt.register_conditions(db,7)
        self.assertEqual(db.execute('select * from st_chatgpt').fetchone()[:-1],before[0])
        self.assertEqual(dict(db.execute('select kind,count(*) from st_event group by kind')),
                         {gpt.CONDITION_EVENT:1,gpt.CADENCE_EVENT:1})
        event=json.loads(db.execute('select data from st_event where kind=?',(gpt.CADENCE_EVENT,)).fetchone()[0])
        self.assertEqual((event['previous_interval_s'],event['interval_s'],event['global_spacing_s']),(900,450,7.5))
        self.assertEqual(event['last_previous_id'],before[0][0])
        for node,ms,code in [(11,4000,200),(11,5000,200),(11,3000,200),(12,3100,403),(13,5001,200)]:
            db.execute("""insert into st_chatgpt(run,node,status,http,tls,tls_limit_s,evidence)
                       values(7,?,'HTTP_REACHED',?,1,5,?)""",(node,code,json.dumps({'handshake_ms':ms})))
        counts=chatgpt_counts(db,7)
        # Even a successful HTTP 200 after validated TLS cannot prove model inference.
        self.assertTrue(all(v['conversation']=='UNVERIFIED' for v in counts.values()))
        self.assertEqual(counts[11]['conditions'][5]['late'],2)
        self.assertEqual(counts[12]['conditions'][5]['late'],0)
        self.assertEqual(counts[13]['conditions'][5]['late'],0)
        self.assertEqual(gpt_comparison(counts),dict(cohort=1,retested=1,now200=1,late200=1,first200=1))

    async def test_gpt_reserves_node_and_backs_off(self):
        with tempfile.TemporaryDirectory() as folder:
            dbfile=Path(folder)/'db'
            dbfile.touch()
            db=connect(dbfile,True)
            try:
                db.executescript(gpt.SCHEMA)
                r=Runner(db,{'id':1})
                now=time.monotonic()
                r.plans={1:Plan(1,'a',now,active=True),2:Plan(2,'b',now)}
                r.gpt_due={1:now-1,2:now}
                r.core=SimpleNamespace(mixed=1234,password='local')
                data=dict(start=time.time(),end=time.time(),elapsed=20,status='RATE_LIMITED',http=429,tls=True)
                with patch.object(gpt,'probe',AsyncMock(return_value=data)) as probe:
                    r.start_gpt(now)
                    self.assertEqual(r.special_key,'b')
                    self.assertEqual(r.gpt_due[2],now+450)
                    self.assertEqual(r.gpt_global,now+7.5)
                    r.plans[1].active=False
                    r.start_gpt(now+8)
                    self.assertEqual(r.special_key,'b')
                    await r.special
                    r.finish_special()
                    probe.assert_awaited_once_with(1234,'b','local')
                self.assertIsNone(r.special_key)
                self.assertGreaterEqual(r.gpt_global,now+1800)
                r.start_gpt(now+8)
                self.assertIsNone(r.special)
                self.assertEqual(tuple(db.execute('select node,status,http from st_chatgpt').fetchone()),(2,'RATE_LIMITED',429))
            finally:
                db.close()
