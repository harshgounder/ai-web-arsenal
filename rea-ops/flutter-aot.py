#!/usr/bin/env python3
"""
flutter-aot.py: identify a Flutter AOT library and report where its Dart snapshots live.

Why this exists, and what it refuses to do. D31 gap three. A Flutter app's Dart code is compiled ahead of
time into `libapp.so` and is not in the APK's DEX, so a reader that only understands DEX sees none of the
application logic. The first question is always the same: is this Flutter, which Dart and engine version,
and where are the four snapshots.

This answers that question by reading the ELF symbol table for the four snapshot symbols Flutter emits, and
reporting each one's offset, size and the first bytes of its content. It does **not** deserialise the
snapshot, recover class or function names, or decompile anything. Deserialising needs an SDK specific
parser keyed to the exact Dart version, and a parser built against the wrong version produces plausible
nonsense, which is worse than a clear refusal.

The version question is answered honestly: if the library embeds a Dart version string or a snapshot hash
it is reported; if it does not, the tool says so instead of inferring a version from a symbol layout that
changed across releases.

Usage:
  python3 rea-ops/flutter-aot.py libapp.so
  python3 rea-ops/flutter-aot.py libapp.so --json
"""
import argparse
import json
import re
import struct
import sys
from pathlib import Path

SYMBOLS = ("_kDartVmSnapshotData", "_kDartVmSnapshotInstructions",
           "_kDartIsolateSnapshotData", "_kDartIsolateSnapshotInstructions")

# A Dart version string appears in libflutter.so and sometimes in libapp.so. It looks like 3.4.0 (stable)
# followed by a date or a commit. Matching loosely here and reporting the match verbatim, rather than
# parsing it into a version object.
DART_VERSION = re.compile(rb"(\d+\.\d+\.\d+)(?:\s*\(([^)]{0,40})\))?")


def parse_elf_symbols(raw):
    """Return {name: (offset, size)} from .symtab and .dynsym, without a third party parser.

    Only what is needed: section headers, then the symbol tables whose type is SHT_SYMTAB (2) or
    SHT_DYNSYM (11), with their linked string tables.
    """
    if raw[:4] != b"\x7fELF":
        raise ValueError("not an ELF file")
    is64 = raw[4] == 2
    little = raw[5] == 1
    end = "<" if little else ">"

    if is64:
        e_shoff, = struct.unpack_from(end + "Q", raw, 0x28)
        e_shentsize, e_shnum = struct.unpack_from(end + "HH", raw, 0x3A)
    else:
        e_shoff, = struct.unpack_from(end + "I", raw, 0x20)
        e_shentsize, e_shnum = struct.unpack_from(end + "HH", raw, 0x2E)

    sections = []
    for i in range(e_shnum):
        off = e_shoff + i * e_shentsize
        if is64:
            name, stype, _flags, _addr, sh_off, sh_size, link, _info, _align, entsize = \
                struct.unpack_from(end + "IIQQQQIIQQ", raw, off)
        else:
            name, stype, _flags, _addr, sh_off, sh_size, link, _info, _align, entsize = \
                struct.unpack_from(end + "IIIIIIIIII", raw, off)
        sections.append({"name_off": name, "type": stype, "off": sh_off, "size": sh_size,
                         "link": link, "entsize": entsize})

    out = {}
    for sh in sections:
        if sh["type"] not in (2, 11) or not sh["entsize"]:
            continue
        strtab = sections[sh["link"]]
        strings = raw[strtab["off"]:strtab["off"] + strtab["size"]]
        count = sh["size"] // sh["entsize"]
        for i in range(count):
            o = sh["off"] + i * sh["entsize"]
            if is64:
                st_name, info, other, shndx, st_value, st_size = \
                    struct.unpack_from(end + "IBBHQQ", raw, o)
            else:
                st_name, st_value, st_size, info, other, shndx = \
                    struct.unpack_from(end + "IIIBBH", raw, o)
            if not st_name:
                continue
            endn = strings.find(b"\x00", st_name)
            nm = strings[st_name:endn if endn > 0 else None].decode("utf-8", "replace")
            if nm in SYMBOLS and nm not in out:
                out[nm] = (st_value, st_size)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"no such file: {p}", file=sys.stderr)
        return 1
    raw = p.read_bytes()

    try:
        syms = parse_elf_symbols(raw)
    except ValueError as e:
        print(f"cannot read: {e}", file=sys.stderr)
        return 1

    found = {k: {"offset": v[0], "size": v[1]} for k, v in syms.items()}
    result = {
        "file": p.name,
        "bytes": len(raw),
        "is_flutter": len(found) >= 2,
        "snapshots": found,
        "missing_symbols": [s for s in SYMBOLS if s not in found],
        "note": ("symbols only. The snapshots are not deserialised: that needs an SDK specific parser keyed "
                 "to the exact Dart version, and a parser built against the wrong version produces "
                 "plausible nonsense rather than an error"),
    }

    # A bare semver pattern matches many unrelated strings in a binary, and taking the first one produced
    # 2.2.5 from a compiler artefact in an early run. Prefer a match that carries a channel in parentheses
    # (stable, beta, dev), and report every candidate rather than hiding the disagreement.
    candidates = []
    for m in DART_VERSION.finditer(raw):
        then = m.group(2).decode(errors="replace") if m.group(2) else None
        candidates.append({"version": m.group(1).decode(), "context": then,
                           "channel_like": bool(then and re.match(r"(stable|beta|dev)", then, re.I))})
    pick = next((c for c in candidates if c["channel_like"]), candidates[0] if candidates else None)
    result["dart_version_string"] = pick["version"] if pick else None
    result["dart_version_context"] = pick["context"] if pick else None
    result["version_candidates"] = len(candidates)

    if not result["is_flutter"]:
        result["warning"] = ("fewer than two snapshot symbols found. This may be a Flutter build stripped of "
                            "symbols, in which case the snapshots are present but unnamed, or it may not be "
                            "Flutter at all")

    if args.json:
        print(json.dumps(result, indent=1))
    else:
        for k, v in result.items():
            if k == "snapshots":
                for n, d in v.items():
                    print(f"  {n:36} offset 0x{d['offset']:x} size {d['size']}")
            else:
                print(f"{k:24} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
