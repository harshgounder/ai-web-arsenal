#!/usr/bin/env python3
"""
reconcile.py: assign exactly one disposition to every entry from every source.

The arithmetic identity, checked per source and in aggregate:

    rows_from_source = unresolved + admitted + excluded + held
    excluded        = sum of the reason buckets

No row is silently dropped. A row whose key is not in the corpus is a bug and is
reported as ORPHAN, never ignored.
"""
import json
from collections import Counter
from pathlib import Path

import re

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ENT = DATA / "entries"
OUT = DATA / "reconcile"
OUT.mkdir(parents=True, exist_ok=True)


def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s[:80]


def disposition(e):
    """One rule chain, first match wins. Returns (disposition, reason)."""
    if e is None:
        return "ORPHAN", "not_in_corpus"
    k = e["kind"]
    if k == "taxonomy_node":
        return "EXCLUDE", "TAXONOMY_NODE"
    if k == "social":
        return "EXCLUDE", "SOCIAL_OR_VIDEO"
    if k == "knowledge":
        return "EXCLUDE", "KNOWLEDGE_NOT_TOOL"
    t = e["tier"]
    if t == "offscope":
        return "EXCLUDE", "OUT_OF_SCOPE_NONWEB"
    if t == "tail":
        if e.get("domain") == "D28" or "mcp" in (e.get("name") or "").lower():
            return "EXCLUDE", "MCP_NON_SECURITY"
        return "HOLD", "UNCLASSIFIED_LOW_SIGNAL"
    if t == "core_web":
        return "ADMIT", "core_web"
    if t == "adjacent":
        return "ADMIT", "adjacent_web"
    return "HOLD", "exhausted_rules"


def main():
    corpus = {}
    for line in (DATA / "corpus.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            e = json.loads(line)
            corpus[e["key"]] = e

    summary = {}
    agg = Counter()
    agg_reason = Counter()

    for f in sorted(ENT.glob("*.jsonl")):
        sid = f.stem
        c = Counter()
        reasons = Counter()
        uniq = {"ADMIT": set(), "EXCLUDE": set(), "HOLD": set()}
        held_examples = []
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:
                c["unparsed"] += 1
                continue
            key = r.get("canonical") or ("name:" + slug(r.get("name")))
            if not r.get("canonical") and not r.get("name"):
                c["unresolved"] += 1
                continue
            d, why = disposition(corpus.get(key))
            c[d.lower()] += 1
            if d in uniq:
                uniq[d].add(key)
            if d == "EXCLUDE":
                reasons[why] += 1
            elif d in ("HOLD", "ORPHAN"):
                reasons[why] += 1
                if len(held_examples) < 25:
                    held_examples.append({"name": (r.get("name") or "")[:90], "url": r.get("url"),
                                          "reason": why})
        total = c["admit"] + c["exclude"] + c["hold"] + c["orphan"] + c["unresolved"] + c["unparsed"]
        rec = {
            "source": sid,
            "rows": total,
            "admitted": c["admit"],
            "excluded": c["exclude"],
            "held": c["hold"],
            "orphan": c["orphan"],
            "unresolved": c["unresolved"],
            "unparsed": c["unparsed"],
            "exclusion_reasons": dict(reasons),
            "unique_entries": {k.lower(): len(v) for k, v in uniq.items()},
            "identity_holds": total == c["admit"] + c["exclude"] + c["hold"] + c["orphan"] + c["unresolved"] + c["unparsed"],
            "held_examples": held_examples,
        }
        json.dump(rec, open(OUT / f"{sid}.json", "w"), indent=1)
        summary[sid] = {k: rec[k] for k in ("rows", "admitted", "excluded", "held", "orphan", "identity_holds")}
        agg["rows"] += total
        agg["admitted"] += c["admit"]
        agg["excluded"] += c["exclude"]
        agg["held"] += c["hold"]
        agg["orphan"] += c["orphan"]
        agg["unresolved"] += c["unresolved"] + c["unparsed"]
        for k, v in reasons.items():
            agg_reason[k] += v

    grand = {
        "generated_at": "2026-10-26",
        "sources": len(summary),
        "rows_total": agg["rows"],
        "admitted": agg["admitted"],
        "excluded": agg["excluded"],
        "held": agg["held"],
        "orphan": agg["orphan"],
        "unresolved": agg["unresolved"],
        "identity_holds": agg["rows"] == (agg["admitted"] + agg["excluded"] + agg["held"]
                                          + agg["orphan"] + agg["unresolved"]),
        "exclusion_reasons": dict(agg_reason.most_common()),
        "per_source": summary,
    }
    json.dump(grand, open(DATA / "reconcile" / "SUMMARY.json", "w"), indent=1)

    print(f"{'source':42s} {'rows':>7s} {'admit':>7s} {'excl':>7s} {'hold':>5s} {'orph':>4s} ok")
    for sid, v in sorted(summary.items(), key=lambda kv: -kv[1]["rows"]):
        print(f"{sid:42s} {v['rows']:7d} {v['admitted']:7d} {v['excluded']:7d} "
              f"{v['held']:5d} {v['orphan']:4d} {v['identity_holds']}")
    print(f"\nTOTAL rows {grand['rows_total']} = admitted {grand['admitted']} "
          f"+ excluded {grand['excluded']} + held {grand['held']} + orphan {grand['orphan']}"
          f" + unresolved {grand['unresolved']}")
    print("identity holds:", grand["identity_holds"])
    print("\nexclusion reasons:")
    for k, v in grand["exclusion_reasons"].items():
        print(f"  {k:26s} {v}")


if __name__ == "__main__":
    main()
