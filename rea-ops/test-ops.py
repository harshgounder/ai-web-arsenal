#!/usr/bin/env python3
"""
test-ops.py: build fixtures for the REA operations and test them against those fixtures.

An operation with no fixture is a claim. Both operations here are tested against files this script
generates, so the test does not depend on any download and cannot drift with a remote sample.

Run: python3 rea-ops/test-ops.py
"""
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")


def make_warc(path, records):
    """Write a minimal but valid WARC 1.0 with the given (uri, body_html, status) tuples."""
    chunks = []
    for i, (uri, body, status) in enumerate(records):
        payload = body.encode()
        http = (f"HTTP/1.1 {status} OK\r\nContent-Type: text/html\r\n"
                f"Content-Length: {len(payload)}\r\n\r\n").encode() + payload
        head = (
            "WARC/1.0\r\n"
            f"WARC-Type: response\r\n"
            f"WARC-Target-URI: {uri}\r\n"
            f"WARC-Date: 2026-10-27T00:00:0{i}Z\r\n"
            f"WARC-Record-ID: <urn:uuid:00000000-0000-0000-0000-00000000000{i}>\r\n"
            "Content-Type: application/http; msgtype=response\r\n"
            f"Content-Length: {len(http)}\r\n"
            "\r\n"
        ).encode()
        chunks.append(head + http + b"\r\n\r\n")
    path.write_bytes(b"".join(chunks))


def make_wxapkg(path, files):
    """Write a wxapkg that follows the layout the reader implements."""
    index = struct.pack("<I", len(files))
    blobs = b""
    for name, data in files:
        nb = name.encode()
        index += struct.pack("<I", len(nb)) + nb + struct.pack("<II", len(blobs), len(data))
        blobs += data
    header = struct.pack("<III", 0xBE, 0, len(index))
    path.write_bytes(header + index + blobs)


def parse_json(out):
    try:
        return json.loads(out)
    except Exception:
        return {}


def run(args):
    r = subprocess.run([sys.executable] + args, capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout, r.stderr


def test_warc(tmp):
    warc = tmp / "test.warc"
    make_warc(warc, [
        ("https://example.com/", "<html><body>one</body></html>", 200),
        ("https://example.com/login", "<html><body>two</body></html>", 200),
        ("https://example.com/missing", "not found", 404),
    ])
    rc, out, err = run([str(HERE / "warc.py"), str(warc)])
    check("warc: exits 0 on a valid archive", rc == 0, err[:80])
    rows = [json.loads(l) for l in out.splitlines() if l.strip()]
    check("warc: three response records", len(rows) == 3, f"got {len(rows)}")
    check("warc: target uri parsed", rows[0]["target_uri"] == "https://example.com/")
    check("warc: http status parsed", [r["http_status"] for r in rows] == [200, 200, 404])
    check("warc: body not emitted without --with-body", "content" not in rows[0])

    rc, out, _ = run([str(HERE / "warc.py"), str(warc), "--summary"])
    s = json.loads(out)
    check("warc: summary counts three responses", s["by_type"].get("response") == 3)
    check("warc: summary groups by host", s["hosts"].get("example.com") == 3)

    rc, out, _ = run([str(HERE / "warc.py"), str(warc), "--url", "login", "--with-body"])
    one = [json.loads(l) for l in out.splitlines() if l.strip()]
    check("warc: url filter and body work", len(one) == 1 and "two" in one[0]["content"])

    # a gzip wrapped warc must read the same
    import gzip
    gz = tmp / "test.warc.gz"
    gz.write_bytes(gzip.compress(warc.read_bytes()))
    rc, out, _ = run([str(HERE / "warc.py"), str(gz)])
    check("warc: gzip archive reads identically", rc == 0 and len(out.strip().splitlines()) == 3)

    # a file that is not a warc must fail with a reason, not an empty success
    junk = tmp / "junk.bin"
    junk.write_bytes(b"not a warc at all")
    rc, out, err = run([str(HERE / "warc.py"), str(junk)])
    check("warc: rejects a non-archive with a reason", rc == 1 and "no WARC records" in err)


def test_wxapkg(tmp):
    pkg = tmp / "app.wxapkg"
    make_wxapkg(pkg, [
        ("app.js", b"console.log('hi')"),
        ("pages/index/index.wxml", b"<view>hello</view>"),
        ("assets/a.bin", bytes(range(32))),
    ])
    rc, out, err = run([str(HERE / "wxapkg.py"), str(pkg), "--list"])
    check("wxapkg: lists entries", rc == 0 and len(parse_json(out).get("entries", [])) == 3, err[:80])

    outdir = tmp / "unpacked"
    rc, out, err = run([str(HERE / "wxapkg.py"), str(pkg), "--out", str(outdir)])
    got = parse_json(out)
    check("wxapkg: extracts every entry", rc == 0 and got["extracted"] == 3)
    check("wxapkg: preserves content",
          (outdir / "app.js").read_bytes() == b"console.log('hi')")
    check("wxapkg: preserves nested path",
          (outdir / "pages/index/index.wxml").read_bytes() == b"<view>hello</view>")
    check("wxapkg: binary content intact",
          (outdir / "assets/a.bin").read_bytes() == bytes(range(32)))

    # a traversal name must be refused, not written outside the target
    evil = tmp / "evil.wxapkg"
    make_wxapkg(evil, [("../../escaped.txt", b"should not land")])
    rc, out, _ = run([str(HERE / "wxapkg.py"), str(evil), "--out", str(tmp / "evil-out")])
    got = parse_json(out)
    check("wxapkg: refuses a traversal name", got["extracted"] == 0 and got["skipped"])
    check("wxapkg: nothing escaped the target", not (tmp / "escaped.txt").exists())

    # a truncated file must fail with a reason
    trunc = tmp / "trunc.wxapkg"
    trunc.write_bytes(pkg.read_bytes()[:20])
    rc, out, err = run([str(HERE / "wxapkg.py"), str(trunc), "--list"])
    check("wxapkg: rejects a truncated file with a reason", rc == 1 and "cannot parse" in err)


def main():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        print("warc.py")
        test_warc(tmp)
        print("wxapkg.py")
        test_wxapkg(tmp)
    print(f"\nfixtures: {len(PASS) + len(FAIL)} checks, {len(PASS)} pass, {len(FAIL)} fail")
    if FAIL:
        for f in FAIL:
            print(f"  failed: {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
