#!/usr/bin/env python3
"""
merge-identities.py: collapse the union by tool identity, not by URL.

The corpus is deduplicated on canonical URL, which cannot see a rename (OWASP/Amass ->
owasp-amass/amass), a name variant (John the Ripper vs john), or a docs site and its repo listed
separately. That inflates the "24,759 canonical entries" claim, because two of those rows are one tool.

This computes a tool identity from the normalised name, merges rows that share it within the same
kind, and reports how many entries survive. The original corpus is not modified; the merged view is
written alongside it with every source preserved.

Output: data/corpus-merged.jsonl, data/corpus-merge-stats.json
"""
import json, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def norm(s):
    s = (s or "").lower()
    s = re.sub(r"\b(the|a|an|framework|tool|tools|suite|project|official)\b", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


def main():
    rows = [json.loads(l) for l in (DATA / "corpus.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    groups = defaultdict(list)
    for e in rows:
        n = norm(e.get("name"))
        if len(n) < 3:
            groups[("key", e["key"])].append(e)
        else:
            groups[(e.get("kind", "?"), n)].append(e)

    merged = []
    dup_groups = 0
    for g, items in groups.items():
        if len(items) == 1:
            merged.append(items[0])
            continue
        dup_groups += 1
        base = dict(items[0])
        base["merged_from"] = [i["key"] for i in items]
        base["sources"] = sorted({s for i in items for s in i.get("sources", [])})
        base["n_sources"] = len(base["sources"])
        base["names"] = sorted({n for i in items for n in (i.get("names") or [i.get("name")])})
        base["tier"] = next((i["tier"] for i in items if i.get("tier") == "core_web"), base.get("tier"))
        merged.append(base)

    with open(DATA / "corpus-merged.jsonl", "w", encoding="utf-8") as fh:
        for e in merged:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")

    stats = {
        "generated_at": "2026-10-27",
        "entries_by_url": len(rows),
        "entries_by_identity": len(merged),
        "collapsed": len(rows) - len(merged),
        "duplicate_groups": dup_groups,
        "largest_groups": sorted(
            ({"name": items[0].get("name"), "count": len(items),
              "urls": [i.get("url") for i in items][:4]}
             for items in groups.values() if len(items) > 1),
            key=lambda x: -x["count"])[:10],
    }
    # The corpus holds more than tools: taxonomy nodes harvested from list headings, plus social and
    # knowledge rows. Quoting entries_by_identity as "tool identities" overcounts tools 2.4x, so the
    # tool-only view is computed here and reported separately.
    by_kind = {}
    for r in rows:
        by_kind[r.get("kind", "?")] = by_kind.get(r.get("kind", "?"), 0) + 1
    tool_rows = [r for r in rows if r.get("kind") == "tool"]
    tool_keys = set()
    for r in tool_rows:
        nm = norm(r.get("name"))
        tool_keys.add(("k", r["key"]) if len(nm) < 3 else ("n", nm))
    stats["rows_by_kind"] = dict(sorted(by_kind.items(), key=lambda kv: -kv[1]))
    stats["tool_rows"] = len(tool_rows)
    stats["tool_identities"] = len(tool_keys)
    # Counts only real http(s) locators. One row carries "skt elecom/bomlens", an unparseable slug,
    # and counting it as a URL would make the link checkpoint under-report by one.
    stats["rows_with_url"] = sum(1 for r in rows
                                 if (r.get("url") or "").lower().startswith(("http://", "https://")))
    json.dump(stats, open(DATA / "corpus-merge-stats.json", "w"), indent=1)
    print(f"by url {len(rows)} -> by identity {len(merged)} (collapsed {stats['collapsed']} across {dup_groups} groups)")
    print(f"of {len(rows)} rows: {len(tool_rows)} are tools ({len(tool_keys)} tool identities); "
          f"rows with a url: {stats['rows_with_url']}")
    print(f"rows by kind: {stats['rows_by_kind']}")
    for g in stats["largest_groups"]:
        print(f"  {g['count']}x {str(g['name'])[:40]:40s} {str(g['urls'][:2])[:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
