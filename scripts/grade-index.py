#!/usr/bin/env python3
"""
grade-index.py: separate genuinely promotable candidates from noise in the domain indexes.

The headline "10,476 indexed, not enriched" was inflated by keyword matching pulling in directory
pages, book listings, badge SVGs and cheat sheets. A count that includes those is not a backlog, it
is a measure of how noisy the matcher is.

Each indexed entry is graded:
  PROMOTABLE  a tool or product with a real URL and a description, worth enriching
  REFERENCE   documentation, spec or cheat sheet. Useful, but not an entry to enrich
  NOISE       directory page, book, social post, badge image, or no usable description

Indexes are rewritten with only PROMOTABLE kept in the entries list, and the filtered counts recorded
so nothing is silently dropped.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOISE_HOST = re.compile(
    r"(glama\.ai|mcp\.so|smithery\.ai|pulsemcp\.com|mcpservers\.org|"
    r"amazon\.|manning\.com|goodreads\.|oreilly\.|packtpub\.|nostarch\.|"
    r"youtube\.com|youtu\.be|medium\.com|twitter\.com|x\.com|reddit\.com|"
    r"linkedin\.com|facebook\.com|discord\.|t\.me|substack\.com)", re.I)
REF_HOST = re.compile(
    r"(cheatsheetseries\.owasp\.org|owasp\.org|portswigger\.net/web-security|"
    r"book\.hacktricks\.wiki|swagger\.io/specification|modelcontextprotocol\.io|"
    r"genai\.owasp\.org|atlas\.mitre\.org|first\.org|cisa\.gov|"
    r"rfc-editor\.org|w3\.org|docs\.oasis-open\.org|cwe\.mitre\.org|cve\.org)", re.I)
BAD_EXT = re.compile(r"\.(svg|png|jpe?g|gif|ico)(\?|$)", re.I)


def grade(e):
    u = e.get("url") or ""
    n = e.get("name") or ""
    if not u.startswith("http"):
        return "NOISE"
    if BAD_EXT.search(u) or n.startswith("!["):
        return "NOISE"
    if NOISE_HOST.search(u):
        return "NOISE"
    if REF_HOST.search(u):
        return "REFERENCE"
    if e.get("kind") == "knowledge":
        return "REFERENCE"
    if len((e.get("name") or "").strip()) < 2:
        return "NOISE"
    return "PROMOTABLE"


def main():
    total = {"PROMOTABLE": 0, "REFERENCE": 0, "NOISE": 0}
    print(f"{'dom':5s} {'was':>6s} {'promotable':>10s} {'reference':>10s} {'noise':>7s}")
    grand = 0
    for f in sorted((ROOT / "data" / "domains").glob("*.index.json")):
        d = json.load(open(f))
        was = d.get("indexed_not_enriched") or len(d.get("entries", []))
        keep, ref, noise = [], 0, 0
        for e in d.get("entries", []):
            g = grade(e)
            if g == "PROMOTABLE":
                keep.append(e)
            elif g == "REFERENCE":
                ref += 1
            else:
                noise += 1
        d["graded_at"] = "2026-10-27"
        d["indexed_raw"] = was
        d["promotable"] = len(keep)
        d["reference"] = ref
        d["noise"] = noise
        d["entries"] = keep
        d["note"] = ("entries kept here are PROMOTABLE only. reference material and noise are counted, "
                     "not stored. the raw count was the keyword matcher's output, not a backlog.")
        json.dump(d, open(f, "w"), indent=1)
        total["PROMOTABLE"] += len(keep)
        total["REFERENCE"] += ref
        total["NOISE"] += noise
        print(f"{d['domain']:5s} {was:6d} {len(keep):10d} {ref:10d} {noise:7d}")
    grand = sum(total.values())
    print(f"\nraw {grand} -> promotable {total['PROMOTABLE']}, reference {total['REFERENCE']}, noise {total['NOISE']}")
    json.dump({"graded_at": "2026-10-27", **total, "raw_total": grand},
              open(ROOT / "data" / "index-grades.json", "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
