"""Local, script-rendered browser fixture and name-group aggregation regression."""
import asyncio
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from playwright.async_api import async_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from stability_guest import DOM
import stability_core as core

class GuestTests(unittest.IsolatedAsyncioTestCase):
    async def test_visitor_render(self):
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(channel='chrome',headless=True)
            try:
                page=await browser.new_page()
                await page.set_content("<textarea id='prompt-textarea'></textarea>")
                self.assertTrue((await page.evaluate(DOM))['composer'])
                await page.evaluate("setTimeout(()=>{document.body.innerText='Country, region, or territory not supported'},100)")
                await page.wait_for_function("document.body.innerText.includes('not supported')")
                result=await page.evaluate(DOM)
                self.assertTrue(result['region'])
                self.assertFalse(result['composer'])
            finally:
                await browser.close()

    def test_inventory_drift_keeps_matched_node(self):
        installed={'proxy-providers':{'p':{'type':'inline','payload':[{'name':'old','type':'ss'},{'name':'A','type':'ss'}]}}}
        live={'providers':{'p':{'proxies':[{'name':'new','type':'Shadowsocks'},{'name':'A','type':'Shadowsocks'}]}}}
        with patch.object(core,'live_get',return_value=live),patch.object(core.yaml,'safe_load',return_value=installed),patch.object(Path,'read_bytes',return_value=b''):
            nodes,issues=core.inventory_snapshot(b'salt')
        self.assertEqual([n.name for n in nodes],['A'])
        self.assertTrue(issues)

    def test_window_deadline_and_name_history(self):
        import json,sqlite3,time
        from stability_guest import GuestWindow,SCHEMA,CONDITIONS
        from stability_view import guest_names
        db=sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.executescript(SCHEMA+"""
          create table st_event(run,at,kind,data);
          create table st_node(id,name,provider);
          create table st_chatgpt(run,node,tls_limit_s,status,http);
          insert into st_node values(1,'A','p'),(2,'A','p'),(3,'A','other');
          insert into st_chatgpt values(7,1,5,'HTTP_REACHED',200),(7,2,5,'TIMEOUT',NULL),
          (7,1,3,'HTTP_REACHED',200),(7,3,5,'HTTP_REACHED',200);
          insert into st_guest(run,node,start,end,status) values(7,2,10,12,'REGION_NG');
        """)
        db.execute("insert into st_event values(7,0,?,?)",(CONDITIONS,json.dumps({'end':1800,'ai_names':['A']})))
        rows=guest_names(db,7)['rows']
        combined=next(r for r in rows if r['provider']=='p')
        self.assertEqual(combined['history'],{3:'1/1',5:'1/2'})
        self.assertTrue(combined['result'].startswith('NG'))
        self.assertEqual(next(r for r in rows if r['provider']=='other')['result'],'未测')
        from unittest.mock import Mock
        runner=Mock()
        w=GuestWindow(db,7)
        w.start(runner,time.monotonic())
        w.start(runner,time.monotonic())
        runner.event.assert_called_once()
        self.assertIsNone(w.task)

    async def test_guest_verdict_from_rendered_controls(self):
        from stability_guest import observe_page
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(channel='chrome',headless=True)
            try:
                for case,expected in [('ready','GUEST_UI_OK'),('region','REGION_NG'),('challenge','CHALLENGE')]:
                    page=await browser.new_page()
                    async def fixture(route):
                        if route.request.url.endswith('/backend-anon/control'):
                            return await route.fulfill(status=403 if case=='region' else 200,content_type='application/json',
                                body='{"error":{"code":"unsupported_country"}}' if case=='region' else '{}')
                        if case=='challenge':
                            return await route.fulfill(status=403,headers={'cf-mitigated':'challenge'},body='Challenge')
                        await route.fulfill(content_type='text/html',body="""<textarea id="prompt-textarea"></textarea><script>fetch('/backend-anon/control')</script>""")
                    await page.route('**/*',fixture)
                    proof=dict(challenge=False,http=None,script_responses=0)
                    try:
                        self.assertEqual(await asyncio.wait_for(observe_page(page,proof),10),expected)
                    finally:
                        await page.close()
            finally:
                await browser.close()
