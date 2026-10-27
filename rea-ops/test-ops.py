#!/usr/bin/env python3
"""
test-ops.py: build fixtures for the REA operations and test them against those fixtures.

An operation with no fixture is a claim. Both operations here are tested against files this script
generates, so the test does not depend on any download and cannot drift with a remote sample.

Run: python3 rea-ops/test-ops.py
"""
import base64
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


def vlq(n):
    """Encode one signed value as base64 VLQ, the inverse of what sourcemap.py decodes."""
    B = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    v = (-n << 1 | 1) if n < 0 else (n << 1)
    out = ""
    while True:
        digit = v & 31
        v >>= 5
        if v:
            digit |= 32
        out += B[digit]
        if not v:
            return out


def make_sourcemap(bundle_path, with_content=True, inline=False):
    """A two line bundle whose map points line 1 column 4 at src/app.js line 9 column 2."""
    js = "function a(x){return x}\nconsole.log(\"BOOM\")\n//# sourceMappingURL=%s\n"
    src = "// original source for the fixture\nexport function a(x) { return x; }\n"
    m = {
        "version": 3,
        "sources": ["webpack:///src/app.js"],
        "names": [],
        # one segment is a concatenation of VLQ values, not a comma separated list. Getting this
        # backwards produces a map that parses and maps nothing, which is the quiet failure mode.
        "mappings": ";".join(["", "".join([vlq(4), vlq(0), vlq(9), vlq(2)])]),
    }
    if with_content:
        m["sourcesContent"] = [src]
    if inline:
        raw = base64.b64encode(json.dumps(m).encode()).decode()
        js = js % ("data:application/json;base64," + raw)
        bundle_path.write_text(js)
        return m
    bundle_path.write_text(js % "app.js.map")
    (bundle_path.parent / "app.js.map").write_text(json.dumps(m))
    return m


def make_hermes(path, version=96, funcs=120, strings=900, storage=4096):
    """A Hermes header this repo generates. Circular by construction: it validates the reader against the
    layout the reader implements, not against a real .hbc. Stated so nobody mistakes it for field data."""
    import struct
    body = b"\x00" * 64
    total = 48 + len(body)
    hdr = struct.pack("<QIII", 0xC61FBB1E, version, 0xDEADBEEF, total)
    hdr += struct.pack("<IIIIIII", 0, funcs, 4, 40, strings, 0, storage)
    path.write_bytes(hdr + body)
    return total


def make_flutter_so(path):
    """Compile a real shared object with the four Flutter snapshot symbols.

    Unlike the wxapkg and Hermes fixtures, this one is genuinely external: gcc produces the ELF and its
    symbol table, so the parser is validated against a real toolchain rather than against bytes this repo
    wrote itself. That is a stronger fixture and it is worth saying why.
    """
    import subprocess, tempfile
    c = tmp_c = path.parent / "fixture.c"
    c.write_text(
        '#include <stdint.h>\n'
        'const unsigned char _kDartVmSnapshotData[4096] = {1,2,3,4};\n'
        'const unsigned char _kDartVmSnapshotInstructions[8192] = {5,6,7,8};\n'
        'const unsigned char _kDartIsolateSnapshotData[16384] = {9,10};\n'
        'const unsigned char _kDartIsolateSnapshotInstructions[32768] = {11,12};\n'
        'const char *dart_version = "3.4.0 (stable) (Tue Aug 6 2026)";\n'
        'int unused(int x) { return x + 1; }\n')
    r = subprocess.run(["gcc", "-shared", "-fPIC", "-o", str(path), str(c)],
                       capture_output=True, text=True, timeout=120)
    c.unlink(missing_ok=True)
    return r.returncode == 0, r.stderr


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


def test_sourcemap(tmp):
    external = tmp / "app.external.js"
    make_sourcemap(external, with_content=True)
    rc, out, err = run([str(HERE / "sourcemap.py"), str(external), "--sources"])
    d = parse_json(out)
    check("sourcemap: finds an external map", rc == 0 and d.get("map_kind") == "external", err[:80])
    check("sourcemap: lists the original source",
          d.get("source_list") == ["webpack:///src/app.js"], str(d.get("source_list")))
    check("sourcemap: reports embedded content", d.get("with_embedded_content") == 1)

    rc, out, _ = run([str(HERE / "sourcemap.py"), str(external), "--lookup", "1", "10"])
    d = parse_json(out)
    got = d.get("lookup") or {}
    check("sourcemap: decodes a position to an original one",
          got.get("source") == "webpack:///src/app.js" and got.get("original_line") == 9,
          str(got)[:70])

    outdir = tmp / "sm-out"
    rc, out, _ = run([str(HERE / "sourcemap.py"), str(external), "--extract", str(outdir)])
    d = parse_json(out)
    check("sourcemap: extracts embedded sources", d.get("extracted") == 1)
    saved = outdir / "src/app.js"
    check("sourcemap: extracted content matches",
          saved.exists() and "original source for the fixture" in saved.read_text())

    inline = tmp / "app.inline.js"
    make_sourcemap(inline, with_content=True, inline=True)
    rc, out, _ = run([str(HERE / "sourcemap.py"), str(inline), "--sources"])
    d = parse_json(out)
    check("sourcemap: finds an inline data URI map",
          rc == 0 and d.get("map_kind") == "inline", str(d.get("map_kind")))

    # the honest case: no map, carve and say confidence is low
    bare = tmp / "app.bare.js"
    bare.write_text('/*! (c) fixture */\nvar webpackChunkapp=[];require("./src/thing.js");\n')
    rc, out, _ = run([str(HERE / "sourcemap.py"), str(bare), "--carve"])
    d = parse_json(out)
    check("sourcemap: no map reports low confidence and says so",
          d.get("confidence") == "low" and "not original sources" in str(d.get("recovered")))
    check("sourcemap: carve names the chunk", "app" in (d.get("chunk_names") or []))
    check("sourcemap: carve surfaces path like literals",
          any("src/thing.js" in x for x in (d.get("path_like_strings") or [])))

    rc, out, err = run([str(HERE / "sourcemap.py"), str(bare), "--sources"])
    check("sourcemap: asking for sources with no map exits 2 with a reason",
          rc == 2 and "no map" in err, f"rc={rc}")


def test_hermes(tmp):
    hbc = tmp / "index.android.bundle.hbc"
    make_hermes(hbc, version=96, funcs=120, strings=900, storage=4096)
    rc, out, err = run([str(HERE / "hermes.py"), str(hbc), "--json"])
    d = parse_json(out)
    check("hermes: reads a valid header", rc == 0, err[:80])
    check("hermes: reports the version", d.get("version") == 96)
    check("hermes: reports function and string counts",
          d.get("function_count") == 120 and d.get("string_count") == 900)
    check("hermes: length check agrees with the file", d.get("length_matches") is True)
    check("hermes: version inside the known range makes no warning", "warning" not in d)

    # an unknown version must still report the header but say so
    odd = tmp / "odd.hbc"
    make_hermes(odd, version=250)
    rc, out, _ = run([str(HERE / "hermes.py"), str(odd), "--json"])
    d = parse_json(out)
    check("hermes: unknown version warns instead of guessing",
          rc == 0 and d.get("known_version") is False and "outside" in str(d.get("warning")))

    # not Hermes at all
    junk = tmp / "junk.bin"
    junk.write_bytes(b"not a hermes bundle at all, twelve bytes")
    rc, out, err = run([str(HERE / "hermes.py"), str(junk)])
    check("hermes: rejects a non Hermes file with a reason", rc == 1 and "not Hermes" in err)


def test_flutter(tmp):
    so = tmp / "libapp.so"
    ok, err = make_flutter_so(so)
    if not ok:
        check("flutter: fixture compiles", False, err[:80])
        return
    check("flutter: fixture compiles with gcc", True)

    rc, out, err = run([str(HERE / "flutter-aot.py"), str(so), "--json"])
    d = parse_json(out)
    check("flutter: identifies the library", rc == 0 and d.get("is_flutter") is True, err[:80])
    snaps = d.get("snapshots") or {}
    check("flutter: finds all four snapshots", len(snaps) == 4, str(sorted(snaps)))
    check("flutter: reports a real size for the isolate data",
          (snaps.get("_kDartIsolateSnapshotData") or {}).get("size") == 16384,
          str(snaps.get("_kDartIsolateSnapshotData")))
    check("flutter: reports the embedded dart version",
          d.get("dart_version_string") == "3.4.0", str(d.get("dart_version_string")))
    check("flutter: records the version context", "stable" in str(d.get("dart_version_context")))

    # Stripping removes .symtab but not .dynsym, and these symbols are exported, so a stripped Flutter
    # library still identifies. Asserting the opposite was wrong: the real question is whether the reader
    # survives stripping, and it does.
    stripped = tmp / "stripped.so"
    import subprocess
    subprocess.run(["cp", str(so), str(stripped)], check=True)
    subprocess.run(["strip", str(stripped)], capture_output=True)
    rc, out, _ = run([str(HERE / "flutter-aot.py"), str(stripped), "--json"])
    d = parse_json(out)
    check("flutter: still identifies after strip, because these are dynamic exports",
          rc == 0 and d.get("is_flutter") is True, str(sorted((d.get("snapshots") or {}).keys()))[:60])

    # not an ELF at all
    junk = tmp / "junk.so"
    junk.write_bytes(b"\x7fELx" + b"\x00" * 40)
    rc, out, err = run([str(HERE / "flutter-aot.py"), str(junk)])
    check("flutter: rejects a non ELF file with a reason", rc == 1 and "not an ELF" in err)


def test_sw(tmp):
    cap = tmp / "cap.json"
    cap.write_text(json.dumps({
        "registrations": [{"scopeURL": "https://a.test/", "scriptURL": "https://a.test/sw.js"}],
        "caches": [{"name": "c1", "entries": [
            {"url": "https://a.test/api/me/account", "status": 200,
             "headers": {"Content-Type": "application/json", "Authorization": "Bearer x"}},
            {"url": "https://a.test/static/logo.svg", "status": 200,
             "headers": {"Content-Type": "image/svg+xml", "Cache-Control": "public, max-age=86400"}},
            {"url": "https://a.test/dashboard", "status": 200,
             "headers": {"Content-Type": "text/html", "Cache-Control": "public"}},
        ]}]}))
    rc, out, err = run([str(HERE / "sw-recover.py"), str(cap), "--json"])
    d = parse_json(out)
    check("sw-recover: parses a cdp capture", rc == 0 and d.get("shape") == "cdp", err[:80])
    check("sw-recover: counts entries", d.get("cached_entries") == 3)
    urls = [r["url"] for r in d.get("risk") or []]
    check("sw-recover: flags the principal bound api response",
          any("api/me/account" in u for u in urls), str(urls))
    check("sw-recover: does not flag a public static asset",
          not any("logo.svg" in u for u in urls), str(urls))
    check("sw-recover: flags a public html page as the weaker case",
          any("dashboard" in u for u in urls) and
          any("varies by user" in r for r in
              [x for e in (d.get("risk") or []) for x in e["reasons"]]))

    # a HAR shaped file must be accepted too
    har = tmp / "cap.har"
    har.write_text(json.dumps({"log": {"entries": [
        {"request": {"url": "https://a.test/app"},
         "response": {"status": 200, "headers": [{"name": "Cache-Control", "value": "public"}],
                      "content": {"size": 10}},
         "_resourceType": "serviceworker"}]}}))
    rc, out, _ = run([str(HERE / "sw-recover.py"), str(har), "--json"])
    d = parse_json(out)
    check("sw-recover: accepts a HAR shape", rc == 0 and d.get("shape") == "har")

    # neither shape
    junk = tmp / "x.json"
    junk.write_text('{"hello": 1}')
    rc, out, err = run([str(HERE / "sw-recover.py"), str(junk)])
    check("sw-recover: rejects an unknown shape with a reason", rc == 2 and "not a CDP" in err)


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
        print("sourcemap.py")
        test_sourcemap(tmp)
        print("hermes.py")
        test_hermes(tmp)
        print("flutter-aot.py")
        test_flutter(tmp)
        print("sw-recover.py")
        test_sw(tmp)
    print(f"\nfixtures: {len(PASS) + len(FAIL)} checks, {len(PASS)} pass, {len(FAIL)} fail")
    if FAIL:
        for f in FAIL:
            print(f"  failed: {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
