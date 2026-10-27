#!/usr/bin/env python3
"""
check-claims.py: run every claim in data/claims.yaml and report which no longer hold.

Why this exists. Ten defects in this project were numbers that drifted while the prose stayed behind,
and every one of them was found by someone recomputing by accident. A claim that is not executed is a
belief. This turns beliefs into checks.

Divison of labour: `recheck.py` covers the numbers that `readme-stats.py` derives. This covers the rest:
facts with no stats key, structural invariants, and any superlative the documents claim about
themselves.

Exit codes: 0 when every claim holds, 1 when any claim fails or errors.
Run with --list for the claims alone, --json for machine output, --quiet for exit code only.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATLAS = ROOT.parent / "web-attack-atlas"
CLAIMS = ROOT / "data" / "claims.yaml"
ATLAS_PRESENT = (ROOT.parent / "web-attack-atlas" / "data" / "atoms.json").exists()

# These claims read the companion repo. Without it they are not false, they are unanswerable, and those
# are different states. A fresh clone with no sibling must not report the repo as broken.
ATLAS_CLAIMS = {"C081", "C083", "C090", "C113"}

# Words the house rules ban. A document that uses them reads as machine-written, and this repo is
# supposed to read like a person who did the work.
BANNED = (r"\b(delve|leverage|leveraging|unlock|robust|synergy|seamless|elevate|empower|foster|"
          r"showcase|cutting-edge|state-of-the-art|game-changer|revolutioni[sz]e|transformative|"
          r"holistic|multifaceted|nuanced|intricate|meticulous|underscore|pivotal|paramount|notably|"
          r"arguably|undoubtedly|indeed|ultimately|essentially|in conclusion|it's worth noting|"
          r"it's important to note|plays a crucial role|stands as a testament|in the realm of|"
          r"paradigm shift|move the needle|deep dive|best practice|close the loop|"
          r"leave no stone unturned|read between the lines|the tip of the iceberg)\b")

# A sentence that says this repo is the only, the best, the most complete, or unlike everything else
# is a claim, and claims get checked. Each invited phrase must appear in JUSTIFIED below with a reason,
# or the check fails.
SUPERLATIVE = re.compile(
    r"(the only (?:repo|list|collection|project|arsenal)|the most (?:complete|exhaustive|comprehensive)|"
    r"the best (?:repo|list|arsenal|collection)|nobody else|no one else|unlike any|unlike every|"
    r"never been done|has never been done|not been done before|world's (?:first|best|most)|"
    r"the definitive|unrivalled|unrivaled|second to none|"
    r"everything (?:anyone|you) could)",
    re.I,
)

# A line that makes a comparative claim on purpose can say so, with a reason, on the line or the one
# above it: <!-- claim-ok: reason -->
CLAIM_OK = "claim-ok:"

# Justified uses. Keyed by the phrase found, lowercase. Anything not listed fails C093.
JUSTIFIED = {}


def docs():
    """The authored document set. Data files are excluded: harvested text is not written by us."""
    out = []
    for name in ("README.md", "RECHECK.md", "PLAN.md", "AUTHORING.md", "RESUME.md",
                 "SCOPE-v1.md", "BOOTSTRAP.md", "LOG.md", "CONTRIBUTING.md", "SECURITY.md"):
        p = ROOT / name
        if p.exists():
            out.append(p)
    out.extend(sorted((ROOT / "docs").glob("*.md")))
    return out


def load_yaml(path):
    text = path.read_text(encoding="utf-8")
    try:
        import yaml
        return yaml.safe_load(text)
    except ImportError:
        return mini_yaml(text)


def mini_yaml(text):
    """Enough YAML for this file if PyYAML is absent: a list of mappings with scalar values."""
    claims, cur, key = [], None, None
    for raw in text.splitlines():
        line = raw.split("  #")[0].rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - "):
            if cur:
                claims.append(cur)
            cur = {}
            rest = line[4:]
            if ":" in rest:
                k, v = rest.split(":", 1)
                cur[k.strip()] = v.strip().strip('"')
        elif line.startswith("    ") and cur is not None and ":" in line:
            k, v = line.strip().split(":", 1)
            cur[k.strip()] = v.strip().strip('"')
    if cur:
        claims.append(cur)
    return {"claims": claims}


def files(pattern):
    return sorted(ROOT.glob(pattern))


def count_sh(rel):
    p = ROOT / rel
    if not p.exists():
        p = ATLAS / rel
    return sum(1 for l in p.read_text(encoding="utf-8").splitlines() if l.strip())


def atlas_pattern_files():
    return sorted(ATLAS.glob("waves/*/patterns.jsonl"))


def atlas_patterns():
    out = []
    for f in atlas_pattern_files():
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
    return out


def atlas_gate_ok():
    try:
        r = subprocess.run([sys.executable, "scripts/render-patterns.py", "--check"],
                           cwd=ATLAS, capture_output=True, text=True, timeout=120)
        return r.returncode == 0 and "all pass" in (r.stdout + r.stderr)
    except Exception:
        return False


def domains():
    out = []
    for f in sorted((ROOT / "data" / "domains").glob("D*.json")):
        if f.stem.endswith(".index"):
            continue
        out.append(json.loads(f.read_text(encoding="utf-8")))
    return out


def entries():
    out = []
    for d in domains():
        out.extend(d.get("entries", []))
    return out


def unjustified_superlatives():
    """Superlative hits with no justification on the line, the line above, or in JUSTIFIED."""
    hits = []
    for p in docs():
        lines = p.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines, 1):
            if CLAIM_OK in line or (i > 1 and CLAIM_OK in lines[i - 2]):
                continue
            for m in SUPERLATIVE.finditer(line):
                if m.group(0).lower() not in JUSTIFIED:
                    hits.append((p.name, i, m.group(0), line.strip()[:110]))
    return hits


def restatement_hits(threshold=0.5):
    """Entries that restate an atlas pattern title rather than pointing at it.

    The documented rule is "never restate a pattern", and like the join key it was asserted without being
    measured. Token overlap over the title and the entry's role is crude but it catches copying, which is
    the failure the rule exists to prevent.
    """
    import json as _j
    import re as _re

    def toks(x):
        return {w for w in _re.findall(r"[a-z]{4,}", (x or "").lower())}

    pats = []
    for f in sorted(ATLAS.glob("waves/*/patterns.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                p = _j.loads(line)
                pats.append((p["id"], toks(p.get("title"))))
    out = []
    for e in entries():
        et = toks((e.get("role") or "") + " " + (e.get("name") or ""))
        if not et:
            continue
        for pid, ptk in pats:
            if not ptk:
                continue
            j = len(ptk & et) / len(ptk | et)
            if j > threshold:
                out.append((pid, e.get("id"), round(j, 2)))
    return out


def read_transcript():
    """Every claim statement found in the documents header block, if present."""
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--only", help="run one claim id")
    ap.add_argument("--require-atlas", action="store_true",
                    help="treat a missing companion repo as failure rather than skip")
    args = ap.parse_args()

    spec = load_yaml(CLAIMS)
    claims = spec.get("claims") or []
    if not claims:
        print("claims.yaml parsed to zero claims, which cannot be right", file=sys.stderr)
        return 1

    stats = {}
    r = subprocess.run([sys.executable, "scripts/readme-stats.py"], cwd=ROOT,
                       capture_output=True, text=True, timeout=300)
    for line in r.stdout.splitlines():
        parts = line.strip().split(" ", 1)
        if len(parts) == 2:
            k, v = parts
            if v.strip().isdigit():
                stats[k] = int(v.strip())

    import builtins
    safe = {k: getattr(builtins, k) for k in
            ("len", "sum", "all", "any", "sorted", "set", "round", "str", "int", "bool",
             "list", "dict", "tuple", "range", "min", "max", "enumerate", "zip", "abs",
             "isinstance", "hasattr", "getattr", "repr")}

    ns = {
        "ROOT": ROOT, "ATLAS": ATLAS, "re": re, "json": json, "stats": stats,
        "rows": lambda rel: [json.loads(l) for l in
                             (ROOT / rel).read_text(encoding="utf-8").splitlines() if l.strip()],
        "load": lambda rel: json.loads((ROOT / rel).read_text(encoding="utf-8")),
        "load_manifest": lambda: __import__("yaml").safe_load(
            (ROOT / "manifest" / "tools.yaml").read_text(encoding="utf-8")),
        "count_sh": count_sh, "files": files, "exists": lambda rel: (ROOT / rel).exists(),
        "domains": domains, "entries": entries,
        "atlas_pattern_files": atlas_pattern_files, "atlas_patterns": atlas_patterns,
        "atlas_gate_ok": atlas_gate_ok,
        "docs_text": lambda: "\n".join(p.read_text(encoding="utf-8") for p in docs()),
        "BANNED": BANNED,
        "unjustified_superlatives": unjustified_superlatives,
        "restatement_hits": restatement_hits,
        "libsh": lambda: (ROOT / "bootstrap" / "lib.sh").read_text(encoding="utf-8"),
    }

    if args.list:
        for c in claims:
            print(f"{c.get('id', '?'):6s} {c.get('statement', '')}")
        return 0

    results = []
    skipped = []
    for c in claims:
        cid = c.get("id", "?")
        if args.only and cid != args.only:
            continue
        if cid in ATLAS_CLAIMS and not ATLAS_PRESENT:
            if args.require_atlas:
                results.append((cid, "ERROR", c.get("statement", ""),
                                "needs ../web-attack-atlas, which is not present"))
            else:
                skipped.append((cid, c.get("statement", "")))
            continue
        expr = c.get("check", "")
        try:
            # Names must live in globals, not locals: a comprehension inside the expression opens a
            # new scope and resolves free names against globals, so a locals-only namespace breaks
            # every claim that uses all() over a generator.
            g = dict(ns)
            g["__builtins__"] = safe
            ok = bool(eval(expr, g))  # noqa: S307, fixed input file
            results.append((cid, "PASS" if ok else "FAIL", c.get("statement", ""), ""))
        except Exception as e:
            results.append((cid, "ERROR", c.get("statement", ""), f"{type(e).__name__}: {e}"))

    failed = [x for x in results if x[1] != "PASS"]

    if args.json:
        print(json.dumps([{"id": a, "status": b, "statement": c, "detail": d}
                          for a, b, c, d in results], indent=1))
    elif not args.quiet:
        w = max((len(c) for _, _, c, _ in results), default=40)
        for cid, status, stmt, detail in results:
            mark = {"PASS": "PASS", "FAIL": "FAIL", "ERROR": "ERR "}[status]
            print(f"  {mark}  {cid:6s} {stmt[:w][:96]:96s} {detail[:60]}")
        print()
        counts = {}
        for _, s, _, _ in results:
            counts[s] = counts.get(s, 0) + 1
        print(f"claims: {len(results)}  " +
              "  ".join(f"{k.lower()} {v}" for k, v in sorted(counts.items())))
        if skipped:
            print(f"\nskipped {len(skipped)} claim(s) that need the companion repo: "
                  f"{', '.join(s[0] for s in skipped)}")
            print("  clone it beside this one, or pass --require-atlas to fail instead:")
            print(f"  git clone https://github.com/harshgounder/web-attack-atlas {ROOT.parent}/web-attack-atlas")
        if failed:
            print("\nA failing claim is a false statement in the repository. Fix the document or the")
            print("check, but do not delete the claim: the deletion is the defect.")

    if failed and not args.json and not args.quiet:
        for name, line_no, phrase, text in unjustified_superlatives():
            print(f"\n  unqualified superlative {phrase!r} at {name}:{line_no}: {text}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
