#!/usr/bin/env python3
"""Serves timesheets.html and keeps its entries in data/store.json.

Python standard library only. Run:  python3 server.py [--host 127.0.0.1] [--port 8077]
"""
import argparse
import json
import os
import re
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, 'timesheets.html')
DATA_DIR = os.path.join(HERE, 'data')
STORE = os.path.join(DATA_DIR, 'store.json')
KEY_RE = re.compile(r'^fmrsd-[A-Za-z0-9:._-]{1,80}$')
MAX_BODY = 1 << 20

lock = threading.Lock()


def read_store():
    try:
        with open(STORE, encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def write_store(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    # Keep one copy of the store as it was at the first change of each day.
    backup = os.path.join(DATA_DIR, f'store-{date.today():%Y%m%d}.json')
    if os.path.exists(STORE) and not os.path.exists(backup):
        os.link(STORE, backup)
    tmp = STORE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, STORE)


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body=b'', ctype='application/json'):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def key(self):
        m = re.match(r'^/api/store/(.+)$', self.path)
        k = unquote(m.group(1)) if m else ''
        return k if KEY_RE.match(k) else None

    def do_GET(self):
        if self.path in ('/', '/index.html') or self.path.startswith(('/?', '/#')):
            with open(PAGE, 'rb') as f:
                self.send(200, f.read(), 'text/html; charset=utf-8')
        elif self.path == '/api/store':
            with lock:
                self.send(200, json.dumps(read_store()).encode())
        else:
            self.send(404, b'{"error":"not found"}')

    def do_PUT(self):
        k = self.key()
        n = int(self.headers.get('Content-Length') or 0)
        if not k or n > MAX_BODY:
            return self.send(400, b'{"error":"bad key or body"}')
        try:
            value = json.loads(self.rfile.read(n))
        except ValueError:
            return self.send(400, b'{"error":"bad json"}')
        with lock:
            data = read_store()
            data[k] = value
            write_store(data)
        self.send(200, b'{"ok":true}')

    def do_DELETE(self):
        k = self.key()
        if not k:
            return self.send(400, b'{"error":"bad key"}')
        with lock:
            data = read_store()
            if data.pop(k, None) is not None:
                write_store(data)
        self.send(200, b'{"ok":true}')

    def log_message(self, fmt, *args):
        if self.command != 'GET':
            super().log_message(fmt, *args)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--port', type=int, default=8077)
    a = p.parse_args()
    print(f'Serving on http://{a.host}:{a.port}', flush=True)
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()
