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


def make_leveldb_log(path, batches):
    """Write a LevelDB write-ahead log with the same layout leveldb-log.py implements.
    batches is a list of (sequence, [(key_bytes, value_bytes_or_None), ...])."""
    import struct

    POLY = 0x82F63B78
    table = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (c >> 1) ^ POLY if c & 1 else c >> 1
        table.append(c)

    def crc32c(data, crc=0):
        crc ^= 0xFFFFFFFF
        for b in data:
            crc = table[(crc ^ b) & 0xFF] ^ (crc >> 8)
        return crc ^ 0xFFFFFFFF

    def mask(c):
        return ((((c >> 15) | (c << 17)) & 0xFFFFFFFF) + 0xA282EAD8) & 0xFFFFFFFF

    def varint(n):
        out = b""
        while True:
            b = n & 0x7F
            n >>= 7
            out += bytes([b | (0x80 if n else 0)])
            if not n:
                return out

    import io
    buf = io.BytesIO()
    for seq, ops in batches:
        payload = struct.pack("<QI", seq, len(ops))
        for k, v in ops:
            payload += b"\x01" if v is not None else b"\x00"
            payload += varint(len(k)) + k
            if v is not None:
                payload += varint(len(v)) + v
        buf.write(struct.pack("<IHB", mask(crc32c(payload)), len(payload), 1))
        buf.write(payload)
    path.write_bytes(buf.getvalue())


def make_hap(path, module_json=None, extra=None):
    import zipfile
    with zipfile.ZipFile(path, "w") as zf:
        if module_json is not None:
            import json as _j
            zf.writestr("module.json", _j.dumps(module_json))
        for name, data in (extra or {}).items():
            zf.writestr(name, data)


def cbor(obj):
    """Encoder for the subset the WebAuthn fixture needs: definite lengths only."""
    import struct
    def head(major, n):
        if n < 24:
            return bytes([(major << 5) | n])
        if n < 256:
            return bytes([(major << 5) | 24, n])
        if n < 65536:
            return bytes([(major << 5) | 25]) + struct.pack(">H", n)
        return bytes([(major << 5) | 26]) + struct.pack(">I", n)

    if isinstance(obj, bool):
        return bytes([0xF5 if obj else 0xF4])
    if isinstance(obj, int):
        return head(0, obj) if obj >= 0 else head(1, -1 - obj)
    if isinstance(obj, (bytes, bytearray)):
        return head(2, len(obj)) + bytes(obj)
    if isinstance(obj, str):
        b = obj.encode()
        return head(3, len(b)) + b
    if isinstance(obj, list):
        return head(4, len(obj)) + b"".join(cbor(x) for x in obj)
    if isinstance(obj, dict):
        return head(5, len(obj)) + b"".join(cbor(k) + cbor(v) for k, v in obj.items())
    raise TypeError(type(obj))


def make_attestation(fmt="none", flags=0x45, sign_count=7, aaguid=b"\x11" * 16,
                     cred_id=b"cred-identifier-01", rp_id_hash=b"\xab" * 32):
    import base64
    cose_key = {1: 2, 3: -7, -1: 1, -2: b"\x22" * 32, -3: b"\x33" * 32}
    auth = rp_id_hash + bytes([flags]) + sign_count.to_bytes(4, "big")
    if flags & 0x40:
        auth += aaguid + len(cred_id).to_bytes(2, "big") + cred_id + cbor(cose_key)
    obj = {"fmt": fmt, "attStmt": {"alg": -7, "sig": b"\x00" * 8}, "authData": auth}
    return base64.b64encode(cbor(obj)).decode()


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


def test_leveldb(tmp):
    log = tmp / "000003.log"
    # Chrome shaped: an origin prefixed key with a UTF-16LE value, then a delete
    key1 = b"_https://example.test\x00\x01theme"
    val1 = "dark".encode("utf-16-le")
    make_leveldb_log(log, [(100, [(key1, val1)]), (101, [(b"plain-key", b"plain-value")]),
                           (102, [(b"gone-key", None)])])
    rc, out, err = run([str(HERE / "leveldb-log.py"), str(log), "--json"])
    rows = [json.loads(l) for l in out.splitlines() if l.strip().startswith("{")]
    check("leveldb: exits 0 on a valid log", rc == 0, err[:90])
    check("leveldb: reads three operations", len(rows) == 3, f"got {len(rows)}")
    check("leveldb: put and delete distinguished",
          [r["op"] for r in rows] == ["put", "put", "delete"], str([r["op"] for r in rows]))
    check("leveldb: sequence numbers ascend", [r["seq"] for r in rows] == [100, 101, 102])
    check("leveldb: utf16 value decoded", rows[0]["value_view"]["utf16"] == "dark",
          rows[0]["value_view"]["utf16"])
    check("leveldb: origin prefix visible in the key ascii view",
          "example.test" in rows[0]["key_view"]["ascii"])

    rc, out, _ = run([str(HERE / "leveldb-log.py"), str(log), "--keys"])
    check("leveldb: keys mode prints one line per op", len(out.strip().splitlines()) == 3)

    # a file that is not a log must not report success with zero records
    junk = tmp / "notalog.bin"
    junk.write_bytes(b"\x00" * 64)
    rc, out, err = run([str(HERE / "leveldb-log.py"), str(junk)])
    check("leveldb: refuses a non-log instead of reporting emptiness", rc == 2 and "sorted table" in err,
          f"rc={rc}")


def test_hap(tmp):
    hap = tmp / "app.hap"
    make_hap(hap, module_json={"module": {"name": "entry", "deviceTypes": ["phone"],
                                          "requestPermissions": [{"name": "ohos.permission.INTERNET"}]}},
             extra={"ets/modules.abc": b"PANDA" + b"\x00" * 32,
                    "libs/arm64-v8a/libentry.so": b"\x7fELF"})
    rc, out, err = run([str(HERE / "hap.py"), str(hap), "--info"])
    d = parse_json(out)
    check("hap: exits 0 on a valid package", rc == 0, err[:90])
    check("hap: finds the Ark bytecode file", d.get("ark_bytecode") == ["ets/modules.abc"])
    check("hap: finds native libraries", d.get("native_libraries") == ["libs/arm64-v8a/libentry.so"])
    check("hap: parses module.json",
          d.get("manifest", {}).get("module.json", {}).get("module", {}).get("name") == "entry")

    outdir = tmp / "hap-out"
    rc, out, _ = run([str(HERE / "hap.py"), str(hap), "--out", str(outdir)])
    check("hap: extracts entries", parse_json(out).get("extracted") == 3)
    check("hap: extracted bytecode intact",
          (outdir / "ets/modules.abc").read_bytes().startswith(b"PANDA"))

    # traversal must be refused
    evil = tmp / "evil.hap"
    make_hap(evil, module_json={}, extra={"../../escaped.txt": b"nope"})
    rc, out, _ = run([str(HERE / "hap.py"), str(evil), "--out", str(tmp / "hap-evil")])
    d = parse_json(out)
    check("hap: refuses traversal names", d.get("skipped") and not (tmp / "escaped.txt").exists())

    # a non zip must fail with a reason
    notzip = tmp / "notzip.hap"
    notzip.write_bytes(b"nope")
    rc, out, err = run([str(HERE / "hap.py"), str(notzip), "--list"])
    check("hap: rejects a non container with a reason", rc == 1 and "not a zip" in err)


def test_webauthn(tmp):
    good = make_attestation()
    rc, out, err = run([str(HERE / "webauthn-attestation.py"), "--b64", good])
    d = parse_json(out)
    check("webauthn: exits 0 on a valid attestation", rc == 0, err[:90])
    check("webauthn: reports the format", d.get("fmt") == "none")
    ad = d.get("auth_data", {})
    check("webauthn: user present and verified flags decoded",
          ad.get("flags", {}).get("user_present") is True
          and ad.get("flags", {}).get("user_verified") is True)
    check("webauthn: sign count decoded", ad.get("sign_count") == 7)
    check("webauthn: rp id hash is the 32 bytes supplied",
          ad.get("rp_id_hash_hex") == "ab" * 32)
    cred = ad.get("attested_credential") or {}
    check("webauthn: aaguid extracted", cred.get("aaguid_hex") == "11" * 16)
    check("webauthn: credential id extracted", cred.get("credential_id_hex") == b"cred-identifier-01".hex())
    check("webauthn: COSE key decoded", str((cred.get("public_key_cose") or {}).get("3")) == "-7",
          str(cred.get("public_key_cose"))[:60])

    # a zero aaguid means no attestation identity to check, which is a real and common case
    zero = make_attestation(aaguid=b"\x00" * 16)
    rc, out, err = run([str(HERE / "webauthn-attestation.py"), "--b64", zero])
    d = parse_json(out)
    got = (d.get("auth_data", {}).get("attested_credential") or {}).get("aaguid_is_zero")
    check("webauthn: zero aaguid flagged", got is True, f"rc={rc} got={got} {err[:60]}")

    # a truncated authData must fail with a reason, not a partial report
    rc, out, err = run([str(HERE / "webauthn-attestation.py"), "--b64", "o2NmbXRoZQ=="])
    check("webauthn: rejects a bad object with a reason", rc == 1 and "cannot parse" in err)

    # a JSON wrapper around the object must work, which is how a client stores it
    wrapper = tmp / "reg.json"
    wrapper.write_text(json.dumps({"response": {"attestationObject": good}}))
    rc, out, _ = run([str(HERE / "webauthn-attestation.py"), str(wrapper)])
    check("webauthn: reads a JSON wrapper", rc == 0 and parse_json(out).get("fmt") == "none")


def main():
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        print("warc.py")
        test_warc(tmp)
        print("wxapkg.py")
        test_wxapkg(tmp)
        print("leveldb-log.py")
        test_leveldb(tmp)
        print("hap.py")
        test_hap(tmp)
        print("webauthn-attestation.py")
        test_webauthn(tmp)
    print(f"\nfixtures: {len(PASS) + len(FAIL)} checks, {len(PASS)} pass, {len(FAIL)} fail")
    if FAIL:
        for f in FAIL:
            print(f"  failed: {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
