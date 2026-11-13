"""One bounded download and two reuses of the original TLS connection."""
import base64
import http.client
import ssl
import time


def small_transfer(port, alias, password):
    host = 'speed.cloudflare.com'
    auth = base64.b64encode(f'{alias}:{password}'.encode()).decode()
    conn = http.client.HTTPSConnection('127.0.0.1',port,timeout=4,context=ssl.create_default_context())
    conn.set_tunnel(host,443,{'Proxy-Authorization':'Basic '+auth})
    record = {'target':host,'path':'/__down?bytes=16384','bytes':0,'reuse':[],'checks':[]}
    try:
        record['connect_start']=time.time()
        conn.connect()
        record['connect_end']=time.time()
        sock = conn.sock
        start = time.perf_counter()
        record['get_start']=time.time()
        conn.request('GET','/__down?bytes=16384',headers={'Accept-Encoding':'identity'})
        response = conn.getresponse()
        record['status'] = response.status
        data = response.read(16385)
        elapsed = time.perf_counter()-start
        record.update(bytes=len(data),seconds=elapsed,get_end=time.time())
        if response.status!=200 or len(data)!=16384:
            return record
        record['small_request_Bps'] = round(len(data)/elapsed)
        for _ in range(2):
            time.sleep(5)
            check={'start':time.time(),'path':'/__down?bytes=1','attempted':False}
            record['checks'].append(check)
            if conn.sock is not sock:
                record['reuse'].append(False)
                check.update(end=time.time(),outcome='connection-closed')
                break
            check['attempted']=True
            conn.request('HEAD','/__down?bytes=1')
            res = conn.getresponse()
            res.read(1)
            record['reuse'].append(res.status==200 and conn.sock is sock)
            check.update(end=time.time(),status=res.status,same_socket=conn.sock is sock)
        return record
    except (OSError,http.client.HTTPException) as e:
        record['error'] = type(e).__name__
        if record['checks'] and 'end' not in record['checks'][-1]:
            record['checks'][-1].update(end=time.time(),outcome=type(e).__name__)
            record['reuse'].append(False)
        return record
    finally:
        conn.close()
