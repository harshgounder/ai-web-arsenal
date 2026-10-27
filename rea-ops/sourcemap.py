#!/usr/bin/env python3
"""
sourcemap.py: recover original sources from a JavaScript bundle, and say plainly when it cannot.

Why this exists. D31 gap ten. A production bundle is the primary artefact in almost every web engagement,
and the map is what turns minified code back into something a person can reason about. Sometimes it is
published, sometimes it is only inline, and sometimes it is absent and the honest answer is that the
original sources are not recoverable.

Recovery order, tried in this order and reported per step:

  1. an inline data: URI map inside the file
  2. an external map at the sourceMappingURL, relative to the bundle
  3. sourcesContent embedded in whichever map was found
  4. no map at all: carve the bundle into module sized sections and report that this is a heuristic

The fourth step is not recovery and the output says so. It gives a reader structure: how many module
boundaries the bundler left, which chunk ids appear, and where the legal comments are. It does not give
original variable names, and any tool claiming otherwise without a map is guessing.

Usage:
  python3 rea-ops/sourcemap.py bundle.js --sources
  python3 rea-ops/sourcemap.py bundle.js --extract out/
  python3 rea-ops/sourcemap.py bundle.js --lookup 1 4821
  python3 rea-ops/sourcemap.py bundle.js --carve
"""
import argparse
import base64
import json
import re
import sys
from pathlib import Path

B64 = {c: i for i, c in enumerate(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/")}
MAP_COMMENT = re.compile(r"[#@]\s*sourceMappingURL=([^\s'\"*]+)")


def decode_vlq(segment):
    """Source map segments are base64 VLQ, each value carrying a sign in its low bit."""
    out = []
    shift = 0
    value = 0
    for ch in segment:
        digit = B64.get(ch)
        if digit is None:
            raise ValueError(f"bad base64 char {ch!r}")
        cont = digit & 32
        digit &= 31
        value += digit << shift
        if cont:
            shift += 5
        else:
            negative = value & 1
            value >>= 1
            out.append(-value if negative else value)
            value = 0
            shift = 0
    return out


def find_map(bundle_path, text):
    """Return (kind, raw_text, note) for the best map available, or (None, None, reason)."""
    m = None
    for m in MAP_COMMENT.finditer(text):
        pass  # last one wins, which is what a browser uses
    if not m:
        return None, None, "no sourceMappingURL comment in the file"

    url = m.group(1).strip()
    if url.startswith("data:"):
        try:
            header, _, payload = url.partition(",")
            if ";base64" in header:
                raw = base64.b64decode(payload + "=" * (-len(payload) % 4)).decode("utf-8", "replace")
            else:
                raw = payload
            return "inline", raw, "map embedded in a data URI"
        except Exception as e:
            return None, None, f"inline map could not be decoded: {e}"

    candidate = (bundle_path.parent / url).resolve()
    if candidate.exists():
        return "external", candidate.read_text(encoding="utf-8", errors="replace"), str(candidate)
    return None, None, f"sourceMappingURL points at {url}, which is not present next to the bundle"


def flatten_map(doc):
    """A regular map has mappings; an indexed map has sections. Return a uniform source list."""
    sources, contents = [], {}

    def take(d):
        for i, s in enumerate(d.get("sources") or []):
            if s not in sources:
                sources.append(s)
            sc = d.get("sourcesContent") or []
            if i < len(sc) and sc[i] is not None:
                contents[s] = sc[i]

    if "sections" in doc:
        for sec in doc["sections"]:
            take(sec.get("map") or {})
    else:
        take(doc)
    return sources, contents


def lookup(doc, line, col):
    """Resolve a generated position to an original one. Returns None when the line has no mapping."""
    if "sections" in doc:
        for sec in doc["sections"]:
            off = (sec.get("offset") or {})
            if off.get("line", 0) <= line:
                sub = sec.get("map") or {}
                r = lookup(sub, line - off.get("line", 0), col - off.get("column", 0))
                if r:
                    return r
        return None

    sources = doc.get("sources") or []
    lines = (doc.get("mappings") or "").split(";")
    if line >= len(lines):
        return None
    src = src_line = src_col = 0
    gen_col = 0
    best = None
    for seg in lines[line].split(","):
        if not seg:
            continue
        vals = decode_vlq(seg)
        if not vals:
            continue
        gen_col += vals[0]
        if len(vals) >= 4:
            src += vals[1]
            src_line += vals[2]
            src_col += vals[3]
            if gen_col <= col:
                best = {"generated_column": gen_col,
                        "source": sources[src] if 0 <= src < len(sources) else None,
                        "original_line": src_line, "original_column": src_col}
            else:
                break
    return best


def carve(text):
    """No map. Report structure, and be explicit that this is not source recovery."""
    modules = re.findall(r"/\*{2,}\s*\(?webpack\)?\s*\*/|/\*\*\*/|\b__webpack_require__\b|\bwebpackChunk", text)
    chunks = sorted(set(re.findall(r"webpackChunk([A-Za-z0-9_]+)", text)))
    legal = re.findall(r"/\*!(?:\s*)([^*]{0,120})", text)
    paths = sorted(set(re.findall(r"['\"]([./][A-Za-z0-9_./-]{2,60})['\"]", text)))[:40]
    return {
        "confidence": "low",
        "recovered": "structure only, not original sources",
        "module_boundary_markers": len(modules),
        "chunk_names": chunks,
        "legal_comments": [c.strip()[:100] for c in legal[:10]],
        "path_like_strings": paths,
        "note": ("without a map the original variable names and comments are gone. This lists the bundler's "
                 "own boundary markers and any path-like literals, which is enough to orient a reader and "
                 "not enough to reconstruct a module"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle")
    ap.add_argument("--sources", action="store_true")
    ap.add_argument("--extract", metavar="DIR")
    ap.add_argument("--lookup", nargs=2, type=int, metavar=("LINE", "COL"))
    ap.add_argument("--carve", action="store_true")
    args = ap.parse_args()

    p = Path(args.bundle)
    if not p.exists():
        print(f"no such file: {p}", file=sys.stderr)
        return 1
    text = p.read_text(encoding="utf-8", errors="replace")

    kind, raw, note = find_map(p, text)
    if kind is None:
        if args.carve or not (args.sources or args.extract or args.lookup):
            print(json.dumps({"bundle": p.name, "map": None, "reason": note, **carve(text)}, indent=1))
            return 0
        print(f"no map: {note}", file=sys.stderr)
        return 2

    try:
        doc = json.loads(raw)
    except Exception as e:
        print(f"map found ({kind}) but does not parse: {e}", file=sys.stderr)
        return 1

    sources, contents = flatten_map(doc)
    out = {"bundle": p.name, "map_kind": kind, "map_note": note,
           "sources": len(sources), "with_embedded_content": len(contents),
           "recovered": "original sources available" if contents else "names only, no content"}

    if args.lookup:
        line, col = args.lookup
        out["lookup"] = lookup(doc, line, col) or "no mapping at that position"

    if args.sources or not (args.extract or args.lookup):
        out["source_list"] = sources[:200]

    if args.extract:
        dest = Path(args.extract)
        dest.mkdir(parents=True, exist_ok=True)
        written = 0
        for name in sources:
            if name not in contents:
                continue
            rel = Path(name.replace("webpack://", "").lstrip("/"))
            if ".." in rel.parts:
                continue                      # a map is attacker supplied too
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(contents[name], encoding="utf-8")
            written += 1
        out["extracted"] = written
        out["out"] = str(dest)

    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
