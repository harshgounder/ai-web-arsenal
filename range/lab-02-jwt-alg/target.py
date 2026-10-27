#!/usr/bin/env python3
"""
lab-02 target: a JWT verifier that trusts the algorithm the token declares.

The bug is the one in the identity lens: the verifier reads `alg` from the token header and dispatches on
it. When the header says "none", it accepts an unsigned token. When it says "HS256" while the application
issued RS256, it verifies with the public key as an HMAC secret, which the attacker also has.

Run: python3 range/lab-02-jwt-alg/target.py [port]
"""
import base64
import hashlib
import hmac
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# The server's HMAC secret. In the real version of this bug the attacker never sees it, because they
# confuse the verifier into using the public key instead. Here the point is the dispatch, so the
# algorithm confusion is shown in its simpler form: the header chooses the check.
SECRET = b"lab-only-secret-not-a-real-one"


def b64e(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def b64d(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def issue(role="user"):
    header = b64e(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = b64e(json.dumps({"sub": "alice", "role": role}).encode())
    sig = b64e(hmac.new(SECRET, f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{sig}"


def verify(token):
    """The defect: dispatch on the caller's declared algorithm."""
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError:
        return None, "malformed"
    try:
        header = json.loads(b64d(header_b64))
        payload = json.loads(b64d(payload_b64))
    except Exception:
        return None, "undecodable"

    alg = header.get("alg")
    if alg == "none":
        # no signature required
        return payload, None
    if alg == "HS256":
        expect = b64e(hmac.new(SECRET, f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).digest())
        if hmac.compare_digest(expect, sig_b64):
            return payload, None
        return None, "bad signature"
    return None, f"unsupported alg {alg}"


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
        if self.path == "/token":
            return self._json(200, {"token": issue("user")})
        if self.path == "/admin":
            auth = self.headers.get("Authorization") or ""
            if not auth.startswith("Bearer "):
                return self._json(401, {"error": "no token"})
            payload, err = verify(auth[7:])
            if err:
                return self._json(401, {"error": err})
            if payload.get("role") != "admin":
                return self._json(403, {"error": "not admin", "role": payload.get("role")})
            return self._json(200, {"flag": "admin panel", "sub": payload.get("sub")})
        return self._json(404, {"error": "not found"})


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8732
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"listening on 127.0.0.1:{port}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
