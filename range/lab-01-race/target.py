#!/usr/bin/env python3
"""
lab-01 target: a signup endpoint whose uniqueness check is not atomic.

This is deliberately small and deliberately vulnerable. It exists so that one factor in Set D can move
from L2 (a procedure someone wrote down) to L3 (a procedure run here, with a negative control).

The bug is the one in atlas pattern W01-0001: the application checks whether an email exists, then
inserts. Between those two steps another request can do the same. There is no unique constraint in the
store, because the developer trusted the check.

Run: python3 range/lab-01-race/target.py [port]
"""
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# The window between check and insert, in seconds. Real applications have this window for free, from
# network latency, a database round trip, or a queue. Making it visible here is the whole point.
WINDOW = 0.05

_lock = threading.Lock()
_records = []
_emails = set()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass  # quiet

    def _json(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/signup":
            return self._json(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            return self._json(400, {"error": "bad json"})
        email = (body.get("email") or "").strip().lower()
        if not email:
            return self._json(400, {"error": "email required"})

        # check
        with _lock:
            exists = email in _emails
        if exists:
            return self._json(409, {"error": "already registered"})

        # the window the attacker needs
        time.sleep(WINDOW)

        # insert
        with _lock:
            _emails.add(email)
            _records.append({"email": email})
        return self._json(201, {"created": email})

    def do_GET(self):
        if self.path != "/count":
            return self._json(404, {"error": "not found"})
        with _lock:
            n = len(_records)
        return self._json(200, {"records": n})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8731
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"listening on 127.0.0.1:{port}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
