#!/usr/bin/env python3
"""
coverage.py: the join between Set D (the denominator) and Set A (what the repos hold).

This is the measurement nobody in this space makes. Every list says it is comprehensive; none defines
what comprehensive would mean, so none can report a fraction. Set D is the denominator, Set A is the
artefacts, and this file records, per factor, whether anything in A gives a procedure AND an oracle for
that factor.

A mention is not coverage. The grading is deliberately strict:

  L0  absent      nothing in A addresses the factor
  L1  named       a tool or entry mentions the concept, with no procedure and no oracle
  L2  procedure   an entry or pattern states a procedure and an oracle, so a competent reader could test it
  L3  observed    a lab exists here and demonstrates it

Only L2 and L3 count as coverage. L1 is recorded because knowing that a concept is named but not
operationalised is useful, but it is not counted.

Records live in data/coverage/coverage.jsonl, one per factor id:
  {"factor": "L01-001", "lens": "L01", "level": "L0"|"L1"|"L2"|"L3",
   "covered_by": ["d16-jwt-weakness"], "basis": "entry"|"pattern"|"tool"|"lab"|"none", "note": "..."}

Commands:
  python3 scripts/coverage.py --stats              coverage by lens and overall
  python3 scripts/coverage.py --pending [L01]      factors with no record yet
  python3 scripts/coverage.py --search "sidechannel cache"   candidate artefacts, with oracle presence
  python3 scripts/coverage.py --validate           every factor has a record, ids resolve, basis consistent
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEN = ROOT / "data" / "denominator"
COV = ROOT / "data" / "coverage" / "coverage.jsonl"
LEVELS = ("L0", "L1", "L2", "L3")
BASES = ("entry", "pattern", "tool", "lab", "none")


def factors():
    out = []
    for p in sorted(DEN.glob("L*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for f in d.get("factors", []):
            out.append({"lens": d["lens"], "lens_name": d["name"], **f})
    return out


def entries():
    out = []
    for f in sorted((ROOT / "data" / "domains").glob("D*.json")):
        if f.stem.endswith(".index"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        for e in d.get("entries", []):
            out.append({"id": e.get("id"), "kind": "entry", "domain": d.get("id"),
                        "name": e.get("name"), "role": e.get("role"),
                        "oracle": bool(e.get("oracle")), "pre": bool(e.get("preconditions"))})
    return out


def patterns():
    atlas = ROOT.parent / "web-attack-atlas"
    out = []
    for f in sorted(atlas.glob("waves/*/patterns.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                p = json.loads(line)
                out.append({"id": p["id"], "kind": "pattern", "wave": f.parent.name,
                            "name": p.get("title"), "role": p.get("target_state"),
                            "oracle": bool(p.get("oracle")), "pre": bool(p.get("preconditions"))})
    return out


def records():
    if not COV.exists():
        return {}
    out = {}
    for line in COV.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["factor"]] = r
    return out


def authored_files():
    return sorted((ROOT / "data" / "coverage").glob("L*.json"))


def cmd_build(args):
    """Expand the authored per lens verdicts into the uniform ledger.

    Authoring is compact on purpose: a lens declares a default level and a reason, then lists only the
    factors that differ. The ledger is uniform so the validator can be strict.
    """
    out = []
    problems = []
    for f in authored_files():
        d = json.loads(f.read_text(encoding="utf-8"))
        lens = d["lens"]
        default = d.get("default", "L0")
        reason = d.get("reason", "")
        exc = d.get("exceptions") or {}
        lens_factors = [x["id"] for x in factors() if x["lens"] == lens]
        if not lens_factors:
            problems.append(f"{lens}: no factors for this lens")
            continue
        for fid in lens_factors:
            if fid in exc:
                e = exc[fid]
                out.append({"factor": fid, "lens": lens, "level": e["level"],
                            "covered_by": e.get("covered_by") or [],
                            "basis": e.get("basis") or ("entry" if e.get("covered_by") else "none"),
                            "note": e.get("note") or ""})
            else:
                out.append({"factor": fid, "lens": lens, "level": default,
                            "covered_by": [], "basis": "none", "note": reason})
    COV.parent.mkdir(parents=True, exist_ok=True)
    COV.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), encoding="utf-8")
    print(f"wrote {len(out)} coverage record(s) from {len(authored_files())} lens file(s)")
    for p in problems:
        print(f"  {p}", file=sys.stderr)
    return 1 if problems else 0


def cmd_stats(args):
    fs = factors()
    rs = records()
    by_lens = {}
    for f in fs:
        by_lens.setdefault(f["lens"], {"total": 0, "done": 0, "L2": 0, "L3": 0})
        by_lens[f["lens"]]["total"] += 1
        r = rs.get(f["id"])
        if r:
            by_lens[f["lens"]]["done"] += 1
            if r["level"] in ("L2", "L3"):
                by_lens[f["lens"]]["L2"] += 1
            if r["level"] == "L3":
                by_lens[f["lens"]]["L3"] += 1

    print(f"{'lens':6s} {'name':24s} {'factors':>7s} {'mapped':>6s} {'covered':>7s} {'observed':>8s}")
    tot = {"total": 0, "done": 0, "L2": 0, "L3": 0}
    for lens in sorted(by_lens):
        v = by_lens[lens]
        name = next((f["lens_name"] for f in fs if f["lens"] == lens), "")
        print(f"{lens:6s} {name[:24]:24s} {v['total']:7d} {v['done']:6d} {v['L2']:7d} {v['L3']:8d}")
        for k in tot:
            tot[k] += v[k]
    print()
    print(f"{'total':31s} {tot['total']:7d} {tot['done']:6d} {tot['L2']:7d} {tot['L3']:8d}")
    if tot["total"]:
        print(f"\ncoverage at L2 or better: {100 * tot['L2'] / tot['total']:.1f}% "
              f"({tot['L2']} of {tot['total']})")
        print(f"observed:                 {100 * tot['L3'] / tot['total']:.1f}%")
    return 0


def cmd_pending(args):
    rs = records()
    todo = [f for f in factors() if f["id"] not in rs]
    if args.pending and args.pending != "all":
        todo = [f for f in todo if f["lens"] == args.pending]
    print(f"{len(todo)} unmapped factor(s)")
    for f in todo[:80]:
        print(f"  {f['id']}  {f['name'][:44]:46s} {f['observable'][:70]}")
    return 0


def cmd_search(args):
    terms = [t.lower() for t in args.search.split()]
    pool = entries() + patterns()
    hits = []
    for a in pool:
        blob = " ".join(str(a.get(k) or "") for k in ("name", "role")).lower()
        score = sum(1 for t in terms if t in blob)
        # require every term by default: one loose term matching "server side" is not a candidate
        need = 1 if getattr(args, "any", False) else len(terms)
        if score >= need:
            hits.append((score, a))
    hits.sort(key=lambda x: (-x[0], x[1]["id"]))
    print(f"{len(hits)} candidate(s) for {terms}")
    for score, a in hits[:40]:
        flag = "P+O" if (a["oracle"] and a["pre"]) else ("O" if a["oracle"] else "-")
        print(f"  {score} {flag} {a['id']:22s} {str(a['name'])[:46]:48s} {str(a['role'])[:60]}")
    return 0


def cmd_validate(args):
    fs = factors()
    rs = records()
    arts = {a["id"] for a in entries() + patterns()}
    problems = []
    for f in fs:
        r = rs.get(f["id"])
        if not r:
            problems.append(f"{f['id']}: no coverage record")
            continue
        if r.get("lens") != f["lens"]:
            problems.append(f"{f['id']}: lens {r.get('lens')} does not match {f['lens']}")
        if r.get("level") not in LEVELS:
            problems.append(f"{f['id']}: level {r.get('level')!r} not in {LEVELS}")
        if r.get("basis") not in BASES:
            problems.append(f"{f['id']}: basis {r.get('basis')!r} not in {BASES}")
        if r.get("level") in ("L2", "L3") and not r.get("covered_by"):
            problems.append(f"{f['id']}: claims {r['level']} with no artefact")
        if r.get("level") == "L0" and r.get("covered_by"):
            problems.append(f"{f['id']}: level L0 but names {len(r['covered_by'])} artefacts")
        for a in r.get("covered_by") or []:
            if a not in arts:
                problems.append(f"{f['id']}: covered_by {a!r} does not exist in either repo")
    orphan = set(rs) - {f["id"] for f in fs}
    for o in sorted(orphan):
        problems.append(f"{o}: coverage record for a factor that does not exist")

    mapped = sum(1 for f in fs if f["id"] in rs)
    print(f"factors {len(fs)}, mapped {mapped}, records {len(rs)}")
    if problems:
        print(f"\n{len(problems)} problem(s):", file=sys.stderr)
        for p in problems[:40]:
            print(f"  {p}", file=sys.stderr)
        if len(problems) > 40:
            print(f"  ... and {len(problems) - 40} more", file=sys.stderr)
        return 1
    print("\nall invariants hold")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--pending", nargs="?", const="all")
    ap.add_argument("--search")
    ap.add_argument("--any", action="store_true", help="match any term rather than all")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--build", action="store_true")
    args = ap.parse_args()

    if args.build:
        return cmd_build(args)
    if args.stats:
        return cmd_stats(args)
    if args.pending:
        return cmd_pending(args)
    if args.search:
        return cmd_search(args)
    if args.validate:
        return cmd_validate(args)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
