#!/usr/bin/env python3
"""
stamp-and-check.py: give every corpus entry a dated evidence state, and actually check the links.

Evidence ladder, per entry:

  HARVESTED      seen in a source collection, never independently checked
  LINK_OK        URL answered 2xx/3xx on last_verified
  LINK_BLOCKED   URL answered 401/403/429 (exists, refuses automated clients)
  LINK_DEAD      404/410 or DNS failure
  LINK_ERROR     timeout or transport error, status unknown
  NO_URL         entry has no URL (taxonomy node, name only)

The point is that "refreshed through October 2026" is a claim about checks that ran, with a date on each
one, not a line in a README. Entries never checked stay HARVESTED and say so.

Usage:
  python3 scripts/stamp-and-check.py                 # stamp only, no network
  python3 scripts/stamp-and-check.py --check core_web --limit 600
  python3 scripts/stamp-and-check.py --check all --limit 2500 --workers 8
"""
import json, sys, time, socket, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TODAY = date.today().isoformat()
UA = "Mozilla/5.0 (X11; Linux x86_64) ai-web-arsenal links/1.0"


BROWSER_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def check(url, timeout=20):
    """GET only, browser UA, read one byte, follow redirects.

    CORRECTION 2026-10-26: an earlier version sent HEAD first. Several real sites answer HEAD with 404
    while GET returns 200 (portswigger.net is a live example), which produced false dead links. A dead
    link claim is expensive, so this now does what a browser does and nothing cleverer.
    """
    if not url or not url.startswith("http"):
        return "NO_URL", None, None
    req = urllib.request.Request(url, headers={
        "User-Agent": BROWSER_UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            r.read(1)
            return ("LINK_OK", r.status, None)
    except urllib.error.HTTPError as e:
        code = e.code
        if code in (401, 403, 407, 429):
            return "LINK_BLOCKED", code, None
        if code in (404, 410):
            return "LINK_DEAD", code, None
        return "LINK_ERROR", code, f"http {code}"
    except socket.timeout:
        return "LINK_ERROR", None, "timeout"
    except Exception as e:
        return "LINK_ERROR", None, type(e).__name__


def main():
    args = sys.argv[1:]
    do_check = "--check" in args
    tier = "core_web"
    if "--check" in args:
        i = args.index("--check")
        if i + 1 < len(args):
            tier = args[i + 1]
    limit = 600
    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])
    workers = 8
    if "--workers" in args:
        workers = int(args[args.index("--workers") + 1])

    rows = [json.loads(l) for l in (DATA / "corpus.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"entries: {len(rows)}")

    for e in rows:
        e.setdefault("first_seen", None)
        e.setdefault("last_verified", None)
        e.setdefault("evidence_status", "HARVESTED")
        if not e.get("url"):
            e["evidence_status"] = "NO_URL"
        if e["first_seen"] is None:
            e["first_seen"] = TODAY

    targets = []
    if "--recheck-failures" in args:
        pool = [e for e in rows if e.get("url") and e.get("evidence_status") in
                ("LINK_DEAD", "LINK_ERROR", "LINK_BLOCKED")]
        targets = pool
        do_check = True
        print(f"rechecking {len(targets)} previously failed links with GET and a browser UA")
    elif do_check:
        pool = [e for e in rows if e.get("url") and (tier == "all" or e["tier"] == tier)]
        pool.sort(key=lambda e: (-(e.get("n_sources") or 0), -(e.get("web_score") or 0)))
        targets = pool[:limit]
        print(f"checking {len(targets)} urls (tier={tier}, limit={limit}, workers={workers})")

    results = {}
    if targets:
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(check, e["url"]): e for e in targets}
            for n, f in enumerate(as_completed(futs), 1):
                e = futs[f]
                status, code, err = f.result()
                results[e["key"]] = {"status": status, "http": code, "error": err}
                e["evidence_status"] = status
                e["last_verified"] = TODAY
                e["link_http"] = code
                if err:
                    e["link_error"] = err
                if n % 50 == 0:
                    print(f"  {n}/{len(targets)}  {time.time()-t0:.0f}s")

    (DATA / "corpus.jsonl").write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in rows) + "\n", encoding="utf-8")

    from collections import Counter
    c = Counter(e["evidence_status"] for e in rows)
    summary = {"generated_at": TODAY, "entries": len(rows),
               "evidence_status": dict(c.most_common()),
               "checked_this_run": len(targets),
               "link_results_this_run": dict(Counter(v["status"] for v in results.values()))}
    json.dump(summary, open(DATA / "evidence-summary.json", "w"), indent=1)
    print("\nevidence status across the corpus:")
    for k, v in c.most_common():
        print(f"  {k:14s} {v}")
    if results:
        print("\nthis run:")
        for k, v in Counter(x["status"] for x in results.values()).most_common():
            print(f"  {k:14s} {v}")


if __name__ == "__main__":
    main()
