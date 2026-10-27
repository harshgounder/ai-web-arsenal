#!/usr/bin/env python3
"""
harvest-osv.py: pull advisories for a selected set of web significant packages.

Why scoping matters. A breadth engine that pulls everything and then filters by keyword produces a
corpus whose size is mostly the filter's false positive rate. This harvests from a package list instead,
so relevance is a selection made before the query rather than a guess made after it. The tradeoff is
stated plainly: this is a sample of packages, not a census of advisories.

Input:  data/advisories/packages.txt, one `ecosystem<TAB>package` per line
Output: data/advisories/raw/<ecosystem>.jsonl, one advisory per line, deduplicated by id

Usage:
  python3 scripts/harvest-osv.py
  python3 scripts/harvest-osv.py --limit 200
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKGS = ROOT / "data" / "advisories" / "packages.txt"
RAW = ROOT / "data" / "advisories" / "raw"
API = "https://api.osv.dev/v1/query"


def query(ecosystem, package, timeout=25):
    body = json.dumps({"package": {"name": package, "ecosystem": ecosystem}}).encode()
    req = urllib.request.Request(API, data=body,
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": "ai-web-arsenal harvest"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read())
            return d.get("vulns") or []
    except urllib.error.HTTPError as e:
        print(f"  {ecosystem}:{package} HTTP {e.code}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"  {ecosystem}:{package} {type(e).__name__}", file=sys.stderr)
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="stop after this many unique advisories")
    args = ap.parse_args()

    if not PKGS.exists():
        print(f"no package list at {PKGS}", file=sys.stderr)
        return 1

    pairs = []
    for line in PKGS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            print(f"bad line: {line!r}", file=sys.stderr)
            continue
        pairs.append((parts[0].strip(), parts[1].strip()))

    print(f"{len(pairs)} package(s) to query")
    RAW.mkdir(parents=True, exist_ok=True)
    by_eco = {}
    seen = set()
    fetched = 0

    for eco, pkg in pairs:
        vulns = query(eco, pkg)
        fetched += 1
        for v in vulns:
            vid = v.get("id")
            if not vid or vid in seen:
                continue
            seen.add(vid)
            v["_queried_as"] = f"{eco}:{pkg}"
            by_eco.setdefault(eco, []).append(v)
        if fetched % 10 == 0:
            print(f"  {fetched}/{len(pairs)} packages, {len(seen)} unique advisories")
        if args.limit and len(seen) >= args.limit:
            break
        time.sleep(0.1)

    total = 0
    for eco, rows in by_eco.items():
        path = RAW / f"{eco.replace('/', '_')}.jsonl"
        with open(path, "w", encoding="utf-8") as fh:
            for v in rows:
                fh.write(json.dumps(v, ensure_ascii=False) + "\n")
        total += len(rows)
        print(f"  {eco}: {len(rows)}")

    print(f"\nunique advisories {total} from {fetched} package queries")
    if total == 0:
        print("nothing harvested: the network may be blocked, which is a different fact from no advisories",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
