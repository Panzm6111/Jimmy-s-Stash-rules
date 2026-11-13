"""Read-only local Mihomo HTTP over Windows named pipes, with cancellable I/O.

Never opens a TCP controller or writes core configuration. Secrets stay in memory.
"""
import ctypes
import http.client
import io
import json
import os
import threading
import time
from pathlib import Path

import yaml

ROOT = Path(os.environ.get('APPDATA', '.')) / 'io.github.clash-verge-rev.clash-verge-rev'


class PipeRaw(io.RawIOBase):
    def __init__(self, path, timeout=5, stop=None):
        super().__init__()
        from ctypes import wintypes as w
        self.w = w
        self.k = ctypes.WinDLL('kernel32', use_last_error=True)
        class OVERLAPPED(ctypes.Structure):
            _fields_ = [('Internal', ctypes.c_size_t), ('InternalHigh', ctypes.c_size_t),
                        ('Offset', w.DWORD), ('OffsetHigh', w.DWORD), ('hEvent', w.HANDLE)]
        self.OVERLAPPED = OVERLAPPED
        self.k.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, ctypes.c_void_p,
                                      w.DWORD, w.DWORD, w.HANDLE]
        self.k.CreateFileW.restype = w.HANDLE
        self.k.CreateEventW.argtypes = [ctypes.c_void_p, w.BOOL, w.BOOL, w.LPCWSTR]
        self.k.CreateEventW.restype = w.HANDLE
        self.k.ReadFile.argtypes = [w.HANDLE, ctypes.c_void_p, w.DWORD,
                                   ctypes.POINTER(w.DWORD), ctypes.POINTER(OVERLAPPED)]
        self.k.WriteFile.argtypes = self.k.ReadFile.argtypes
        self.k.GetOverlappedResult.argtypes = [w.HANDLE, ctypes.POINTER(OVERLAPPED),
                                             ctypes.POINTER(w.DWORD), w.BOOL]
        self.k.CancelIoEx.argtypes = [w.HANDLE, ctypes.POINTER(OVERLAPPED)]
        self.k.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
        self.k.CloseHandle.argtypes = [w.HANDLE]
        self.k.WaitNamedPipeW.argtypes = [w.LPCWSTR, w.DWORD]
        for attempt in range(5):
            self.handle = self.k.CreateFileW(path, 0xC0000000, 0, None, 3, 0x40000000, None)
            if self.handle != ctypes.c_void_p(-1).value or ctypes.get_last_error()!=231:break
            self.k.WaitNamedPipeW(path,250)
        if self.handle == ctypes.c_void_p(-1).value:
            raise OSError(ctypes.get_last_error(), 'Core pipe unavailable')
        self.timeout, self.stop = timeout, stop or threading.Event()

    def _io(self, buffer, count, write=False):
        n = self.w.DWORD()
        ov = self.OVERLAPPED()
        ov.hEvent = self.k.CreateEventW(None, True, False, None)
        if not ov.hEvent:
            raise OSError('Cannot allocate I/O event')
        try:
            call = self.k.WriteFile if write else self.k.ReadFile
            ok = call(self.handle, buffer, count, ctypes.byref(n), ctypes.byref(ov))
            if not ok:
                error = ctypes.get_last_error()
                if error in (109, 232):
                    return 0
                if error != 997:
                    raise OSError(error, 'Core pipe I/O failed')
                deadline = time.monotonic() + self.timeout
                while self.k.WaitForSingleObject(ov.hEvent, 250) != 0:
                    if self.stop.is_set() or time.monotonic() >= deadline:
                        self.k.CancelIoEx(self.handle, ctypes.byref(ov))
                        self.k.GetOverlappedResult(self.handle, ctypes.byref(ov), ctypes.byref(n), True)
                        raise TimeoutError('Core I/O cancelled or timed out')
                if not self.k.GetOverlappedResult(self.handle, ctypes.byref(ov), ctypes.byref(n), False):
                    if ctypes.get_last_error() in (109, 232):
                        return 0
                    raise OSError(ctypes.get_last_error(), 'Core pipe result failed')
            return n.value
        finally:
            self.k.CloseHandle(ov.hEvent)

    def readable(self): return True

    def readinto(self, b):
        if self.closed:
            return 0
        view = (ctypes.c_char * len(b)).from_buffer(b)
        return self._io(view, len(b))

    def send(self, data):
        offset = 0
        while offset < len(data):
            block = ctypes.create_string_buffer(data[offset:])
            n = self._io(block, len(data) - offset, True)
            if not n:
                raise OSError('Core pipe closed while writing')
            offset += n

    def close(self):
        if not self.closed:
            self.k.CloseHandle(self.handle)
        super().close()


class PipeSocket:
    def __init__(self, raw): self.raw = raw
    def makefile(self, *args): return io.BufferedReader(self.raw)


class CoreClient:
    def __init__(self, root=ROOT, stop=None):
        self.root, self.stop = Path(root), stop or threading.Event()
        self._credential_cache = None

    def identity(self):
        pipes = [p for p in os.listdir('\\\\.\\pipe\\') if p.startswith('verge-mihomo-production-')]
        if len(pipes) != 1:
            raise OSError('Expected one production core')
        return pipes[0]

    def response(self, endpoint, timeout=5):
        if not endpoint.startswith('/') or any(c in endpoint for c in '\r\n '):
            raise ValueError('Invalid read endpoint')
        path = self.root / 'clash-verge.yaml'
        stamp = path.stat().st_mtime_ns
        cached = self._credential_cache
        if cached is None or cached[0] != stamp:
            config = yaml.safe_load(path.read_text(encoding='utf-8'))
            cached = (stamp, config.get('secret', ''))
            self._credential_cache = cached
        raw = PipeRaw('\\\\.\\pipe\\' + self.identity(), timeout, self.stop)
        try:
            secret = cached[1]
            if any(c in secret for c in '\r\n'):
                raise ValueError('Invalid controller credential')
            raw.send(('GET ' + endpoint + ' HTTP/1.1\r\nHost: localhost\r\n'
                      'Authorization: Bearer ' + secret + '\r\nConnection: close\r\n\r\n').encode())
            response = http.client.HTTPResponse(PipeSocket(raw))
            response.begin()
            if response.status != 200:
                status=response.status;response.close()
                raise OSError('Core read rejected: ' + str(status))
            return response
        except Exception:
            raw.close()
            raise

    def get(self, endpoint):
        with self.response(endpoint) as response:
            data = response.read(16 * 1024 * 1024 + 1)
            if len(data) > 16 * 1024 * 1024:
                raise ValueError('Core response exceeds read limit')
            return json.loads(data)

    def logs(self):
        with self.response('/logs?level=info', timeout=45) as response:
            while not self.stop.is_set():
                line = response.readline(128 * 1024)
                if not line:
                    return
                try:
                    yield json.loads(line)
                except (ValueError, UnicodeError):
                    continue
