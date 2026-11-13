"""Half-hour anonymous Chromium guest check, independent of the 8 KiB probe."""
import asyncio
import json
import time
from urllib.parse import urlsplit

from stability_core import CoreClient, live_get

CONDITIONS = "CHATGPT_GUEST_WINDOW"
SCHEMA = """create table if not exists st_guest(
 id integer primary key, run integer not null, node integer not null,
 start real not null, end real, status text not null, evidence text);
 create index if not exists st_guest_run on st_guest(run,node);"""
DOM = """() => {
 const text=(document.body?.innerText || '').slice(0,100000);
 const editor=document.querySelector('#prompt-textarea,textarea[name="prompt-textarea"]');
 return {
  region:/unsupported_country(?:_region_territory)?|country, region, or territory not supported|(?:not available|not supported|unavailable) in your (?:country|region)|不支持您所在的|您所在的(?:国家|地区).{0,15}(?:不受支持|不可用|不支持)/i.test(text),
  challenge:/just a moment|verify you are human|verifying you are human|验证您是真人/i.test(document.title+' '+text.slice(0,600)),
  composer:!!editor && editor.getBoundingClientRect().width>0 && !editor.disabled &&
           (editor.isContentEditable || !editor.readOnly && editor.tagName==='TEXTAREA'),
  loaded:document.readyState==='complete',
  login:/log in to continue|sign in to continue/i.test(text)
 };
}"""


def membership():
    proxies = live_get(CoreClient(), '/proxies')['proxies']
    return list(proxies['Jimmy · ai']['all'])


async def observe_page(page,proof):
    from playwright.async_api import Error
    pending=set()
    async def read_error(r):
        try:
            obj=await r.json()
            error=obj.get("error",obj) if isinstance(obj,dict) else {}
            if isinstance(error,dict) and error.get("code") in {"unsupported_country","unsupported_country_region_territory"}:
                proof["region_api"]=True
        except (ValueError,Error):
            pass
    def response(r):
        host=urlsplit(r.url).hostname or ''
        if host!='chatgpt.com' and not host.endswith('.chatgpt.com'):
            return
        if r.request.resource_type in ('xhr','fetch') and r.status in (400,403,451) and 'application/json' in r.headers.get('content-type',''):
            size=r.headers.get('content-length','')
            if not size or (size.isdecimal() and int(size)<65536):
                task=asyncio.create_task(read_error(r)); pending.add(task); task.add_done_callback(pending.discard)
        if r.request.resource_type in ('xhr','fetch') and r.ok and urlsplit(r.url).path.startswith('/backend-anon/'):
            proof['guest_api']=True
        if r.status==429:
            proof['limited']=True
        challenged=r.headers.get('cf-mitigated')=='challenge'
        if challenged:
            proof['saw_challenge']=True
        if r.request.resource_type=='document' and r.frame==page.main_frame:
            proof['http']=r.status
            proof['document_challenge']=challenged
        elif challenged:
            proof['resource_challenge']=True
        if r.request.resource_type=='script' and r.ok:
            proof['script_responses']+=1
    page.on('response',response)
    await page.goto('https://chatgpt.com/', wait_until='commit',timeout=15000)
    ready_since=challenge_since=None
    while True:
        try:
            flags=await page.evaluate(DOM)
        except Error as exc:
            if 'Execution context was destroyed' in str(exc):
                ready_since=None
                await asyncio.sleep(.25)
                continue
            raise
        flags['challenge'] |= bool(proof.get('document_challenge') or proof.get('resource_challenge'))
        proof.update(flags)
        url=urlsplit(page.url)
        official=url.scheme=='https' and url.hostname=='chatgpt.com'
        if proof.get('limited'):
            status='RATE_LIMITED'; break
        if proof.get('region_api') or (official and proof['region']):
            status='REGION_NG'; break
        if proof['challenge']:
            # Observe ordinary navigation only. Never interact with a challenge.
            challenge_since=challenge_since or time.monotonic()
            ready_since=None
            if time.monotonic()-challenge_since>=8:
                status='CHALLENGE'; break
            await asyncio.sleep(.5)
            continue
        challenge_since=None
        if official and flags['loaded'] and flags['composer'] and proof['http']==200 and proof.get('guest_api'):
            ready_since=ready_since or time.monotonic()
            if time.monotonic()-ready_since>=4:
                status='GUEST_UI_OK'; break
        else:
            ready_since=None
        if flags['loaded'] and flags['login'] and not flags['composer']:
            status='LOGIN_REQUIRED'; break
        await asyncio.sleep(.5)
    return status


async def probe(core, plan, seconds):
    from playwright.async_api import async_playwright, Error
    start = time.time()
    proof = dict(browser='Chrome', mode='anonymous', http=None, loaded=False,
                 composer=False, region=False, challenge=False, script_responses=0)
    status = 'INDETERMINATE'
    try:
        async with asyncio.timeout(seconds), async_playwright() as pw:
            browser = await pw.chromium.launch(channel='chrome', headless=True,
                proxy=dict(server=f'http://127.0.0.1:{core.mixed}',username=plan.key,password=core.password),
                args=['--disable-quic','--disable-background-networking','--disable-component-update'])
            try:
                page = await browser.new_page(locale='en-US')
                cdp = await page.context.new_cdp_session(page)
                await cdp.send('Network.enable')
                await cdp.send('Network.emulateNetworkConditions',dict(offline=False,latency=0,
                    downloadThroughput=256*1024,uploadThroughput=64*1024))
                status=await observe_page(page,proof)
            finally:
                await browser.close()
    except TimeoutError:
        status='TIMEOUT'
    except (Error,OSError) as exc:
        import re
        proof['error_class']=type(exc).__name__
        token=re.search(r'net::ERR_[A-Z_]+',str(exc))
        if token:
            proof['browser_error']=token.group()
        status='BROWSER_OR_NETWORK_ERROR'
    return start,time.time(),status,proof


class GuestWindow:
    def __init__(self,db,run):
        self.db,self.run=db,run
        # One calibration admission, persisted separately from timed survey results.
        request=db.execute("select rowid,at,data from st_event where run=? and kind='CHATGPT_PILOT_REQUEST' order by rowid desc limit 1",(run,)).fetchone()
        self.pilot_id=self.pilot_node=None
        self.in_pilot=False
        if request and request[1]>time.time()-180:
            used=db.execute("select 1 from st_event where run=? and kind='CHATGPT_PILOT_STARTED' and json_extract(data,'$.request')=?",(run,request[0])).fetchone()
            if not used:
                self.pilot_id=request[0]
                self.pilot_node=json.loads(request[2])['node']
                self.pilot_until=request[1]+180
        self.task=self.plan=None
        self.next=0
        self.end=0
        self.ai=set()
        self.global_pause=0
        self.hold={}
        self.last={}
        self.seen={}
        db.executescript(SCHEMA)
        db.execute("update st_guest set status='UNKNOWN' where run=? and status='IN_PROGRESS'",(run,))
        ev=db.execute('select data from st_event where run=? and kind=? order by at desc limit 1',(run,CONDITIONS)).fetchone()
        if ev:
            data=json.loads(ev[0])
            self.end=data['end']
            self.ai=set(data['ai_names'])
        for name,status,start in db.execute('select n.name,g.status,g.start from st_guest g join st_node n on n.id=g.node where g.run=? order by g.start',(run,)):
            self.record(name,status,start)
        db.commit()

    def record(self,name,status,at):
        self.seen[name]=self.seen.get(name,0)+1
        self.last[name]=at
        if status=='RATE_LIMITED':
            self.global_pause=self.end
        if status=='CHALLENGE':
            self.hold[name]=self.end

    def finish(self,runner):
        try:
            _,end,status,proof=self.task.result()
        except Exception as exc:
            end,status,proof=time.time(),'BROWSER_OR_NETWORK_ERROR',{'error_class':type(exc).__name__}
        if self.in_pilot:
            runner.event('CHATGPT_PILOT_RESULT',dict(request=self.pilot_id,node=self.plan.node,status=status,end=end,evidence=proof))
            if status=='RATE_LIMITED':
                runner.gpt_global=max(runner.gpt_global,time.monotonic()+1800)
            self.db.commit()
            self.task=self.plan=self.pilot_id=None
            self.in_pilot=False
            return
        self.db.execute('update st_guest set end=?,status=?,evidence=? where id=?',(end,status,json.dumps(proof),self.row))
        self.db.commit()
        self.record(self.name,status,end)
        if status=='RATE_LIMITED':
            runner.gpt_global=max(runner.gpt_global,time.monotonic()+1800)
        self.task=self.plan=None

    def start(self,runner,now):
        wall=time.time()
        if self.pilot_id and not self.task and wall<self.pilot_until and now>=runner.gpt_global:
            p=runner.plans.get(self.pilot_node)
            if p and not p.active and p.key!=runner.special_key and p.node not in runner.waiting and now>=p.cool and len(runner.tasks)+int(bool(runner.special))<runner.limit:
                runner.event('CHATGPT_PILOT_STARTED',dict(request=self.pilot_id,node=p.node,mode='single anonymous page'))
                self.db.commit()
                self.plan=p
                self.in_pilot=True
                self.task=asyncio.create_task(probe(runner.core,p,27))
                return
        if self.end and wall>=self.end and not self.task:
            if not self.db.execute("select 1 from st_event where run=? and kind='CHATGPT_GUEST_ENDED'",(self.run,)).fetchone():
                counts=dict(self.db.execute('select status,count(*) from st_guest where run=? group by status',(self.run,)))
                runner.event('CHATGPT_GUEST_ENDED',dict(deadline=self.end,counts=counts))
                self.db.commit()
            self.end=0
        if self.task or wall+6>=self.end or wall<max(self.next,self.global_pause) or now<runner.gpt_global or len(runner.tasks)+int(bool(runner.special))>=runner.limit:
            return
        self.next=wall+.75
        names=dict(self.db.execute('select id,name from st_node'))
        options=[p for p in runner.plans.values() if not p.active and p.key!=runner.special_key and
                 p.node not in runner.waiting and p.cool<=now and self.hold.get(names[p.node],0)<=wall
                 and runner.gpt_due.get(p.node,0)<=now+900]
        if not options:
            return
        def priority(p):
            name=names[p.node]
            return (self.seen.get(name,0),name not in self.ai,self.last.get(name,0),name.startswith('['),name)
        plan=min(options,key=priority)
        self.name=names[plan.node]
        self.plan=plan
        self.next=wall+30
        self.row=self.db.execute("insert into st_guest(run,node,start,status) values(?,?,?,'IN_PROGRESS')",
                                 (self.run,plan.node,wall)).lastrowid
        self.db.commit()
        self.task=asyncio.create_task(probe(runner.core,plan,min(27,self.end-wall)))
