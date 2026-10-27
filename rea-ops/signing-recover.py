#!/usr/bin/env python3
"""
signing-recover.py: find where a JavaScript bundle constructs a request signature.

The problem. An API that signs its requests puts the secret in the client, and the client is obfuscated.
The question an analyst actually has is narrow: which function builds the value that goes into the header,
and what does it feed on. Recovering a whole algorithm by hand is slow, and claiming to have recovered one
is worse than not trying, because a wrong claim sends the next person down a false path.

So this returns **ranked candidates with their evidence**, never a recovered algorithm. Every candidate is
a region of the bundle with the patterns that matched, the surrounding source, and the signals that pushed
it up or down. A human confirms or discards each one.

Ranking signals, in the order they matter:

  strong   a digest call whose output is assigned to a header or a request field
  strong   an hmac construction (createHmac, HmacSHA256, subtle.sign) fed by something named like a key
  weak     a bare digest, which is usually a cache key or a checksum
  weak     string concatenation near a digest, which is the usual way the message is built
  decoy    a digest consumed by a cache or an etag, which is the mistake this tool has to avoid

Confidence is not a probability. It is a count of independent signal groups, and the report says so.

Usage:
  python3 rea-ops/signing-recover.py bundle.js
  python3 rea-ops/signing-recover.py bundle.js --json --top 5
"""
import argparse
import json
import re
import sys
from pathlib import Path

# (name, pattern, group, weight). Groups matter more than counts: three weak signals of the same kind are
# one piece of evidence, not three.
SIGNALS = [
    ("hmac construction", re.compile(r"\b(?:createHmac|HmacSHA(?:1|256|384|512)|hmac|HMAC)\b"), "hmac", 3),
    ("webcrypto sign", re.compile(r"subtle\s*\.\s*sign|subtle\s*\.\s*importKey"), "hmac", 3),
    ("digest call", re.compile(r"\b(?:createHash|sha256|sha1|md5|SHA256)\b"), "digest", 1),
    ("digest encoding", re.compile(r"\.digest\s*\(\s*['\"](?:hex|base64)['\"]|toString\s*\(\s*['\"]hex['\"]"), "digest", 1),
    ("key material name", re.compile(r"\b(?:secret|secretKey|appSecret|privateKey|signingKey|apiSecret|salt)\b"), "key", 2),
    ("header assignment", re.compile(r"['\"](?:X-[\w-]*Sig[\w-]*|X-Signature|X-Sign|Authorization|signature|sign)['\"]\s*[:=]"), "sink", 3),
    ("request field", re.compile(r"\b(?:sign|signature|sig|token)\s*[:=]\s*[a-zA-Z_$]"), "sink", 2),
    ("message assembly", re.compile(r"(?:\+\s*['\"][:&|]['\"]|\.join\(\s*['\"][:&|]['\"]|sort\(\)\s*\.\s*join)"), "assembly", 1),
    ("timestamp input", re.compile(r"\b(?:Date\.now|getTime|timestamp|nonce|ts)\b"), "assembly", 1),
]

# A digest that only ever reaches a cache or an etag is not a signature. Matching this inside the window
# costs the candidate more than any single weak signal earns it.
DECOYS = [
    ("cache or etag consumer", re.compile(r"\b(?:etag|ETag|cacheKey|cache-key|fromCache|localStorage)\b"), 3),
    ("checksum label", re.compile(r"\b(?:checksum|crc|integrity|dedupe|contentHash)\b"), 2),
]

WINDOW = 320


def scan(text):
    hits = []
    for name, rx, group, weight in SIGNALS:
        for m in rx.finditer(text):
            hits.append({"signal": name, "group": group, "weight": weight, "at": m.start()})
    for name, rx, penalty in DECOYS:
        for m in rx.finditer(text):
            hits.append({"signal": name, "group": "decoy", "weight": -penalty, "at": m.start()})
    hits.sort(key=lambda h: h["at"])
    return hits


def cluster(hits, gap=90):
    """Anchor on the crypto calls, not on every hit.

    The first version grouped any hits within one window of each other, which on a small bundle merged the
    whole file into one region: a decoy etag at the top then sank a real signer 200 bytes below it. A
    candidate is a crypto call and whatever surrounds it, so the anchors are the crypto calls and the
    proximity rule only merges anchors that are effectively the same site.
    """
    anchors = [h for h in hits if h["group"] in ("hmac", "digest")]
    out, cur = [], []
    for h in anchors:
        if cur and h["at"] - cur[-1]["at"] > gap:
            out.append(cur)
            cur = []
        cur.append(h)
    if cur:
        out.append(cur)
    return out


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def score(cluster_hits):
    groups = {}
    for h in cluster_hits:
        groups.setdefault(h["group"], []).append(h)
    # one credit per group, so three digest signals do not outrank one hmac
    total = sum(max(h["weight"] for h in hs) if k != "decoy" else min(h["weight"] for h in hs)
                for k, hs in groups.items())
    has_sink = "sink" in groups
    has_crypto = "hmac" in groups or "digest" in groups
    return total, has_sink, has_crypto, sorted(groups)


def assess(text, anchor_hits, idx, all_hits, before=80, after=320, decoy_proximity=70):
    start = max(0, min(h["at"] for h in anchor_hits) - before)
    end = min(len(text), max(h["at"] for h in anchor_hits) + after)
    # a candidate is an anchor plus every signal that falls in its own neighbourhood, so a decoy costs
    # only the candidate it actually sits inside
    cluster_hits = [h for h in all_hits
                    if (start <= h["at"] <= end)
                    # a decoy counts only when it consumes this anchor, meaning it sits within a few dozen
                    # characters of the crypto call. An etag 40 characters upstream is a different function,
                    # and letting it vote was how the first version sank a real signer.
                    and (h["group"] != "decoy"
                         or min(abs(h["at"] - a["at"]) for a in anchor_hits) <= decoy_proximity)]
    total, has_sink, has_crypto, groups = score(cluster_hits)
    if not has_crypto:
        return None
    snippet = re.sub(r"\s+", " ", text[start:end]).strip()

    if "decoy" in groups:
        verdict = "likely not a signature: a cache or integrity consumer is in the same region"
    elif has_sink and "hmac" in groups:
        verdict = "strong: an hmac whose result reaches a header or a request field"
    elif has_sink:
        verdict = "strong: a digest whose result reaches a header or a request field"
    elif "key" in groups:
        verdict = "possible: key material near a digest but no sink seen in this window"
    else:
        verdict = "weak: a digest with no sink and no key nearby, which is usually a checksum"

    return {
        "candidate": idx,
        "line": line_of(text, cluster_hits[0]["at"]),
        "score": total,
        "verdict": verdict,
        "groups": groups,
        "signals": sorted({h["signal"] for h in cluster_hits}),
        "evidence": snippet[:300],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--top", type=int, default=8)
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"no such file: {p}", file=sys.stderr)
        return 1
    text = p.read_text(encoding="utf-8", errors="replace")
    if len(text) < 200:
        print(f"{p.name} is {len(text)} bytes, which is too small to be a bundle. Refusing rather than "
              f"reporting nothing, because nothing and too small are different answers.", file=sys.stderr)
        return 2

    hits = scan(text)
    cands = []
    for i, cl in enumerate(cluster(hits)):
        a = assess(text, cl, i, hits)
        if a:
            cands.append(a)
    cands.sort(key=lambda c: (-c["score"], c["line"]))

    out = {
        "file": p.name,
        "bytes": len(text),
        "candidates": cands[: args.top],
        "total_candidates": len(cands),
        "method": ("ranked candidates, not a recovered algorithm. Score counts independent signal groups, "
                   "so it is ordering rather than probability. Confirm each candidate by reading its "
                   "evidence before using it"),
    }

    if args.json:
        print(json.dumps(out, indent=1))
        return 0

    print(f"{p.name}  {len(text)} bytes  {len(cands)} candidate region(s)")
    if not cands:
        print("  no digest or hmac construction found. That is a fact about this bundle, not proof the")
        print("  signing happens elsewhere: it may be in a lazily loaded chunk you did not supply.")
        return 0
    for c in out["candidates"]:
        print(f"\n  line {c['line']:<6} score {c['score']:<3} {c['verdict']}")
        print(f"    signals: {', '.join(c['signals'])}")
        print(f"    evidence: {c['evidence'][:170]}")
    print("\n  Ranked candidates, not a recovered algorithm. Read the evidence before using one.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
