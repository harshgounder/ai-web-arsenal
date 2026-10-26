#!/usr/bin/env python3
"""
link-mirrors.py: give every entry a mirror reference, or record that none covers it.

The domain docs all promise "every offensive entry has a detection". At domain level that was true.
At entry level, 354 of 389 entries had an empty detected_by, so the promise was only half kept.

This links each entry to the specific mirror row in its own domain by keyword overlap between the
entry's role and the mirror row's attack description. It marks the link PROVISIONAL because matching
is lexical, not semantic. Where nothing matches, it says so rather than inventing a detection.

Output per entry:
  detected_by        the mirror row's detect text, if matched
  mirror_ref         index of the mirror row in the domain, if matched
  mirror_note        "no mirror row covers this entry" when unmatched

Run after any domain edit. Idempotent.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STOP = set("the a an of to in on for with and or is are be by as at from that this it its".split())


def toks(s):
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if w not in STOP and len(w) > 2}


def main():
    total = matched = unmatched = 0
    per = {}
    for f in sorted((ROOT / "data" / "domains").glob("D*.json")):
        if f.stem.endswith(".index"):
            continue
        d = json.load(open(f))
        mirror = d.get("mirror") or []
        if not mirror:
            continue
        mcount = um = 0
        for e in d.get("entries", []):
            total += 1
            if e.get("mirror_ref") is not None and e.get("detected_by"):
                matched += 1
                continue
            et = toks(e.get("role", "") + " " + " ".join(e.get("atom", [])))
            best, bestscore = None, 0.0
            for i, row in enumerate(mirror):
                rt = toks(row.get("attack", "") + " " + row.get("detect", ""))
                if not rt or not et:
                    continue
                score = len(et & rt) / len(et | rt)
                if score > bestscore:
                    best, bestscore = i, score
            if best is not None and bestscore >= 0.12:
                e["detected_by"] = [mirror[best].get("detect", "")]
                e["mirror_ref"] = best
                e["mirror_provisional"] = True
                mcount += 1
                matched += 1
            else:
                e["mirror_note"] = "no mirror row covers this entry"
                um += 1
                unmatched += 1
        per[d["id"]] = (mcount, um)
        json.dump(d, open(f, "w"), indent=1)
    print(f"{total} entries: {matched} linked to a mirror row, {unmatched} with no coverage recorded")
    print(f"\n{'dom':5s} {'linked':>7s} {'none':>6s}")
    for k, (a, b) in sorted(per.items()):
        print(f"{k:5s} {a:7d} {b:6d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
