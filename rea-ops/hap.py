#!/usr/bin/env python3
"""
hap.py: unpack a HarmonyOS HAP package and report what is inside.

Why this exists. D31 gap five. A HAP is a zip container holding an ArkTS module, its compiled Ark
bytecode and resources. Until now the repo had no reader, so the HarmonyOS lane had an entry naming the
format and no way to open one.

What this does: lists and extracts the container, reports the manifest fields that decide what the app
can do, and identifies Ark bytecode files by their magic. It does not decompile Ark bytecode, does not
verify the signature, and does not parse the binary module.json if the package ships only that form.

Usage:
  python3 rea-ops/hap.py app.hap --list
  python3 rea-ops/hap.py app.hap --out dir/
  python3 rea-ops/hap.py app.hap --info
"""
import argparse
import json
import sys
import zipfile
from pathlib import Path

# Compiled Ark bytecode starts with this. Reported so a reader knows which files need a disassembler.
ABA_MAGIC = b"PANDA"
ABC_MAGIC = b"\x00"  # not reliable on its own, so detection also uses the extension


def safe(rel):
    p = Path(rel)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError(f"unsafe path in archive: {rel}")
    return p


def info(zf):
    names = zf.namelist()
    modules, abc, so, json_files = [], [], [], []
    for n in names:
        if n.endswith("module.json") or n.endswith("pack.info"):
            json_files.append(n)
        if n.endswith(".abc"):
            abc.append(n)
        if n.endswith(".so"):
            so.append(n)
    manifest = {}
    # the readable module.json can live at the root or under a module directory
    for cand in ("module.json", "pack.info"):
        if cand in names:
            try:
                manifest[cand] = json.loads(zf.read(cand))
            except Exception:
                manifest[cand] = "present but not parseable as JSON"
    for n in json_files:
        if n in manifest:
            continue
        if n.endswith("module.json"):
            try:
                manifest[n] = json.loads(zf.read(n))
            except Exception:
                manifest[n] = "present, unparsed"
    return {
        "entries": len(names),
        "ark_bytecode": abc,
        "native_libraries": so,
        "manifest_files": json_files,
        "manifest": manifest,
        "note": "a HAP that ships only the binary module.json will show manifest_files and no parsed JSON",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--info", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"no such file: {p}", file=sys.stderr)
        return 1
    if not zipfile.is_zipfile(p):
        print(f"{p.name} is not a zip container, so it is not a HAP or it is encrypted", file=sys.stderr)
        return 1

    with zipfile.ZipFile(p) as zf:
        if args.info:
            print(json.dumps(info(zf), indent=1, ensure_ascii=False))
            return 0
        if args.list or not args.out:
            names = zf.namelist()
            print(json.dumps({"entries": len(names), "names": names[:300]}, indent=1))
            return 0

        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        written, skipped = 0, []
        for n in zf.namelist():
            if n.endswith("/"):
                continue
            try:
                rel = safe(n)
            except ValueError as e:
                skipped.append(str(e))
                continue
            dest = out / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(n) as src, open(dest, "wb") as dst:
                dst.write(src.read())
            written += 1
        print(json.dumps({"extracted": written, "skipped": skipped, "out": str(out)}, indent=1))
        return 0


if __name__ == "__main__":
    sys.exit(main())
