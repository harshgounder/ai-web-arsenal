#!/usr/bin/env python3
"""
hermes.py: identify a Hermes bytecode bundle and report its header.

Why this exists, and why it is deliberately small. D31 gap four. Hermes is the JavaScript engine React
Native ships, so a compiled `.hbc` bundle is the logic layer of most React Native apps, and there was no
reader here at all.

What this does: validates the magic, reads the version, and reports the header fields that are stable
across versions: source hash, declared file length, function count, identifier count, string count and
string storage size. That is the triage question, and it is answerable without touching a single table.

What this refuses to do: walk the function, string or object key tables. Those offsets move between
versions, and a reader that guesses them produces plausible nonsense from a real file, which is worse than
no reader. This one reports the version it does not know and stops.

If the version is outside the range this file claims to understand, it says so and prints the header
anyway, because the magic and version are still true even when the layout above them is not.

Usage:
  python3 rea-ops/hermes.py bundle.hbc
  python3 rea-ops/hermes.py bundle.hbc --json
"""
import argparse
import json
import struct
import sys
from pathlib import Path

# Hermes bytecode files start with this 64 bit little endian value.
MAGIC = 0xC61FBB1E
HEADER_BYTES = 48  # the fields this reader interprets; the full header is longer

# Versions this reader has been written against. Outside the range it reports the header and refuses to
# interpret anything further, because a wrong offset does not fail, it produces a plausible number.
KNOWN_MIN, KNOWN_MAX = 70, 99


def read_header(raw):
    if len(raw) < 16:
        raise ValueError(f"too short for a header: {len(raw)} bytes")
    magic, version, source_hash, file_length = struct.unpack_from("<QIII", raw, 0)
    if (magic & 0xFFFFFFFF) != MAGIC:
        raise ValueError(
            f"not Hermes bytecode: first 8 bytes are 0x{magic:016x}, expected the low 32 bits to be "
            f"0x{MAGIC:08x}. A React Native app that ships this in a bundle may have a different magic")
    out = {
        "magic": f"0x{magic:016x}",
        "version": version,
        "known_version": KNOWN_MIN <= version <= KNOWN_MAX,
        "source_hash": f"0x{source_hash:08x}",
        "declared_file_length": file_length,
        "actual_file_length": len(raw),
        "length_matches": file_length == len(raw),
    }
    if len(raw) >= HEADER_BYTES:
        (global_code, funcs, kinds, identifiers, strings, overflow, string_storage) = \
            struct.unpack_from("<IIIIIII", raw, 20)
        out.update({
            "global_code_index": global_code,
            "function_count": funcs,
            "string_kind_count": kinds,
            "identifier_count": identifiers,
            "string_count": strings,
            "overflow_string_count": overflow,
            "string_storage_bytes": string_storage,
        })
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
        h = read_header(raw)
    except ValueError as e:
        print(f"cannot read: {e}", file=sys.stderr)
        return 1

    h["file"] = p.name
    h["note"] = ("header only. The function, string and object key tables are not walked, because their "
                 "offsets move between versions and a guessed offset produces a plausible number rather "
                 "than an error")
    if not h["known_version"]:
        h["warning"] = (f"version {h['version']} is outside the {KNOWN_MIN} to {KNOWN_MAX} range this "
                        "reader was written against. The header fields above are still read from fixed "
                        "offsets that have been stable, but nothing beyond them is attempted")

    if args.json:
        print(json.dumps(h, indent=1))
    else:
        for k, v in h.items():
            print(f"{k:24} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
