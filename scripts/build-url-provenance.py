#!/usr/bin/env python3
"""
build-url-provenance.py: one record per URL this repo asserts, with when it was checked and what
answered.

Why. Two repository URLs were invented earlier in this project and were indistinguishable from the 110
real ones, because nothing recorded where a URL came from or when anyone last asked it whether it
exists. A bulk link check answers "how many are live"; this answers "was this specific URL ever
verified, and when". A URL with no record is a hypothesis wearing a link's clothes.

Input:  data/domains/D*.json (every entry URL), data/domain-link-check.json (bulk results)
Output: data/url-provenance.jsonl, data/url-provenance.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def main():
    check = json.loads((DATA / "domain-link-check.json").read_text(encoding="utf-8"))
    results = check.get("results", {})
    checked_at = check.get("checked_at")

    # Every URL an authored entry asserts, plus which entry asserts it.
    wanted = {}
    for f in sorted((DATA / "domains").glob("D*.json")):
        if f.stem.endswith(".index"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        for e in d.get("entries", []):
            u = e.get("url")
            if u:
                wanted.setdefault(u, []).append(e.get("id"))

    rows = []
    unchecked = []
    for u in sorted(wanted):
        r = results.get(u)
        if not r:
            unchecked.append(u)
            rows.append({"url": u, "checked_at": None, "status": "UNCHECKED",
                         "http": None, "entries": wanted[u]})
            continue
        rows.append({"url": u, "checked_at": checked_at, "status": r.get("status"),
                     "http": r.get("http"), "entries": wanted[u]})

    with open(DATA / "url-provenance.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    from collections import Counter
    st = Counter(r["status"] for r in rows)
    stats = {
        "generated_at": checked_at,
        "urls_asserted": len(rows),
        "by_status": dict(st),
        "unchecked": len(unchecked),
        "note": "a URL with no record is unverified, and unverified is not the same as broken",
    }
    (DATA / "url-provenance.json").write_text(json.dumps(stats, indent=1) + "\n", encoding="utf-8")

    print(f"urls asserted {len(rows)} -> {dict(st)}")
    if unchecked:
        print(f"\n{len(unchecked)} URL(s) have no check record. Run the link check, do not assume:")
        for u in unchecked[:10]:
            print(f"  {u}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
