#!/usr/bin/env python3
"""
normalize-atoms.py: repair atom fields that were written as strings.

Three separate domains shipped with atoms like "['A15','A08']" because the value was passed
as a string where a list was expected. It renders as garbage and only the validator catches it.
This normalises every domain file idempotently, so the class of bug cannot persist.

Run before validate-domains.py in any build sequence.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
fixed = 0
for f in sorted((ROOT / "data" / "domains").glob("D*.json")):
    if f.stem.endswith(".index"):
        continue
    d = json.load(open(f))
    dirty = False
    top = d.get("atoms")
    if isinstance(top, str):
        d["atoms"] = re.findall(r"A\d{2}", top) or []
        dirty = True
    for e in d.get("entries", []):
        a = e.get("atom")
        if isinstance(a, str):
            ids = re.findall(r"A\d{2}", a)
            e["atom"] = ids or ["A08"]
            dirty = True
        elif isinstance(a, list):
            clean = []
            for x in a:
                if isinstance(x, str) and re.fullmatch(r"A\d{2}", x):
                    clean.append(x)
                elif isinstance(x, str):
                    clean.extend(re.findall(r"A\d{2}", x))
            if clean != a:
                e["atom"] = clean or ["A08"]
                dirty = True
    if dirty:
        json.dump(d, open(f, "w"), indent=1)
        fixed += 1
        print(f"normalised {f.name}")
print(f"{fixed} files changed")
sys.exit(0)
