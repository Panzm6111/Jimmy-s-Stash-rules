"""Anonymous ChatGPT front-door reachability. No browser state, API key or inference."""
import asyncio
import base64
import json
import re
import ssl
import time
from email.utils import parsedate_to_datetime

HOST='chatgpt.com'
INTERVAL=450
GLOBAL_SPACING=7.5
BODY_LIMIT=8192
TLS_LIMIT_S=5
TOTAL_LIMIT_S=7
CONDITION_EVENT='CHATGPT_TEST_CONDITIONS'
CADENCE_EVENT='CHATGPT_CADENCE_CHANGED'
SCHEMA="""CREATE TABLE IF NOT EXISTS st_chatgpt(
 id INTEGER PRIMARY KEY,run INTEGER,node INTEGER,slot REAL,start REAL,end REAL,elapsed REAL,
 status TEXT NOT NULL,http INTEGER,tls INTEGER DEFAULT 0,evidence TEXT,env INTEGER,
 tls_limit_s INTEGER NOT NULL DEFAULT 3);
 CREATE INDEX IF NOT EXISTS st_chatgpt_lookup ON st_chatgpt(run,node,slot);
 """
LABELS={
    'WEB_ENTRY_OK':'网页入口正常','HTTP_REACHED':'已收到响应，页面未确认',
    'AUTH_REQUIRED':'要求认证','CHALLENGE':'访问挑战','REGION_RESTRICTED':'明确提示地区限制',
    'RATE_LIMITED':'限流','SERVER_ERROR':'站点服务错误','FORBIDDEN':'拒绝访问，原因未明',
    'REDIRECT':'重定向','TLS_ERROR':'TLS 验证或握手失败','TIMEOUT':'超时',
    'TUNNEL_FAILED':'代理隧道失败','TRANSPORT_ERROR':'传输失败','UNKNOWN':'结果未知',
    'IN_PROGRESS':'检测中'}


def register_conditions(db,run):
    db.executescript(SCHEMA)
    with db:
        if 'tls_limit_s' not in {r[1] for r in db.execute('pragma table_info(st_chatgpt)')}:
            db.execute('alter table st_chatgpt add column tls_limit_s integer not null default 3')
        if not db.execute('select 1 from st_event where run=? and kind=? and json_extract(data,\'$.tls_s\')=?',
                          (run,CONDITION_EVENT,TLS_LIMIT_S)).fetchone():
            count,last=db.execute('select count(*),max(id) from st_chatgpt where run=? and tls_limit_s=3',(run,)).fetchone()
            change=dict(tls_s=TLS_LIMIT_S,total_s=TOTAL_LIMIT_S,legacy_tls_s=3,legacy_total_s=5,
                        legacy_rows=count,last_legacy_id=last,interval_s=INTERVAL,body_limit=BODY_LIMIT,
                        target='https://chatgpt.com/',reason='measure HTTPS responses after a 3–5 second TLS handshake')
            db.execute('insert into st_event values(?,?,?,?)',(run,time.time(),CONDITION_EVENT,json.dumps(change)))
        last=db.execute('select data from st_event where run=? and kind=? order by rowid desc limit 1',
                        (run,CADENCE_EVENT)).fetchone()
        settings=json.loads(last[0]) if last else {}
        previous=(settings.get('interval_s'),settings.get('global_spacing_s'))
        if previous!=(INTERVAL,GLOBAL_SPACING):
            count,boundary=db.execute('select count(*),max(id) from st_chatgpt where run=?',(run,)).fetchone()
            cadence=dict(interval_s=INTERVAL,global_spacing_s=GLOBAL_SPACING,
                previous_interval_s=(previous[0] if previous[0] is not None else 900) if count else None,
                previous_global_spacing_s=(previous[1] if previous[1] is not None else 15) if count else None,
                previous_rows=count,last_previous_id=boundary,tls_s=TLS_LIMIT_S,total_s=TOTAL_LIMIT_S,
                max_simultaneous=1,body_limit=BODY_LIMIT,reason='record ChatGPT sampling cadence')
            db.execute('insert into st_event values(?,?,?,?)',(run,time.time(),CADENCE_EVENT,json.dumps(cadence)))


def classify(code,headers,prefix):
    body=prefix.lower()
    if code>=400 and any(x in body for x in (b'unsupported_country_region_territory',
            b'unsupported_country',b'country, region, or territory not supported')):
        return 'REGION_RESTRICTED'
    if code==429:
        return 'RATE_LIMITED'
    if headers.get('cf-mitigated','').lower()=='challenge' or (code in (200,403,503) and
            (b'<title>just a moment' in body or b'/cdn-cgi/challenge-platform/' in body and b'<title>chatgpt' not in body)):
        return 'CHALLENGE'
    if code==401:
        return 'AUTH_REQUIRED'
    if code==403:
        return 'FORBIDDEN'
    if 300<=code<400:
        return 'REDIRECT'
    if code>=500:
        return 'SERVER_ERROR'
    if code==200 and 'text/html' in headers.get('content-type','').lower() and (
            re.search(br'<title\b[^>]{0,256}>\s*chatgpt(?:\s|</title>)',body) or b'property="og:site_name" content="chatgpt"' in body):
        return 'WEB_ENTRY_OK'
    return 'HTTP_REACHED'


async def read_headers(reader):
    raw=await reader.readuntil(b'\r\n\r\n')
    lines=raw.split(b'\r\n')
    code=int(lines[0].split()[1])
    headers={}
    for line in lines[1:]:
        key,sep,val=line.partition(b':')
        if sep:
            headers[key.decode('ascii','ignore').lower()]=val.decode('latin1').strip()
    return code,headers


async def probe(port,key,password):
    tick=time.monotonic()
    data={'target':'https://chatgpt.com/','start':time.time(),'tls':False,'http':None,
          'phase':'proxy','dns':'remote-resolution-unobserved','bytes_read':0,
          'tls_limit_s':TLS_LIMIT_S,'total_limit_s':TOTAL_LIMIT_S,
          'interval_s':INTERVAL,'global_spacing_s':GLOBAL_SPACING}
    w=None
    try:
        async with asyncio.timeout(TOTAL_LIMIT_S):
            r,w=await asyncio.open_connection('127.0.0.1',port,limit=32768)
            auth=base64.b64encode((key+':'+password).encode())
            w.write(b'CONNECT chatgpt.com:443 HTTP/1.1\r\nHost: chatgpt.com:443\r\nProxy-Authorization: Basic '+auth+b'\r\n\r\n')
            await w.drain()
            data['phase']='tunnel'
            tunnel,_=await read_headers(r)
            data['connect_status']=tunnel
            data['connect_ms']=round((time.monotonic()-tick)*1000,2)
            if tunnel!=200:
                data['status']='TUNNEL_FAILED'
                return data
            data['phase']='tls'
            context=ssl.create_default_context()
            handshake_start=time.monotonic()
            try:
                await w.start_tls(context,server_hostname=HOST,ssl_handshake_timeout=TLS_LIMIT_S)
            finally:
                data['handshake_ms']=(time.monotonic()-handshake_start)*1000
            data['tls']=True
            data['tls_version']=w.get_extra_info('ssl_object').version()
            data['tls_ready_ms']=round((time.monotonic()-tick)*1000,2)
            data['phase']='http'
            w.write(b'GET / HTTP/1.1\r\nHost: chatgpt.com\r\nAccept: text/html\r\nAccept-Encoding: identity\r\nUser-Agent: NodeStability/1.0\r\nConnection: close\r\n\r\n')
            await w.drain()
            code,headers=await read_headers(r)
            data['http']=code
            if code==429:
                retry=headers.get('retry-after','')
                try:
                    wait=int(retry) if retry.isdigit() else parsedate_to_datetime(retry).timestamp()-time.time()
                except (ValueError,TypeError,OverflowError):
                    wait=1800
                data['retry_after_s']=min(259200,max(1800,round(wait)))
            data['headers_ms']=round((time.monotonic()-tick)*1000,2)
            data['type']=headers.get('content-type','')[:80]
            data['cf_challenge']=headers.get('cf-mitigated','').lower()=='challenge'
            # Read a short prefix including possible chunk framing, never store the body or cookies.
            length=headers.get('content-length','')
            limit=min(BODY_LIMIT,int(length)) if length.isdigit() else BODY_LIMIT
            prefix=bytearray()
            while len(prefix)<limit:
                part=await r.read(limit-len(prefix))
                if not part:
                    break
                prefix.extend(part)
            data['bytes_read']=len(prefix)
            data['status']=classify(code,headers,bytes(prefix))
            data['phase']='complete'
    except TimeoutError:
        data['status']='TIMEOUT'
        data['timeout_reason']='overall deadline'
    except ssl.SSLError as e:
        data.update(status='TLS_ERROR',error=type(e).__name__)
    except (OSError,ValueError,IndexError,asyncio.IncompleteReadError,asyncio.LimitOverrunError) as e:
        data.update(status='TRANSPORT_ERROR',error=type(e).__name__)
        if data['phase']=='tls' and isinstance(e,ConnectionAbortedError) and 'SSL handshake is taking longer than' in str(e):
            data.update(status='TIMEOUT',timeout_reason='TLS handshake deadline')
    finally:
        data.update(end=time.time(),elapsed=round((time.monotonic()-tick)*1000,3))
        if w and w.transport:
            w.transport.abort()
    return data
