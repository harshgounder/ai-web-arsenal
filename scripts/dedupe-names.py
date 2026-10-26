#!/usr/bin/env python3
"""
dedupe-names.py: flag index candidates whose tool NAME already exists in the domain.

URL canonicalisation cannot catch a rename (OWASP/Amass vs owasp-amass/amass) or a name variant
(John the Ripper vs john). That is why the n_sources==2 promotion tier was 40% duplicates.

Normalises names by lowercasing and stripping everything but alphanumerics, then compares against
every entry already enriched in the same domain. Reports, does not delete.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def main():
    total = dup = 0
    per = {}
    for f in sorted((ROOT / "data" / "domains").glob("*.index.json")):
        did = json.load(open(f))["domain"]
        dom = json.load(open(ROOT / "data" / "domains" / f"{did}.json"))
        have = {norm(e.get("name")) for e in dom["entries"]}
        have |= {norm(e.get("id", "").replace(f"{did.lower()}-", "")) for e in dom["entries"]}
        idx = json.load(open(f))
        keep, marked = [], 0
        for e in idx["entries"]:
            total += 1
            n = norm(e.get("name"))
            if n and (n in have or n.rstrip("0123456789") in have):
                marked += 1
                dup += 1
                continue
            keep.append(e)
        idx["indexed_not_enriched"] = len(keep)
        idx["entries"] = keep
        idx["duplicate_names_removed"] = marked
        json.dump(idx, open(f, "w"), indent=1)
        per[did] = marked
    print(f"candidates {total}, removed as name duplicates of an existing entry: {dup}")
    top = sorted(per.items(), key=lambda kv: -kv[1])[:8]
    for k, v in top:
        if v:
            print(f"  {k} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
