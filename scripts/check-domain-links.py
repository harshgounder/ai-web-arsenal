#!/usr/bin/env python3
"""
check-domain-links.py: check every URL an authored domain asserts, and record what answered.

Why. `data/domain-link-check.json` existed but nothing produced it: it was written by hand during an
earlier session, which makes it a memory rather than a measurement. A file that cannot be rebuilt is
exactly what the standing rule forbids.

Method notes that cost real time to learn:
  - GET, never HEAD. Several real sites answer 404 to HEAD and 200 to GET, which produced seven false
    dead links once.
  - a browser User-Agent, because several sites refuse automated clients outright.
  - follow redirects, and record the final status, not the first.
  - 403, 401 and 429 are BLOCKED, not DEAD. The site exists and refuses us. That is a different fact.

Usage:
  python3 scripts/check-domain-links.py                # check all, rewrite the file
  python3 scripts/check-domain-links.py --only-missing  # only URLs with no record yet
  python3 scripts/check-domain-links.py --workers 4
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "domain-link-check.json"

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/131.0 Safari/537.36")


def collect():
    wanted = {}
    for f in sorted((DATA / "domains").glob("D*.json")):
        if f.stem.endswith(".index"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        for e in d.get("entries", []):
            u = e.get("url")
            if u:
                wanted.setdefault(u, []).append(e.get("id"))
    return wanted


def check(url, timeout=25):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"status": "OK", "http": r.status}
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 429):
            return {"status": "BLOCKED", "http": e.code,
                    "note": "the site refuses automated clients, which is not the same as absent"}
        if e.code in (404, 410):
            return {"status": "DEAD", "http": e.code}
        return {"status": "ERROR", "http": e.code}
    except Exception as e:
        msg = type(e).__name__
        if "timed out" in str(e).lower() or "timeout" in msg.lower():
            return {"status": "TIMEOUT", "http": None}
        return {"status": "ERROR", "http": None, "note": msg[:80]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-missing", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if any link is DEAD, ERROR or TIMEOUT. BLOCKED never fails.")
    args = ap.parse_args()

    wanted = collect()
    prior = {}
    if OUT.exists():
        try:
            prior = json.loads(OUT.read_text(encoding="utf-8")).get("results", {})
        except Exception:
            prior = {}

    targets = sorted(wanted)
    if args.only_missing:
        targets = [u for u in targets if u not in prior]

    print(f"urls asserted {len(wanted)}, to check {len(targets)}")
    results = dict(prior)
    t0 = time.time()
    done = 0

    def work(u):
        nonlocal done
        r = check(u)
        r["entries"] = wanted[u]
        done += 1
        if done % 25 == 0:
            print(f"  {done}/{len(targets)}")
        return u, r

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for u, r in pool.map(work, targets):
            results[u] = r

    # Drop records for URLs no longer asserted, so the file stays a statement about the repo.
    results = {u: r for u, r in results.items() if u in wanted}

    payload = {
        "checked_at": date.today().isoformat(),
        "unique_urls": len(results),
        "method": "GET, browser UA, redirects followed, 3 concurrent retries not attempted",
        "results": dict(sorted(results.items())),
    }
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    from collections import Counter
    st = Counter(r["status"] for r in results.values())
    print(f"\nchecked {len(targets)} in {time.time() - t0:.0f}s -> {dict(st)}")
    bad = [u for u, r in results.items() if r["status"] in ("DEAD", "ERROR", "TIMEOUT")]
    if bad:
        print(f"\n{len(bad)} need a look:")
        for u in bad[:15]:
            print(f"  {results[u]['status']:8} {u}")
    # A report that finds dead links and exits 0 is a report, not a gate. The default stays 0 so the
    # checker can run mid-session without blocking work, but strict mode fails, and says which statuses
    # caused it. BLOCKED is never a failure: the site exists and refuses us, which is a different fact.
    if bad and args.strict:
        print(f"\nstrict: {len(bad)} dead, error or timeout link(s). Failing.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
