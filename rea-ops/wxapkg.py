#!/usr/bin/env python3
"""
wxapkg.py: unpack a WeChat mini program package.

Why this exists. D31 gap two. Mini programs are a real web surface in the China lane and the only way
into one is unpacking its package. There was no reader here, so the whole lane was unreadable.

Layout this reader implements, and which its fixture writes: a 12 byte header of three little-endian
uint32 (magic 0xBE, info flags, index length), then the index, then the file data. The index is a uint32
file count, then per entry a uint32 name length, the name bytes, a uint32 data offset and a uint32 size,
with offsets relative to the first byte of the data section.

**This has not been validated against a real WeChat package.** The layout matches the fixture in
`rea-ops/test-ops.py` and nothing else. Published descriptions of the format disagree on the header
width across package versions, so a real sample has to be checked before this is trusted, and that check
has not been done. Treat it as a correct parser for a documented shape, not as a working WeChat tool.

Scope: no decryption of encrypted packages, no decompilation, no reconstruction of the original project
tree.

Usage:
  python3 rea-ops/wxapkg.py app.wxapkg --list
  python3 rea-ops/wxapkg.py app.wxapkg --out dir/
"""
import argparse
import json
import struct
import sys
from pathlib import Path

MAGIC_FIRST_BYTE = 0xBE


def parse(raw):
    """Return (header, files) or raise ValueError with a specific reason."""
    if len(raw) < 12:
        raise ValueError(f"too short for a header: {len(raw)} bytes")
    if raw[0] != MAGIC_FIRST_BYTE:
        raise ValueError(f"first byte is 0x{raw[0]:02x}, expected 0x{MAGIC_FIRST_BYTE:02x}. "
                         "This is not a wxapkg, or it is encrypted")
    first, flags, index_len = struct.unpack_from("<III", raw, 0)
    header = {"first_mark": first, "info_flags": flags, "index_length": index_len,
              "header_bytes": 12}
    index_end = 12 + index_len
    if index_end > len(raw):
        raise ValueError(f"index length {index_len} runs past the file end ({len(raw)} bytes)")

    off = 12
    (count,) = struct.unpack_from("<I", raw, off)
    off += 4
    files = []
    for i in range(count):
        if off + 4 > index_end:
            raise ValueError(f"file count says {count}, index ended after {i} entries")
        (name_len,) = struct.unpack_from("<I", raw, off)
        off += 4
        if off + name_len + 8 > index_end:
            raise ValueError(f"entry {i} runs past the index end")
        name = raw[off:off + name_len].decode("utf-8", errors="replace")
        off += name_len
        file_off, size = struct.unpack_from("<II", raw, off)
        off += 8
        files.append({"name": name, "offset": file_off, "size": size})
    return header, files, index_end


def safe_relpath(name):
    """A package is attacker supplied. Never trust a path inside one."""
    p = Path(name)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError(f"refusing to extract unsafe path: {name}")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()

    raw = Path(args.path).read_bytes()
    try:
        header, files, data_start = parse(raw)
    except ValueError as e:
        print(f"cannot parse: {e}", file=sys.stderr)
        return 1

    if args.list or not args.out:
        print(json.dumps({"header": header, "files": len(files),
                          "entries": [{"name": f["name"], "size": f["size"]} for f in files[:200]]},
                         indent=1))
        return 0

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    written = 0
    skipped = []
    for f in files:
        try:
            rel = safe_relpath(f["name"])
        except ValueError as e:
            skipped.append(str(e))
            continue
        start = data_start + f["offset"]
        end = start + f["size"]
        if end > len(raw):
            skipped.append(f"{f['name']}: declared size runs past the file end")
            continue
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw[start:end])
        written += 1

    print(json.dumps({"extracted": written, "skipped": skipped, "out": str(out)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
