#!/usr/bin/env python3
"""
validate-denominator.py: check the Set D enumeration in data/denominator/.

Set D is the denominator: every factor that determines whether a web system can be made to do something
its owners did not intend. It is the number the coverage claim is measured against, so it has to be
structurally sound before anything is measured with it.

What it enforces:
  - every lens file parses and declares lens, name, owns, why_in_D
  - factor ids are unique across all lenses and match their lens prefix
  - every factor has a name, a definition, an observable and an evidence class
  - evidence is one of the four kinds this repo accepts
  - no lens is empty
  - a lens that is still unwritten is reported as missing, not as zero

Run: python3 scripts/validate-denominator.py [--stats]
Exit: 0 sound, 1 a violation, 3 nothing to validate yet.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEN = ROOT / "data" / "denominator"

EXPECTED_LENSES = [f"L{i:02d}" for i in range(1, 17)]
EVIDENCE = {"source", "paper", "run", "vendor"}
REQUIRED = ("id", "name", "def", "observable", "evidence")
MIN_PER_LENS = 50


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()

    if not DEN.exists():
        print("no data/denominator directory: Phase 1 has not produced anything yet", file=sys.stderr)
        return 3

    files = {p.stem: p for p in sorted(DEN.glob("L*.json"))}
    if not files:
        print("no lens files found", file=sys.stderr)
        return 3

    problems = []
    seen_ids = {}
    total = 0
    per_lens = {}

    for lens in EXPECTED_LENSES:
        p = files.get(lens)
        if not p:
            problems.append(f"{lens}: not written yet")
            per_lens[lens] = 0
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            problems.append(f"{lens}: does not parse ({e})")
            continue

        for k in ("lens", "name", "owns", "why_in_D", "factors"):
            if not d.get(k):
                problems.append(f"{lens}: missing {k}")
        if d.get("lens") != lens:
            problems.append(f"{lens}: declares lens {d.get('lens')!r}")

        factors = d.get("factors") or []
        per_lens[lens] = len(factors)
        total += len(factors)
        if not factors:
            problems.append(f"{lens}: has no factors")
        elif len(factors) < MIN_PER_LENS:
            problems.append(f"{lens}: {len(factors)} factors, target is at least {MIN_PER_LENS}")

        for f in factors:
            fid = f.get("id", "?")
            for r in REQUIRED:
                if not f.get(r):
                    problems.append(f"{lens}: {fid} missing {r}")
            if not str(fid).startswith(lens + "-"):
                problems.append(f"{lens}: {fid} does not match the lens prefix")
            if fid in seen_ids:
                problems.append(f"{lens}: duplicate id {fid} (also in {seen_ids[fid]})")
            seen_ids[fid] = lens
            if f.get("evidence") and f["evidence"] not in EVIDENCE:
                problems.append(f"{lens}: {fid} evidence {f['evidence']!r} not one of {sorted(EVIDENCE)}")

    written = sum(1 for v in per_lens.values() if v)
    print(f"lenses written {written} of 16, factors {total}")
    for lens, n in per_lens.items():
        mark = "  " if n >= MIN_PER_LENS else ("--" if n else "  ")
        print(f"  {mark} {lens} {n:4d}")

    if args.stats:
        print(f"\ntotal {total}")
        print(f"written {written}")
        print(f"remaining {16 - written}")

    if problems:
        print(f"\n{len(problems)} problem(s):", file=sys.stderr)
        for p in problems[:60]:
            print(f"  {p}", file=sys.stderr)
        if len(problems) > 60:
            print(f"  ... and {len(problems) - 60} more", file=sys.stderr)
        return 1

    print("\nall invariants hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
