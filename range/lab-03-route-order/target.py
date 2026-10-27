#!/usr/bin/env python3
"""
lab-03 target: a router that decodes after the guard has already decided.

The guard matches the raw request path against the protected prefix. The router then unquotes and
lowercases before dispatch. Two spellings therefore slip past the guard and still reach the handler:
a percent-encoded path, and a differently cased one.

Run: python3 range/lab-03-route-order/target.py [port]
"""
import json
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KEY = "lab-admin-key"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def _json(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        raw = self.path.split("?")[0]

        # guard: decided on the raw path, before any normalisation
        if raw.startswith("/admin") and self.headers.get("X-Key") != KEY:
            return self._json(401, {"error": "admin requires a key"})

        # router: normalises, then matches
        path = urllib.parse.unquote(raw).lower()

        if path == "/admin":
            return self._json(200, {"page": "admin", "secret": "admin panel reached without a key"})
        if path == "/public":
            return self._json(200, {"page": "public"})
        if path == "/health":
            return self._json(200, {"ok": True})
        return self._json(404, {"error": "no route", "path": path})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8733
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"listening on 127.0.0.1:{port}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
