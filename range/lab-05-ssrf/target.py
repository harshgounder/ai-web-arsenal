#!/usr/bin/env python3
"""
lab-05 target: a fetch endpoint with a filter that looks reasonable and is not.

The application accepts a URL and fetches it, because a feature needs to preview links. The filter
blocks the cloud metadata address and requires http or https. It does not block loopback, which is the
only thing that matters here, because a loopback address reaches every internal service that never
expected to be reachable from outside.

Two servers in one process: an internal service on port+1 holding a secret, and the app on port.

Run: python3 range/lab-05-ssrf/target.py [port]
"""
import json
import sys
import threading
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SECRET = "internal-only-credential-lab05"
BLOCKED_HOSTS = ("169.254.169.254", "metadata.google.internal")


class Internal(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/secret":
            body = json.dumps({"token": SECRET, "service": "inventory"}).encode()
            self.send_response(200)
        else:
            body = b'{"error":"no such internal route"}'
            self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class App(BaseHTTPRequestHandler):
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
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/fetch":
            return self._json(404, {"error": "not found"})
        qs = urllib.parse.parse_qs(parsed.query)
        target = (qs.get("url") or [""])[0]
        if not target:
            return self._json(400, {"error": "url required"})

        # The filter. It blocks the metadata address the vendor warned about, and nothing else.
        if any(h in target for h in BLOCKED_HOSTS):
            return self._json(403, {"error": "target not permitted"})
        if not target.startswith(("http://", "https://")):
            return self._json(403, {"error": "only http and https"})

        try:
            with urllib.request.urlopen(target, timeout=5) as r:
                payload = r.read(4096).decode(errors="replace")
                return self._json(200, {"fetched": target, "body": payload})
        except Exception as e:
            return self._json(502, {"error": type(e).__name__, "target": target})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8735
    internal_port = port + 1
    threading.Thread(
        target=ThreadingHTTPServer(("127.0.0.1", internal_port), Internal).serve_forever,
        daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", port), App)
    print(f"app on 127.0.0.1:{port}, internal on 127.0.0.1:{internal_port}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
