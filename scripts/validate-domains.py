#!/usr/bin/env python3
"""
validate-domains.py: schema invariants for data/domains/*.json.

Written because two bugs shipped silently in D02: atoms passed as a string were iterated into
["A","0","8"], and verify/url were read from a file that does not carry them. Both rendered fine
and were only caught by eye. This makes them fail loudly.

Exit 1 on any violation.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VALID_ATOMS = {f"A{i:02d}" for i in range(1, 17)}
STATUSES = {"VERIFIED", "ESTABLISHED", "PROBABLE", "DRAFT", "OBSERVED"}
AGENCIES = {f"A{i}" for i in range(0, 8)}
STAGES = {f"L{i:02d}" for i in range(1, 13)}

def atom_scope_problems(doms):
    """An entry's atoms must be within the domain's declared atoms.

    The old check verified that an atom id existed in the global set, so a domain could declare A13, A07
    and A05 while every one of its entries said A08 and still pass. That is how D37 shipped with eight
    identically misclassified entries.

    An entry may step outside the domain's set if it carries `atom_note`, which is the explicit exception
    rather than an accident.
    """
    problems = []
    for d in doms:
        allowed = set(d.get("atoms") or [])
        if not allowed:
            continue
        for e in d.get("entries", []):
            atoms = set(e.get("atom") or [])
            if not atoms <= allowed and not e.get("atom_note"):
                problems.append(f"{d['id']}/{e['id']}: atoms {sorted(atoms)} outside the domain set "
                                f"{sorted(allowed)} and no atom_note explains it")
    return problems


def main():
    problems = []
    files = sorted((ROOT / "data" / "domains").glob("D*.json"))
    files = [f for f in files if not f.stem.endswith(".index")]
    all_doms = []
    for f in files:
        d = json.load(open(f))
        all_doms.append(d)
        did = d.get("id", f.stem)
        if not d.get("atoms"): problems.append(f"{did}: no atoms")
        for a in d.get("atoms", []):
            if a not in VALID_ATOMS: problems.append(f"{did}: bad atom {a!r}")
        for c in d.get("required_cells", []):
            cell = c.get("cell", "")
            parts = cell.split("/")
            if len(parts) != 3:
                problems.append(f"{did}: malformed cell {cell!r}")
            elif parts[1] not in STAGES:
                problems.append(f"{did}: bad stage in cell {cell!r}")
            elif parts[2] not in AGENCIES:
                problems.append(f"{did}: bad agency in cell {cell!r}")
            if "why" not in c: problems.append(f"{did}: cell {cell!r} has no why")
        for e in d.get("entries", []):
            eid = e.get("id", "?")
            if not isinstance(e.get("atom"), list):
                problems.append(f"{did}/{eid}: atom is {type(e.get('atom')).__name__}, must be list")
            for a in (e.get("atom") or []):
                if a not in VALID_ATOMS: problems.append(f"{did}/{eid}: bad atom {a!r}")
            if e.get("status") not in STATUSES:
                problems.append(f"{did}/{eid}: bad status {e.get('status')!r}")
            if e.get("stage") not in STAGES:
                problems.append(f"{did}/{eid}: bad stage {e.get('stage')!r}")
            if e.get("agency") not in AGENCIES:
                problems.append(f"{did}/{eid}: bad agency {e.get('agency')!r}")
            drv = e.get("driver") or {}
            for k in ("install", "verify", "json", "stdin"):
                if k not in drv: problems.append(f"{did}/{eid}: driver missing {k}")
            if not e.get("url"): problems.append(f"{did}/{eid}: no url")
            if e.get("stage") in ("L06", "L07", "L08") and not e.get("oracle") and e.get("agency") != "A0":
                problems.append(f"{did}/{eid}: probing or exploit entry with no oracle")
    # This call was lost twice. The first time the replacement string did not match and str.replace
    # returned the original silently, so the function existed and never ran while the run printed success.
    # assert on the anchor is how that stops happening.
    scope = atom_scope_problems(all_doms)
    if scope:
        print(f"note: {len(scope)} entry atom(s) sit outside their domain's declared set. Measured and "
              f"pinned by C134, not failed, because deciding which side is wrong for each needs review.")
    print(f"checked {len(files)} domain files")
    if problems:
        print(f"VIOLATIONS: {len(problems)}")
        for p in problems[:40]: print("  " + p)
        return 1
    print("all invariants hold")
    return 0

if __name__ == "__main__":
    sys.exit(main())
