#!/usr/bin/env python3
"""
lab-04 target: a cache that keys on the path, in front of an origin that reflects a header.

The origin puts the X-Forwarded-Host value into the page, because the application uses it to build
absolute links. The cache in front stores the response by path only. One request with a hostile header
therefore poisons the page for everyone who asks for that path next.

Two servers, one process: the origin on port+1 and the cache on port. Run:
  python3 range/lab-04-cache-poison/target.py [port]
"""
import json
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Origin(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def do_GET(self):
        # The vulnerable pattern: a client controlled header is reflected into the body.
        host = self.headers.get("X-Forwarded-Host") or "origin.local"
        if self.path == "/page":
            body = f'<html><body><a href="https://{host}/login">Sign in</a></body></html>'.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Cache-Control", "public, max-age=60")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/nostore":
            body = f'<html><body>session for {host}</body></html>'.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.send_header("Content-Length", "0")
        self.end_headers()


class Cache(BaseHTTPRequestHandler):
    """A shared cache keyed on path alone. Deliberately naive, which is the defect."""
    protocol_version = "HTTP/1.1"
    store = {}
    origin = None

    def log_message(self, *args):
        pass

    def _serve(self, body, status=200, hdr=None):
        self.send_response(status)
        for k, v in (hdr or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        key = self.path.split("?")[0]
        hit = self.store.get(key)
        if hit and time.time() - hit["at"] < 60:
            self._serve(hit["body"], hdr={"X-Cache": "HIT", "Content-Type": "text/html"})
            return

        req = urllib.request.Request(self.origin + self.path)
        # the unkeyed input: forwarded straight through, and not part of the cache key
        for h in ("X-Forwarded-Host",):
            if self.headers.get(h):
                req.add_header(h, self.headers.get(h))
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                body = r.read()
                cc = r.headers.get("Cache-Control") or ""
                status = r.status
        except Exception:
            return self._serve(b"origin error", 502)

        if status == 200 and "no-store" not in cc and "public" in cc:
            self.store[key] = {"body": body, "at": time.time()}
        self._serve(body, status, hdr={"X-Cache": "MISS", "Content-Type": "text/html"})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8734
    origin_port = port + 1

    Cache.origin = f"http://127.0.0.1:{origin_port}"
    threading.Thread(
        target=ThreadingHTTPServer(("127.0.0.1", origin_port), Origin).serve_forever,
        daemon=True).start()

    srv = ThreadingHTTPServer(("127.0.0.1", port), Cache)
    print(f"cache on 127.0.0.1:{port}, origin on 127.0.0.1:{origin_port}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
