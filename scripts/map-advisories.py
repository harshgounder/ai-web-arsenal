#!/usr/bin/env python3
"""
map-advisories.py: classify harvested advisories into atoms and control classes.

This is a breadth engine, not an authoring pass. It produces records mechanically from public
advisories, and the honest thing to do with a mechanical classifier is to state its error mode:

  - every record carries the terms that matched, so a reader can disagree with the classification
    without rerunning it
  - confidence is high only where two or more distinct patterns matched, medium at one
  - an advisory that matches nothing is recorded as unmapped rather than forced into a class

The output is a separate dataset from the curated corpus, with its own counts, because mixing generated
records with hand authored ones is how a size claim gets inflated. This repo has made that mistake once
with corpus rows and is not making it again with advisories.

Input:  data/advisories/raw/*.jsonl
Output: data/advisories/advisories.jsonl, data/advisories/SUMMARY.json

Usage: python3 scripts/map-advisories.py [--sample]
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "advisories" / "raw"
OUT = ROOT / "data" / "advisories" / "advisories.jsonl"
SUMMARY = ROOT / "data" / "advisories" / "SUMMARY.json"

# atom -> patterns. Written to describe mechanisms, not products, and short enough to read.
ATOM_PATTERNS = {
    "A01": ["injection", "deserializ", "prototype pollution", "template injection",
            "command execution", "code execution", "expression language", "eval(",
            "inconsistent interpretation", "header injection", "log injection",
            "crlf injection", "xxe", "xml external", "request splitting",
            "serialization gadget", "unescaped", "unsanitized", "untrusted data",
            "neutralization", "polymorphic typing", "script injection"],
    "A02": ["ssrf", "server-side request forgery", "csrf", "cross-site request forgery",
            "open redirect", "request smuggling", "origin validation", "cors",
            "httpoxy", "url parsing", "redirect"],
    "A03": ["authentication bypass", "session fixation", "jwt", "oauth", "saml",
            "privilege escalation", "impersonat", "authorization bypass", "auth bypass",
            "improper authentication", "access control"],
    "A04": ["replay", "idempoten", "state", "race condition", "toctou", "time-of-check"],
    "A05": ["prototype pollution", "type confusion", "deserializ", "unexpected type"],
    "A06": ["path traversal", "directory traversal", "zip slip", "symlink", "absolute path",
            "filename", "file path", "directory", "arbitrary file", "file read", "file write", "path limitation"],
    "A07": ["denial of service", "redos", "regular expression", "unbounded", "resource exhaustion",
            "memory exhaustion", "infinite loop", "algorithmic complexity"],
    "A08": ["information disclosure", "information exposure", "sensitive information",
            "cleartext", "debug", "logs", "leak"],
    "A09": ["cryptograph", "weak hash", "padding oracle", "certificate validation", "tls",
            "signature verification", "improper verification", "random",
            "improper certificate", "insufficient entropy", "weak random", "insecure random"],
    "A10": ["business logic", "improper authorization", "authorization", "permission",
            "bypass", "validation"],
    "A11": ["malicious package", "dependency confusion", "typosquat", "supply chain",
            "compromised", "backdoor"],
    "A12": ["race condition", "timing", "ordering", "concurren"],
    "A13": ["side channel", "timing attack", "cache poisoning", "speculative"],
    "A14": ["phishing", "social engineering", "spoofing"],
    "A15": ["misconfiguration", "insecure default", "default configuration", "insecure default"],
    "A16": ["prompt injection", "llm", "language model", "agent", "model context"],
}

# atoms are grouped by the lens they belong to in the denominator, so a mapped advisory can be compared
# against the same sixteen lenses the coverage ledger uses.
ATOM_LENS = {
    "A01": "L04", "A02": "L06", "A03": "L06", "A04": "L08", "A05": "L07",
    "A06": "L07", "A07": "L09", "A08": "L07", "A09": "L06", "A10": "L08",
    "A11": "L10", "A12": "L08", "A13": "L01", "A14": "L11", "A15": "L09", "A16": "L12",
}

# the control class a defender would reach for, given the dominant atom. Deliberately coarse: this is a
# routing hint for a reader, not a claim that one class closes the finding.
ATOM_CONTROL = {
    "A01": "C07", "A02": "C02", "A03": "C01", "A04": "C05", "A05": "C03",
    "A06": "C08", "A07": "C10", "A08": "C11", "A09": "C06", "A10": "C02",
    "A11": "C13", "A12": "C05", "A13": "C10", "A14": "C13", "A15": "C12", "A16": "C07",
}

COMPILED = {a: [(p, re.compile(re.escape(p), re.I)) for p in pats] for a, pats in ATOM_PATTERNS.items()}


def classify(text):
    matched = {}
    for atom, pats in COMPILED.items():
        hits = [p for p, rx in pats if rx.search(text)]
        if hits:
            matched[atom] = hits
    if not matched:
        return [], {}, "unmapped", ""
    # strongest atom is the one with most distinct matches, tie broken by atom id for determinism
    ranked = sorted(matched.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    top = [a for a, hits in ranked if len(hits) == len(ranked[0][1])]
    atoms = sorted(top)
    distinct = sum(len(h) for h in matched.values())
    confidence = "high" if distinct >= 2 else "medium"
    return atoms, matched, confidence, atoms[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0, help="print N mapped records and exit")
    args = ap.parse_args()

    files = sorted(RAW.glob("*.jsonl"))
    if not files:
        print(f"nothing to map in {RAW}; run scripts/harvest-osv.py first", file=sys.stderr)
        return 1

    rows = []
    seen = set()
    for f in files:
        eco = f.stem.replace("_", "/")
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            v = json.loads(line)
            if v["id"] in seen:
                continue
            seen.add(v["id"])
            text = " ".join([v.get("summary") or "", (v.get("details") or "")[:2500]])
            atoms, matched, confidence, top = classify(text)
            rows.append({
                "id": v["id"],
                "aliases": v.get("aliases") or [],
                "ecosystem": eco,
                "package": v.get("_queried_as", "").split(":", 1)[1] if ":" in (v.get("_queried_as") or "") else "",
                "summary": (v.get("summary") or "")[:200],
                "atoms": atoms,
                "lens": ATOM_LENS.get(top, "") if atoms else "",
                "control_class": ATOM_CONTROL.get(top, "") if atoms else "",
                "matched": matched,
                "confidence": confidence,
                "published": v.get("published") or "",
                "severity": ((v.get("severity") or [{}])[0] or {}).get("type") or "",
            })

    if args.sample:
        for r in [x for x in rows if x["atoms"]][: args.sample]:
            print(json.dumps({k: r[k] for k in ("id", "package", "atoms", "confidence", "summary")},
                             ensure_ascii=False))
        return 0

    rows.sort(key=lambda r: (not r["atoms"], r["ecosystem"], r["id"]))
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")

    mapped = [r for r in rows if r["atoms"]]
    by_atom = Counter(a for r in mapped for a in r["atoms"])
    by_lens = Counter(r["lens"] for r in mapped)
    by_eco = Counter(r["ecosystem"] for r in rows)
    by_conf = Counter(r["confidence"] for r in rows)
    unmapped = len(rows) - len(mapped)

    summary = {
        "generated_at": "2026-10-27",
        "source": "OSV query API, scoped to a selected package list rather than filtered by keyword",
        "total": len(rows),
        "mapped": len(mapped),
        "unmapped": unmapped,
        "unmapped_pct": round(100.0 * unmapped / len(rows), 1) if rows else 0.0,
        "by_confidence": dict(by_conf),
        "by_ecosystem": dict(by_eco),
        "by_atom": dict(by_atom.most_common()),
        "by_lens": dict(by_lens.most_common()),
        "note": ("mechanical classification: confidence is high only where two or more distinct patterns "
                 "matched, and every record carries the terms that matched so a reader can disagree. "
                 "The unmapped share measures the classifier's recall, not the advisories' irrelevance: "
                 "reading a sample of them finds real mechanisms the pattern table does not name yet."),
    }
    SUMMARY.write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")

    print(f"advisories {len(rows)}, mapped {len(mapped)}, unmapped {unmapped} "
          f"({summary['unmapped_pct']}%)")
    print(f"confidence {dict(by_conf)}")
    print(f"top atoms {dict(by_atom.most_common(8))}")
    print(f"by lens {dict(by_lens.most_common(6))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
