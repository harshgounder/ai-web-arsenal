#!/usr/bin/env python3
"""
lab-06 target: an object endpoint that authenticates and does not authorise.

The endpoint requires a valid token, which is why it looks protected. It then looks the object up by the
identifier in the path and returns it, without ever asking whether the caller owns it. Authentication is
checked once at the edge and ownership is never checked at all.

Run: python3 range/lab-06-idor/target.py [port]
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKENS = {"alice-token": "alice", "bob-token": "bob"}
OBJECTS = {
    1: {"id": 1, "owner": "alice", "body": "alice private note: lab06-alpha"},
    2: {"id": 2, "owner": "bob", "body": "bob private note: lab06-beta"},
    3: {"id": 3, "owner": "alice", "body": "alice second note: lab06-gamma"},
}


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
        if not self.path.startswith("/object/"):
            return self._json(404, {"error": "not found"})

        auth = self.headers.get("Authorization") or ""
        token = auth[7:] if auth.startswith("Bearer ") else ""
        user = TOKENS.get(token)
        if not user:
            return self._json(401, {"error": "a valid token is required"})

        try:
            oid = int(self.path.rsplit("/", 1)[1])
        except ValueError:
            return self._json(400, {"error": "id must be an integer"})

        obj = OBJECTS.get(oid)
        if not obj:
            return self._json(404, {"error": "no such object"})

        # The defect: the caller's identity is never compared to obj["owner"].
        return self._json(200, {"object": obj, "served_to": user})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8736
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"listening on 127.0.0.1:{port}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
