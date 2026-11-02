#!/usr/bin/env python3
"""Local-only Radarr SignalR failure probe; no Bazarr configuration is loaded.
Run each scenario in its own process: retry threads in the original are daemon
threads and intentionally survive stop(). Uses the checkout's bundled libraries.
"""
import argparse, ast, base64, hashlib, json, logging, os, pathlib, socket
import struct, sys, threading, time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace as NS

p = argparse.ArgumentParser()
p.add_argument('--repo', default=str(pathlib.Path(__file__).resolve().parents[3]))
p.add_argument('--mode', choices=['outage', 'flap', 'cold', 'refused'], default='outage')
p.add_argument('--duration', type=float, default=8)
p.add_argument('--real-time', action='store_true')
a = p.parse_args()
repo = pathlib.Path(a.repo)
sys.path[:0] = [str(repo/'custom_libs'), str(repo/'libs')]
from signalrcore.hub_connection_builder import HubConnectionBuilder
from requests.exceptions import ConnectionError
logging.disable(logging.CRITICAL)
opened = threading.Event()
recover = threading.Event()
stats = {'negotiate': 0, 'upgrades': 0, 'connected': 0, 'reconnect_callbacks': 0}

class Endpoint(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_POST(self):
        stats['negotiate'] += 1
        self.rfile.read(int(self.headers.get('Content-Length', 0)))
        if a.mode == 'cold':
            self.connection.shutdown(socket.SHUT_RDWR)
            self.close_connection = True
            return
        if (a.mode in ('outage', 'refused') and opened.is_set() and not recover.is_set()):
            self.send_error(503); return
        body = json.dumps({'connectionId': 'local-test', 'availableTransports': [
            {'transport': 'WebSockets', 'transferFormats': ['Text']}]}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        key = self.headers['Sec-WebSocket-Key']
        digest = base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode()
        self.send_response(101)
        self.send_header('Upgrade', 'websocket')
        self.send_header('Connection', 'Upgrade')
        self.send_header('Sec-WebSocket-Accept', digest)
        self.end_headers()
        self.connection.settimeout(2)
        # Read masked client handshake frame (small JSON payload).
        header = self.rfile.read(2)
        if len(header) != 2: return
        size = header[1] & 127
        if size == 126: size = struct.unpack('!H', self.rfile.read(2))[0]
        self.rfile.read(4); self.rfile.read(size)
        self.wfile.write(b'\x81\x03{}\x1e'); self.wfile.flush()
        stats['upgrades'] += 1
        opened.set()
        if recover.is_set():
            try:
                while self.rfile.read(1): pass
            except (OSError, TimeoutError): pass
        else:
            time.sleep(.03 if not a.real_time else .2)
        # Abrupt TCP disconnect, as on a stopped server.
        try: self.connection.shutdown(socket.SHUT_RDWR)
        except OSError: pass

server = ThreadingHTTPServer(('127.0.0.1', 0), Endpoint)
server.daemon_threads = True
threading.Thread(target=server.serve_forever, daemon=True, name='mock-radarr').start()
# Extract the actual class to isolate unrelated DB/scheduler/config imports.
tree = ast.parse((repo/'bazarr/app/signalr_client.py').read_text())
node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'RadarrSignalrClient')
settings = NS(general=NS(use_radarr=True), radarr=NS(apikey='test', movies_sync_on_live=False))
ns = dict(logging=logging, time=time, ConnectionError=ConnectionError, HubConnectionBuilder=HubConnectionBuilder,
          settings=settings, HEADERS={}, headers={}, url_radarr=lambda: f'http://127.0.0.1:{server.server_port}',
          args=NS(dev=True, no_signalr=False), event_stream=lambda **kw: None, radarr_queue=deque(), feed_queue=lambda *args: None)
exec(compile(ast.Module(body=[node], type_ignores=[]), str(repo/'bazarr/app/signalr_client.py'), 'exec'), ns)
client = ns['RadarrSignalrClient']()
client.configure()
t = client.connection.transport
if not a.real_time:
    t.connection_checker.sleep = .05
    t.connection_checker.keep_alive_interval = .05
    t.reconnection_handler.sleep_time = .3
# Use the configured real Radarr callbacks, counting their invocations.
original_open, original_reconnect = t._on_open, t._on_reconnect
def on_open():
    stats['connected'] += 1
    original_open()
def on_reconnect():
    stats['reconnect_callbacks'] += 1
    original_reconnect()
t._on_open, t._on_reconnect = on_open, on_reconnect

def snapshot(label):
    status = pathlib.Path('/proc/self/status').read_text().splitlines()
    values = {k: next(line.split(':',1)[1].strip() for line in status if line.startswith(k+':'))
              for k in ('Threads','VmRSS','VmSize')}
    targets = [getattr(th, '_target', None) for th in threading.enumerate()]
    values.update(label=label, seconds=round(time.monotonic()-begin, 3),
                  fd=len(os.listdir('/proc/self/fd')),
                  retry_threads=sum(getattr(fn, '__name__', '') == 'deferred_reconnect' for fn in targets),
                  checker_threads=sum(getattr(fn, '__name__', '') == 'run' and getattr(fn, '__self__', None) is t.connection_checker for fn in targets),
                  children='unavailable: proc children not exposed',
                  cpu_seconds=round(time.process_time(), 4), **stats)
    print(json.dumps(values), flush=True)

begin = time.monotonic()
snapshot('baseline')
# Cold-start retry uses Bazarr's actual start loop, sped up only for this scenario.
if a.mode == 'cold':
    client.configure = lambda: None
    if not a.real_time:
        ns['time'] = NS(sleep=lambda _: time.sleep(.05))
    threading.Thread(target=client.start, daemon=True).start()
else:
    client.connection.start()
    if a.mode == 'refused':
        if not opened.wait(3): raise RuntimeError('handshake failed')
        server.shutdown(); server.server_close()
for second in range(int(a.duration)):
    time.sleep(1)
    snapshot('outage')
    if threading.active_count() > 180:
        raise RuntimeError('safety cap reached')
if a.mode != 'cold':
    if a.mode != 'refused':
        recover.set()
        time.sleep(1 if not a.real_time else 7)
        snapshot('recovery')
    client.stop()
    time.sleep(.7 if not a.real_time else 2)
    snapshot('after_stop')
# Explicitly stop the checker for test process teardown even on unpatched code.
t.connection_checker.running = False
