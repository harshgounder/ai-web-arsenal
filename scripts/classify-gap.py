#!/usr/bin/env python3
"""
classify-gap.py: put every uncovered factor into a class that decides what to do about it.

Phase 2 produced a number. This phase produces a plan, because "893 factors uncovered" is not
actionable until you know which ones can be reached and how.

Classes, following the method in PLAN.md:

  I   derivable with noise. The mechanism is in public source, a specification or a vendor document.
      It can be written from what exists, with an approximation error equal to the author's misreading.
      Cost: authoring time. No lab needed.
  II  inferable from structure. The factor is a property of a running system. Its effect is only
      visible under a probe or in a paper's measurement. Cost: a lab and a target.
  III genuinely unavailable. A fact about a specific private organisation or unpublished research.
      No defensible proxy exists. Cost: impossible from outside.

The default rule is mechanical and comes from the `evidence` field on each factor, which was authored
deliberately when Set D was written:

  source          -> I    (the mechanism is published)
  paper or run    -> II   (needs measurement against a system)

Exceptions are authored per lens where the rule is wrong, and they are almost all Class III: governance
facts such as whether a team has an exception register are not in any public source and are not
revealed by any probe.

Output: data/gap/classification.jsonl, data/gap/SUMMARY.json

Commands:
  python3 scripts/classify-gap.py            build the ledger
  python3 scripts/classify-gap.py --stats    class counts and the ceiling
  python3 scripts/classify-gap.py --validate  every uncovered factor classified exactly once
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEN = ROOT / "data" / "denominator"
GAPDIR = ROOT / "data" / "gap"
COV = ROOT / "data" / "coverage" / "coverage.jsonl"
OUT = GAPDIR / "classification.jsonl"
SUMMARY = GAPDIR / "SUMMARY.json"

CLASSES = {"I": "derivable with noise", "II": "inferable from structure", "III": "genuinely unavailable"}
COST = {"I": "authoring", "II": "lab", "III": "impossible"}
RULE = {"source": "I", "paper": "II", "run": "II"}


def factors():
    out = []
    for p in sorted(DEN.glob("L*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for f in d.get("factors", []):
            out.append({"lens": d["lens"], "lens_name": d["name"], **f})
    return out


def coverage():
    if not COV.exists():
        return {}
    return {json.loads(l)["factor"]: json.loads(l)
            for l in COV.read_text(encoding="utf-8").splitlines() if l.strip()}


def exceptions():
    """Lens files may override the mechanical rule. Keyed by factor id."""
    out = {}
    for p in sorted(GAPDIR.glob("L*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for fid, rec in (d.get("exceptions") or {}).items():
            out[fid] = {**rec, "lens": d["lens"]}
    return out


def build():
    cov = coverage()
    exc = exceptions()
    rows = []
    problems = []
    for f in factors():
        c = cov.get(f["id"])
        if c and c["level"] in ("L2", "L3"):
            continue  # already covered, not part of the gap
        e = exc.get(f["id"])
        if e:
            cls = e["class"]
            why = e.get("reason", "")
        else:
            cls = RULE.get(f.get("evidence"), "II")
            why = f"evidence is {f.get('evidence')}"
            if cls == "I":
                why += ", so the mechanism is published and can be written"
            else:
                why += ", so it needs a probe or a lab"
        if cls not in CLASSES:
            problems.append(f"{f['id']}: class {cls!r} not in {sorted(CLASSES)}")
        rows.append({"factor": f["id"], "lens": f["lens"], "class": cls, "cost": COST.get(cls),
                     "evidence": f.get("evidence"), "reason": why})

    known = {f["id"] for f in factors()}
    for fid in exc:
        if fid not in known:
            problems.append(f"exception names {fid}, which is not a factor")
        elif fid not in {r["factor"] for r in rows}:
            problems.append(f"exception names {fid}, which is already covered, so it does nothing")

    GAPDIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")

    total = len(factors())
    covered = total - len(rows)
    by_class = {}
    for r in rows:
        by_class[r["class"]] = by_class.get(r["class"], 0) + 1
    summary = {
        "generated_at": "2026-10-27",
        "factors_total": total,
        "covered_l2_plus": covered,
        "gap_total": len(rows),
        "gap_by_class": by_class,
        "cost_by_class": {k: COST[k] for k in by_class},
        "reachable_by_authoring": by_class.get("I", 0),
        "reachable_by_lab": by_class.get("II", 0),
        "unavailable": by_class.get("III", 0),
        "ceiling_pct": round(100.0 * (total - by_class.get("III", 0)) / total, 1),
        "ceiling_note": "share of Set D that any collection could reach from outside, given unlimited "
                        "authoring and lab time. It is not a forecast of what this repo will reach.",
    }
    SUMMARY.write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")

    print(f"gap {len(rows)} of {total} factors ({covered} already at L2+)")
    for k in ("I", "II", "III"):
        print(f"  {k:3s} {by_class.get(k, 0):4d}  {CLASSES[k]:26s} cost: {COST[k]}")
    print(f"\nceiling {summary['ceiling_pct']}% of Set D is reachable at all")
    if problems:
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    return 0


def stats():
    if not SUMMARY.exists():
        print("run without flags first", file=sys.stderr)
        return 1
    s = json.loads(SUMMARY.read_text(encoding="utf-8"))
    print(f"factors {s['factors_total']}  covered {s['covered_l2_plus']}  gap {s['gap_total']}")
    print(f"class I   {s['reachable_by_authoring']:4d}  authoring only")
    print(f"class II  {s['reachable_by_lab']:4d}  needs a lab")
    print(f"class III {s['unavailable']:4d}  unreachable")
    print(f"ceiling   {s['ceiling_pct']}%")
    rows = [json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines() if l.strip()]
    by = {}
    for r in rows:
        by.setdefault(r["lens"], {"I": 0, "II": 0, "III": 0})
        by[r["lens"]][r["class"]] += 1
    print(f"\n{'lens':6s} {'I':>4s} {'II':>4s} {'III':>4s}")
    for lens in sorted(by):
        v = by[lens]
        print(f"{lens:6s} {v['I']:4d} {v['II']:4d} {v['III']:4d}")
    return 0


def validate():
    cov = coverage()
    rows = [json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines() if l.strip()]
    seen = {}
    problems = []
    for r in rows:
        if r["factor"] in seen:
            problems.append(f"{r['factor']}: classified twice")
        seen[r["factor"]] = r
        if r["class"] not in CLASSES:
            problems.append(f"{r['factor']}: bad class {r['class']!r}")
    for f in factors():
        c = cov.get(f["id"])
        covered = bool(c and c["level"] in ("L2", "L3"))
        if covered and f["id"] in seen:
            problems.append(f"{f['id']}: covered but still classified as a gap")
        if not covered and f["id"] not in seen:
            problems.append(f"{f['id']}: uncovered but not classified")
    print(f"gap records {len(rows)}, factors {len(factors())}")
    if problems:
        print(f"\n{len(problems)} problem(s):", file=sys.stderr)
        for p in problems[:30]:
            print(f"  {p}", file=sys.stderr)
        return 1
    print("\nall invariants hold")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()
    if args.stats:
        return stats()
    if args.validate:
        return validate()
    return build()


if __name__ == "__main__":
    sys.exit(main())
