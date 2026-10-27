#!/usr/bin/env python3
"""
mine-capability.py: find tools by what they do, not by the name someone gave them.

Why this exists. The 8,848 row corpus was harvested from nineteen curated lists, and a curated list only
contains what its author remembered. Search by capability inverts that: ask the registry what exists for a
job, then check whether the lists already had it. The interesting number is not how many tools are found,
it is how many of them the lists **missed**.

Method, stated so it can be argued with:

  - a fixed table of capability queries, each a phrase a person would search for a job
  - results are filtered to repositories pushed inside a recency window, because an abandoned scanner is a
    citation rather than a tool
  - each candidate is checked against the corpus by repository slug, and `in_corpus` is recorded either way
  - nothing here is admitted to the corpus. This produces candidates, and admission remains a decision

Input:  the query table below
Output: data/capability/candidates.jsonl, data/capability/SUMMARY.json

Usage:
  python3 scripts/mine-capability.py
  python3 scripts/mine-capability.py --limit 30 --months 18
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "capability" / "candidates.jsonl"
SUMMARY = ROOT / "data" / "capability" / "SUMMARY.json"
CORPUS = ROOT / "data" / "corpus.tools.jsonl"

# capability -> GitHub topic qualifiers. Topics are curated by humans and are far more precise than free
# text, which matters because the first version of this used `in:readme` and returned `public-apis`,
# `yt-dlp` and `ollama` as top web security candidates. That number was meaningless and was caught by
# reading the rows rather than by any check.
QUERIES = {
    "web scanner": "topic:vulnerability-scanner",
    "fuzzer": "topic:fuzzing+language:python",
    "proxy and interception": "topic:proxy+security",
    "api security": "topic:api-security",
    "graphql security": "topic:graphql-security",
    "authentication testing": "topic:jwt+security",
    "client side": "topic:xss",
    "javascript analysis": "topic:deobfuscation",
    "artifact extraction": "topic:reverse-engineering",
    "mobile web analysis": "topic:mobile-security",
    "agent tooling": "topic:mcp-server+security",
    "waf evasion": "topic:waf",
    "secret scanning": "topic:secret-scanning",
    "bug bounty": "topic:bugbounty",
}

# A repository whose name is a list is a list. Nineteen of those are already reconciled, and a twentieth
# arriving as a "tool candidate" is exactly the row-is-not-a-tool mistake this repo has fixed once.
LIST_NAMES = ("awesome", "roadmap", "public-apis", "book-of", "cheatsheet", "cheat-sheet",
              "curated", "collection", "resources", "lists", "handbook", "notes")

# A topic is applied by a human and applied inconsistently. `topic:reverse-engineering` returns gpt4free,
# an AirPods client and a visual novel translator, so a topic match is a candidate and not a classification.
# This vocabulary is the second filter, and its pass rate is reported because it measures how noisy the
# first filter was.
RELEVANCE = ("security", "pentest", "penetration", "vulnerab", "exploit", "attack", "scanner",
             "fuzz", "recon", "payload", "xss", "sqli", "ssrf", "jwt", "oauth", "waf", "bypass",
             "cve", "malware", "forensic", "reverse engineer", "traffic", "intercept", "proxy")


def gh(args, timeout=45):
    try:
        r = subprocess.run(["gh"] + args, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            print(f"  gh failed: {r.stderr.strip()[:120]}", file=sys.stderr)
            return None
        return json.loads(r.stdout)
    except Exception as e:
        print(f"  gh error: {type(e).__name__}", file=sys.stderr)
        return None


def norm(s):
    s = (s or "").lower()
    s = re.sub(r"\b(the|a|an|framework|tool|tools|suite|project|official|scanner)\b", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


def corpus_index():
    """Slugs AND normalised names. The first version matched only repository slugs and therefore reported
    apktool, MobSF and ModSecurity as new to the lists, which they are plainly not: they are present under
    another URL or another name. An overlap check that only looks one way measures its own index."""
    slugs, names = set(), set()
    if not CORPUS.exists():
        return slugs, names
    for line in CORPUS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        u = e.get("url") or ""
        m = re.match(r"https?://(?:www\.)?github\.com/([^/]+)/([^/#?]+)", u)
        if m:
            slugs.add(f"{m.group(1).lower()}/{re.sub(r'\.git$', '', m.group(2)).lower()}")
        n = norm(e.get("name"))
        if len(n) >= 3:
            names.add(n)
        for alt in (e.get("names") or []):
            a = norm(alt)
            if len(a) >= 3:
                names.add(a)
    return slugs, names


def _name_hit(name, known_names):
    """Exact match, then containment for names long enough that containment is meaningful. `MobSF` versus
    `mobile security framework mobsf` is the case that made this necessary: equality alone reported a tool
    the lists plainly contain as new."""
    n = norm(name)
    if len(n) < 3:
        return False, None
    if n in known_names:
        return True, "name"
    if len(n) >= 5:
        for k in known_names:
            if len(k) >= 5 and (n in k or k in n):
                return True, "name_containment"
    return False, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=25, help="results per capability")
    ap.add_argument("--months", type=int, default=24, help="recency window on last push")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if args.check:
        rows = [json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines() if l.strip()] \
            if OUT.exists() else []
        problems = [r["id"] for r in rows if not r.get("capability") or not r.get("url")
                    or "in_corpus" not in r]
        if problems:
            print(f"{len(problems)} malformed candidate(s): {problems[:5]}", file=sys.stderr)
            return 1
        print(f"{len(rows)} candidate(s) checked, every one names a capability, a url and its corpus status")
        return 0

    cutoff = (datetime.now(timezone.utc) - timedelta(days=30 * args.months)).strftime("%Y-%m-%d")
    known, known_names = corpus_index()
    print(f"{len(QUERIES)} capability queries, recency window since {cutoff}, "
          f"{len(known)} corpus slugs and {len(known_names)} names for the overlap check")

    seen = {}
    for cap, phrase in QUERIES.items():
        q = f"{phrase} pushed:>{cutoff} archived:false"
        data = gh(["api", f"search/repositories?q={urllib_quote(q)}&sort=stars&order=desc"
                          f"&per_page={args.limit}"])
        if not data:
            continue
        for item in data.get("items") or []:
            full = (item.get("full_name") or "").lower()
            name_l = (item.get("name") or "").lower()
            if any(w in name_l for w in LIST_NAMES):
                continue
            desc_l = (item.get("description") or "").lower()
            if any(w in desc_l for w in ("a curated list", "a list of", "collection of resources")):
                continue
            relevant = any(w in (name_l + " " + desc_l) for w in RELEVANCE)
            if not full or full in seen:
                seen[full].setdefault("also_found_under", []).append(cap) if full in seen else None
                continue
            seen[full] = {
                "id": full,
                "capability": cap,
                "also_found_under": [],
                "name": item.get("name"),
                "url": item.get("html_url"),
                "desc": (item.get("description") or "")[:220],
                "stars": item.get("stargazers_count"),
                "last_push": (item.get("pushed_at") or "")[:10],
                "archived": bool(item.get("archived")),
                "in_corpus": (full in known) or _name_hit(name_l, known_names)[0],
                "in_corpus_by": ("slug" if full in known else _name_hit(name_l, known_names)[1]),
                "relevant": relevant,
                "status": "CANDIDATE",
            }
        print(f"  {cap:26} {len(data.get('items') or []):3d} results")

    rows = sorted(seen.values(), key=lambda r: (-(r["stars"] or 0), r["id"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")

    from collections import Counter
    relevant = [r for r in rows if r["relevant"]]
    new = [r for r in relevant if not r["in_corpus"]]
    by_cap = Counter(r["capability"] for r in new)
    summary = {
        "generated_at": date.today().isoformat(),
        "queries": len(QUERIES),
        "recency_months": args.months,
        "candidates": len(rows),
        "relevant": len(relevant),
        "filtered_out_as_irrelevant": len(rows) - len(relevant),
        "already_in_corpus": len(relevant) - len(new),
        "new_to_the_lists": len(new),
        "new_pct": round(100.0 * len(new) / len(relevant), 1) if relevant else 0.0,
        "topic_pass_rate_pct": round(100.0 * len(relevant) / len(rows), 1) if rows else 0.0,
        "new_by_capability": dict(by_cap.most_common()),
        "note": ("candidates only. Nothing here is admitted to the corpus, and the headline number is the "
                 "new_to_the_lists count, which measures what nineteen curated lists did not contain "
                 "rather than how many tools exist."),
    }
    SUMMARY.write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")

    print(f"\ncandidates {len(rows)}, relevant {len(relevant)} "
          f"({summary['topic_pass_rate_pct']}% of topic hits survive the vocabulary filter)")
    print(f"of the relevant: already in the corpus {len(relevant) - len(new)}, "
          f"new to the lists {len(new)} ({summary['new_pct']}%)")
    for cap, n in by_cap.most_common(6):
        print(f"  {cap:26} {n}")
    return 0


def urllib_quote(s):
    from urllib.parse import quote
    return quote(s, safe="")


if __name__ == "__main__":
    sys.exit(main())
