#!/usr/bin/env python3
"""
warc.py: read a WARC archive and emit the same record shape a HAR would.

Why this exists. D31 named ten REA gaps as build candidates and none were built. This is the first of
them. A WARC is what a crawler or an archival capture produces, and until now the repo had no way to read
one, which meant an archived target was unreadable without a third party tool.

Scope, stated honestly: this reads uncompressed and gzip member WARC 1.0 and 1.1 records. It does not
reconstruct a browsable session, resolve revisits against originals beyond a pointer, or verify digests.
Those are named as limits rather than left implied.

Usage:
  python3 rea-ops/warc.py archive.warc              # JSONL to stdout, one record per response
  python3 rea-ops/warc.py archive.warc --summary     # counts and hosts only
  python3 rea-ops/warc.py archive.warc --url https://example.com/
"""
import argparse
import gzip
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def open_maybe_gzip(path):
    """WARC files are often concatenated gzip members, which gzip.open reads as one stream."""
    raw = Path(path).read_bytes()
    # newline="" is required. Universal newline mode rewrites every CRLF to LF, which breaks the
    # header terminator search and every Content-Length offset computed from it.
    if raw[:2] == b"\x1f\x8b":
        return io.TextIOWrapper(gzip.GzipFile(fileobj=io.BytesIO(raw)), encoding="utf-8",
                                errors="replace", newline="")
    return io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8", errors="replace", newline="")


def parse_records(raw):
    """Split a WARC into (headers, payload), framing on bytes.

    Content-Length counts bytes, so every offset here is a byte offset. An earlier version decoded the
    archive to text first and then sliced with a byte count, which truncates any body containing a
    multi-byte character and misaligns every record after it. The ASCII fixtures never showed this, which
    is exactly the failure mode of a fixture that shares the reader's assumptions.
    """
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    records = []
    i = 0
    n = len(raw)
    while i < n:
        start = raw.find(b"WARC/", i)
        if start < 0:
            break
        head_end = raw.find(b"\r\n\r\n", start)
        if head_end < 0:
            records.append(({"_error": "header block not terminated"}, ""))
            break
        block = raw[start:head_end].decode("utf-8", "replace")
        lines = block.split("\r\n")
        version = lines[0].strip()
        headers = {"_version": version}
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        try:
            length = int(headers.get("content-length", "0"))
        except ValueError:
            length = 0
        body_start = head_end + 4
        chunk = raw[body_start:body_start + length]
        if len(chunk) != length:
            headers["_error"] = (f"declared Content-Length {length} but only {len(chunk)} bytes remain")
        body = chunk.decode("utf-8", "replace")
        i = body_start + len(chunk)
        while i < n and raw[i:i + 1] in (b"\r", b"\n"):
            i += 1
        records.append((headers, body))
    return records


def to_har_like(headers, body, source):
    """Emit the fields the rest of this repo understands, and say which are absent rather than guessing."""
    status = headers.get("warc-type")
    out = {
        "source": str(source),
        "warc_type": status,
        "target_uri": headers.get("warc-target-uri"),
        "date": headers.get("warc-date"),
        "record_id": headers.get("warc-record-id"),
        "content_type": headers.get("content-type"),
        "body_bytes": len(body),
    }
    if status == "response":
        # the payload of a response record is an HTTP message: status line, headers, body
        head, _, payload = body.partition("\r\n\r\n")
        lines = head.split("\r\n")
        code = None
        if lines and lines[0].startswith("HTTP/"):
            parts = lines[0].split()
            if len(parts) >= 2 and parts[1].isdigit():
                code = int(parts[1])
        resp_headers = {}
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                resp_headers.setdefault(k.strip().lower(), []).append(v.strip())
        out["http_status"] = code
        out["response_headers"] = resp_headers
        out["content"] = payload
        digest = headers.get("warc-payload-digest")
        if digest:
            out["payload_digest"] = digest
    return out


def summary(records):
    from collections import Counter
    types = Counter(h.get("warc-type") for h, _ in records)
    hosts = Counter()
    for h, _ in records:
        uri = h.get("warc-target-uri") or ""
        if "://" in uri:
            host = uri.split("://", 1)[1].split("/")[0]
            hosts[host] += 1
    return {
        "records": len(records),
        "by_type": dict(types),
        "hosts": dict(hosts.most_common(20)),
        "note": "counts are of parsed records only; a malformed record is reported as an error record",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--url")
    ap.add_argument("--with-body", action="store_true", help="include response bodies (large)")
    args = ap.parse_args()

    if not Path(args.path).exists():
        print(f"no such file: {args.path}", file=sys.stderr)
        return 1

    text = Path(args.path).read_bytes()
    if text[:2] == b"\x1f\x8b":
        import gzip as _gz
        text = _gz.decompress(text)
    records = parse_records(text)
    if not records:
        print("no WARC records found: the file may not be a WARC, or it may be compressed twice",
              file=sys.stderr)
        return 1

    if args.summary:
        print(json.dumps(summary(records), indent=1))
        return 0

    n = 0
    for headers, body in records:
        if headers.get("_error"):
            print(json.dumps({"error": headers["_error"]}), file=sys.stdout)
            continue
        if args.url and args.url not in (headers.get("warc-target-uri") or ""):
            continue
        rec = to_har_like(headers, body, args.path)
        if not args.with_body:
            rec.pop("content", None)
        print(json.dumps(rec, ensure_ascii=False))
        n += 1
        if args.url and n >= 20:
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
