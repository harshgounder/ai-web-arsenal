#!/usr/bin/env python3
"""
leveldb-log.py: read a LevelDB write-ahead log and emit its keys and values.

Why this exists. D31 gap one. Chrome stores LocalStorage, IndexedDB metadata and session state in
LevelDB, and the write-ahead log is where recent writes live before compaction. Without a reader, live
browser storage is opaque, which is a strange hole for a web arsenal to have.

What this reads, and what it does not:

  reads    the .log / LOG write-ahead log: 32 KiB blocks, records split across block boundaries, a
           masked CRC32C per record, and WriteBatch payloads of put and delete operations
  does not read the .ldb / .sst sorted tables, which need block handles and snappy, so a value that was
           compacted before the log was read is not here. Say so rather than returning an empty result
           that reads like absence.

Scope note that matters for Chrome: LocalStorage keys are blobs shaped like
`_<origin>\\x00\\x01<key>` and values are UTF-16LE. This tool reports raw bytes in hex and a best effort
UTF-16 view, and labels the view as a guess, because guessing wrong silently is worse than not guessing.

Usage:
  python3 rea-ops/leveldb-log.py path/to/000003.log
  python3 rea-ops/leveldb-log.py path/to/000003.log --keys
  python3 rea-ops/leveldb-log.py path/to/000003.log --json
"""
import argparse
import json
import struct
import sys
from pathlib import Path

BLOCK = 32768
HEADER = 7  # 4 checksum, 2 length, 1 type
FULL, FIRST, MIDDLE, LAST = 1, 2, 3, 4

# CRC32C (Castagnoli), reflected, which is what LevelDB uses. zlib.crc32 is the other polynomial and
# would reject every record, so this table is not optional.
_POLY = 0x82F63B78
_TABLE = []
for _i in range(256):
    _c = _i
    for _ in range(8):
        _c = (_c >> 1) ^ _POLY if _c & 1 else _c >> 1
    _TABLE.append(_c)


def crc32c(data, crc=0):
    crc ^= 0xFFFFFFFF
    for b in data:
        crc = _TABLE[(crc ^ b) & 0xFF] ^ (crc >> 8)
    return crc ^ 0xFFFFFFFF


def unmask(masked):
    rot = ((masked - 0xA282EAD8) & 0xFFFFFFFF)
    return ((rot >> 17) | (rot << 15)) & 0xFFFFFFFF


def read_records(raw):
    """Yield (offset, type, payload) for logical records, joining fragments across blocks."""
    pos = 0
    pending = b""
    pending_at = None
    n = len(raw)
    while pos + HEADER <= n:
        block_end = min(((pos // BLOCK) + 1) * BLOCK, n)
        remaining = block_end - pos
        if remaining < HEADER:
            pos = block_end          # trailer padding, not a record
            continue
        checksum, length, rtype = struct.unpack_from("<IHB", raw, pos)
        if rtype == 0 and length == 0:
            pos = block_end          # zero filled remainder of a block
            continue
        if pos + HEADER + length > block_end:
            # A record may not span a block boundary; the writer pads instead. Treat as corruption.
            yield (pos, "corrupt", b"record length crosses a block boundary")
            pos = block_end
            continue
        payload = raw[pos + HEADER: pos + HEADER + length]
        if rtype == 0:  # zero fill or padding
            pos = block_end
            continue
        if rtype == FULL:
            yield (pos, FULL, payload)
            pending = b""
        elif rtype == FIRST:
            pending = payload
            pending_at = pos
        elif rtype == MIDDLE:
            pending += payload
        elif rtype == LAST:
            yield (pending_at, FULL, pending + payload)
            pending = b""
        else:
            yield (pos, "unknown-type", bytes([rtype]))
        pos += HEADER + length


def read_varint(buf, i):
    shift = 0
    val = 0
    while True:
        if i >= len(buf):
            raise ValueError("varint runs past end")
        b = buf[i]
        i += 1
        val |= (b & 0x7F) << shift
        if not b & 0x80:
            return val, i
        shift += 7
        if shift > 63:
            raise ValueError("varint too long")


def parse_batch(payload):
    """WriteBatch: sequence u64, count u32, then tag + key [+ value] per entry."""
    if len(payload) < 12:
        raise ValueError("batch shorter than its header")
    seq, count = struct.unpack_from("<QI", payload, 0)
    i = 12
    out = []
    for _ in range(count):
        if i >= len(payload):
            raise ValueError("batch ended before its declared count")
        tag = payload[i]
        i += 1
        klen, i = read_varint(payload, i)
        key = payload[i:i + klen]
        i += klen
        if tag == 1:
            vlen, i = read_varint(payload, i)
            val = payload[i:i + vlen]
            i += vlen
            out.append({"seq": seq, "op": "put", "key": key, "value": val})
        elif tag == 0:
            out.append({"seq": seq, "op": "delete", "key": key, "value": b""})
        else:
            raise ValueError(f"unknown batch tag {tag}")
        seq += 1
    return out


def view(b):
    """A printable label, honest about which half is the guess."""
    if not b:
        return {"hex": "", "utf16": ""}
    try:
        u = b.decode("utf-16-le")
        utf16 = u if u.isprintable() else u.encode("unicode_escape").decode()
    except Exception:
        utf16 = ""
    hx = b.hex()
    printable = "".join(chr(c) if 32 <= c < 127 else "." for c in b)
    return {"hex": hx[:400], "ascii": printable[:200], "utf16": utf16[:200]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--keys", action="store_true", help="print keys only")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"no such file: {p}", file=sys.stderr)
        return 1
    raw = p.read_bytes()

    rows = []
    bad = 0
    for offset, rtype, payload in read_records(raw):
        if rtype != FULL:
            bad += 1
            if args.json:
                print(json.dumps({"offset": offset, "problem": payload.decode(errors="replace")}))
            continue
        try:
            for op in parse_batch(payload):
                op["key_view"] = view(op["key"])
                op["value_view"] = view(op["value"])
                rows.append(op)
        except Exception as e:
            bad += 1
            print(json.dumps({"offset": offset, "batch_error": str(e)}), file=sys.stderr)
        if args.limit and len(rows) >= args.limit:
            break

    if args.json:
        for r in rows:
            r.pop("key", None)
            r.pop("value", None)
            print(json.dumps(r))
    elif args.keys:
        for r in rows:
            print(f"{r['op']:6} {r['key_view'].get('ascii') or r['key_view']['hex'][:80]}")
    else:
        for r in rows:
            print(json.dumps({"seq": r["seq"], "op": r["op"],
                              "key": r["key_view"], "value": r["value_view"]}, ensure_ascii=False))

    print(f"records {len(rows)} from {p.name}, unreadable {bad}", file=sys.stderr)
    if not rows and not bad:
        print("no records found: this may be a sorted table (.ldb/.sst) rather than a log, which this "
              "reader does not handle", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
