"""Offline native acceptance. Both simulated exits and HTTP targets terminate on loopback."""
import asyncio
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from stability_core import Sidecar,project_nodes


@unittest.skipUnless(os.name=='nt','requires installed Windows Verge core')
class Native(unittest.IsolatedAsyncioTestCase):
    async def test_provider_aliases_status_and_exit_selection(self):
        from functools import partial
        import aiohttp
        paths=[[],[]]
        async def serve(i,r,w):
            try:
                first=await asyncio.wait_for(r.readuntil(b'\r\n\r\n'),3)
                if first.startswith(b'CONNECT '):
                    w.write(b'HTTP/1.1 200 Connection established\r\n\r\n')
                    await w.drain()
                    first=await asyncio.wait_for(r.readuntil(b'\r\n\r\n'),3)
                paths[i].append(first.splitlines()[0])
                status=b'204 No Content' if i==0 else b'503 Unavailable'
                w.write(b'HTTP/1.1 '+status+b'\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
                await w.drain()
            except (OSError,TimeoutError,asyncio.IncompleteReadError):
                pass
            finally:
                w.close()
                await w.wait_closed()
        servers=[]
        nodes=[]
        core=None
        try:
            for i in range(2):
                srv=await asyncio.start_server(partial(serve,i),'127.0.0.1',0)
                servers.append(srv)
                row=dict(name='同名 / #% 节点',type='http',server='127.0.0.1',port=srv.sockets[0].getsockname()[1])
                nodes.extend(project_nodes('Provider '+str(i),[row],[row],b'secret'))
            core=Sidecar(nodes,'Loopback Pseudo-Interface 1')
            await core.start()
            # TEST-NET destination is intercepted by our two mock HTTP proxies.
            with patch('stability_core.TARGETS',('http://192.0.2.1/test','http://192.0.2.2/test')):
                ok=await core.probe(nodes[0].key,0)
                mismatch=await core.probe(nodes[1].key,0)
                self.assertEqual(ok[0],'SUCCESS')
                self.assertEqual(mismatch[0],'UNKNOWN_ERROR')
            for i,n in enumerate(nodes):
                async with core.session.get('http://192.0.2.1/special',
                    proxy=f'http://127.0.0.1:{core.mixed}',
                    proxy_auth=aiohttp.BasicAuth(n.key,core.password)) as res:
                    self.assertEqual(res.status,(204,503)[i])
            self.assertTrue(all(len(calls)==2 for calls in paths))
            self.assertTrue(all(b'/special' in calls[1] for calls in paths))
        finally:
            if core:
                await core.close()
            for srv in servers:
                srv.close()
                await srv.wait_closed()
