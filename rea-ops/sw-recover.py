#!/usr/bin/env python3
"""
sw-recover.py: reconstruct what a service worker can serve offline, from a capture.

Why this matters. A service worker sits between the page and the network, so it can answer a request with a
response the server would refuse today: an authenticated page cached before logout, an API response cached
under a different user, a redirect that no longer exists. None of that is visible in a HAR taken without
looking for it, because the HAR records what came over the wire, and the interesting case is what did not.

What this does: reads a captured CDP session or a HAR, and reports the worker registrations, the cache
names, and the entries in each, then answers one question per entry: **could this response be served to
someone who should not have it**. That question is decided by whether the entry carries a credential, a
personal identifier, or a cache header that permits sharing.

What it does not do: talk to a browser. There is no CDP transport here, so you must supply a capture.
That is a real gap and it is stated rather than implied, because a tool that quietly needs Chrome and does
not say so is worse than one that takes a file.

Input shapes accepted:
  a CDP capture: {"registrations": [...], "caches": [{"name": ..., "entries": [...]}]}
  a HAR:         {"log": {"entries": [...]}}   where initiator or request indicates service worker

Usage:
  python3 rea-ops/sw-recover.py capture.json
  python3 rea-ops/sw-recover.py capture.json --json

Output: a manifest plus a risk list. Exit 0 when it parsed, 2 when it found nothing service worker shaped.
"""
import argparse
import json
import re
import sys
from pathlib import Path

CREDENTIAL_HEADERS = ("authorization", "cookie", "x-api-key", "x-auth-token", "proxy-authorization")

# A cache header that permits sharing is the difference between a private bug and a shared one.
SHAREABLE = ("public", "s-maxage")

# Values that look like they belong to one person. Deliberately crude: this is a triage hint for a human to
# confirm, not a classifier, and every hit is reported with the value that produced it.
PERSONAL = ("user", "account", "tenant", "customer", "member", "email", "session", "owner", "sub")


def from_cdp(doc):
    regs, caches = [], []
    for r in doc.get("registrations") or []:
        regs.append({"scope": r.get("scopeURL") or r.get("scope"),
                     "script": r.get("scriptURL") or r.get("script"),
                     "version": r.get("versionId") or r.get("version")})
    for c in doc.get("caches") or []:
        entries = []
        for e in c.get("entries") or []:
            entries.append({"url": e.get("url") or e.get("urls"),
                            "status": e.get("status"),
                            "size": e.get("size") or e.get("contentLength"),
                            "headers": {k.lower(): v for k, v in (e.get("headers") or {}).items()},
                            "body_len": len(e.get("body") or "")})
        caches.append({"name": c.get("name"), "entries": entries})
    return regs, caches


def from_har(doc):
    regs, caches = [], {}
    for e in ((doc.get("log") or {}).get("entries") or []):
        req, res = e.get("request") or {}, e.get("response") or {}
        url = req.get("url") or ""
        sw = (e.get("_resourceType") == "serviceworker") or bool(e.get("_serviceWorker"))
        hdrs = {h.get("name", "").lower(): h.get("value", "") for h in (res.get("headers") or [])}
        if sw and url.endswith("sw.js") or "service-worker" in url:
            regs.append({"scope": url.rsplit("/", 1)[0] + "/", "script": url, "version": None})
        if not sw:
            continue
        key = res.get("_fromCache") and "from-cache" or "service-worker"
        caches.setdefault(key, []).append({
            "url": url, "status": res.get("status"),
            "size": (res.get("content") or {}).get("size"),
            "headers": hdrs, "body_len": (res.get("content") or {}).get("size") or 0,
        })
    return regs, [{"name": k, "entries": v} for k, v in sorted(caches.items())]


def assess(entry):
    """Why this cached entry could be served to the wrong person.

    The first version of this flagged any entry with a shareable cache-control, which made a public logo
    the same severity as somebody's account page. Sharing a static asset is the correct behaviour. The
    question is only interesting when the entry is bound to a principal and shared anyway, so this computes
    the binding first and treats sharing as the amplifier rather than the fault.
    """
    h = entry.get("headers") or {}
    url = (entry.get("url") or "").lower()
    ctype = (h.get("content-type") or "").lower()
    cc = (h.get("cache-control") or "").lower()

    bound_by = []
    for name in CREDENTIAL_HEADERS:
        if name in h:
            bound_by.append(f"carries a {name} header")
            break
    hits = [p for p in PERSONAL if p in url]
    if hits:
        bound_by.append(f"url names a person or an account ({', '.join(hits)})")
    if "json" in ctype and ("/api/" in url or "/me" in url or "/graphql" in url):
        bound_by.append("an api response, which is usually computed for one caller")

    is_static = any(x in ctype for x in ("image/", "font/", "text/css", "javascript")) or \
        re.search(r"\.(svg|png|jpg|jpeg|gif|woff2?|ttf|css|js|ico)(\?|$)", url)
    if is_static and not any("carries a" in b for b in bound_by):
        return []

    reasons = []
    if bound_by and any(x in cc for x in SHAREABLE):
        reasons.append(f"bound to a principal ({'; '.join(bound_by)}) and cache-control permits sharing")
    elif bound_by and not cc:
        reasons.append(f"bound to a principal ({'; '.join(bound_by)}) with no cache-control at all")
    elif bound_by and "private" not in cc and "no-store" not in cc:
        reasons.append(f"bound to a principal ({'; '.join(bound_by)}) without private or no-store")
    if not reasons and "html" in ctype and any(x in cc for x in SHAREABLE):
        # weaker, and labelled as such: a public cached page is not a finding unless the page varies by
        # person, which a capture cannot tell you
        reasons.append("an html page cached as public, which is only a finding if the page varies by user")
    return reasons


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"no such file: {p}", file=sys.stderr)
        return 1
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"cannot parse: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    if "log" in doc:
        regs, caches = from_har(doc)
        shape = "har"
    elif "registrations" in doc or "caches" in doc:
        regs, caches = from_cdp(doc)
        shape = "cdp"
    else:
        print("not a CDP capture and not a HAR: expected a 'log' or a 'registrations'/'caches' key",
              file=sys.stderr)
        return 2

    total = sum(len(c["entries"]) for c in caches)
    if not regs and not total:
        print("parsed, but found no service worker registrations and no cached entries. That is a fact "
              "about the capture, not proof the target has none.", file=sys.stderr)
        return 2

    risk = []
    for c in caches:
        for e in c["entries"]:
            r = assess(e)
            if r:
                risk.append({"cache": c["name"], "url": e["url"], "reasons": r})

    out = {
        "file": p.name,
        "shape": shape,
        "registrations": regs,
        "caches": [{"name": c["name"], "entries": len(c["entries"])} for c in caches],
        "cached_entries": total,
        "at_risk": len(risk),
        "risk": risk[:40],
        "transport_note": ("no CDP transport in this tool. It reads a capture you supply. Live collection "
                          "needs a browser and is not implemented here, which is stated rather than hidden"),
    }

    if args.json:
        print(json.dumps(out, indent=1))
        return 0

    print(f"[{shape}] {p.name}")
    print(f"  registrations {len(regs)}   caches {len(caches)}   cached entries {total}")
    for r in regs:
        print(f"    scope {r.get('scope')}  script {r.get('script')}")
    for c in out["caches"]:
        print(f"    cache {c['name']}: {c['entries']} entries")
    if risk:
        print(f"\n  {len(risk)} entr(y/ies) could be served to the wrong person:")
        for r in out["risk"][:12]:
            print(f"    {str(r['url'])[:70]}")
            for why in r["reasons"]:
                print(f"      - {why}")
    else:
        print("\n  no entry looked shareable on these tests. Absence here is weak: the headers may be")
        print("  stripped in the capture, so confirm against a live cache before concluding anything.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
