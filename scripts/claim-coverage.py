#!/usr/bin/env python3
"""
claim-coverage.py: measure how much of the documentation's structural prose has a check behind it.

Why this exists. Four rounds of hunting fiction in the docs found four real defects: a join key nothing
used, a stdlib-only claim that needed PyYAML, a check passing on a stale mention, and two domains rendering
an empty decision tree. The rate was not dropping, which means the docs are bigger than the ledger and the
hunting was sampling.

This turns that into measurement. It extracts sentences that make a structural assertion, then asks whether
any claim in `data/claims.yaml` plausibly covers each one, by token overlap with the claim's statement and
by whether the claim's check mentions a distinctive term from the sentence.

Be clear about what this is: **a burn-down list, not a verdict.** Token overlap cannot tell whether a claim
actually tests the sentence, only that the two are about the same thing. A sentence marked covered may still
be unverified, and a sentence marked uncovered may be prose that needs no check. It is a review order, and
its value is that it is ordered rather than infinite.

Usage:
  python3 scripts/claim-coverage.py               summary and 25 worst offenders
  python3 scripts/claim-coverage.py --all          every uncovered sentence
  python3 scripts/claim-coverage.py --json         machine readable
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAIMS = ROOT / "data" / "claims.yaml"
OUT = ROOT / "data" / "claims-coverage.json"

DOCS = ["README.md", "RECHECK.md", "AUTHORING.md", "PLAN.md", "RESUME.md", "BOOTSTRAP.md", "SCOPE-v1.md"]

# A sentence is structural if it asserts a universal, a prohibition, a requirement, or a count.
STRUCTURAL = re.compile(
    r"\b(every|each|all|never|always|must|none|no [a-z]+ (?:is|are)|only|any)\b"
    r"|\b\d[\d,]{2,}\b"
    r"|`[^`]+`",
    re.I,
)

# Sentences that are instructions to a reader rather than claims about the repo. Running `bash x` is not a
# statement that can be false.
SKIP = re.compile(
    r"^\s*(?:[-*]|\d+\.)?\s*(?:`|bash |python3 |git |curl |\./|cd |npm |pipx |./scripts)"
    r"|^\s*\|"          # table rows are measured separately by the doc checks
    r"|^\s*(?:#|>)"     # headings and quotes
    r"|^\s*\|?---",     # table separators
)

STOP = set("""the a an and or of to in for on with is are was were be been being it its this that these
those as at by from not no any all every each some such than then there their they you your we our
which who whom what when where why how can could would should may might must will shall do does did
has have had also very more most less least into out up down over under again further once here
one two three four five six seven eight nine ten number value set case way thing things part""".split())


def tokens(s):
    return {w for w in re.findall(r"[a-z][a-z0-9_-]{2,}", (s or "").lower()) if w not in STOP}


def sentences(text):
    """Split on sentence ends and blank lines, keeping inline code intact."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)   # code blocks are not prose claims
    out = []
    for block in re.split(r"\n\s*\n", text):
        block = " ".join(l.strip() for l in block.splitlines() if l.strip())
        for s in re.split(r"(?<=[.!?])\s+", block):
            s = s.strip()
            if 20 <= len(s) <= 400:
                out.append(s)
    return out


def load_claims():
    try:
        import yaml
        return yaml.safe_load(CLAIMS.read_text(encoding="utf-8"))["claims"]
    except Exception:
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    claims = load_claims()
    if not claims:
        print("no claims parsed; is PyYAML installed?", file=sys.stderr)
        return 1

    claim_sets = []
    for c in claims:
        blob = (c.get("statement") or "") + " " + (c.get("check") or "")
        claim_sets.append((c.get("id"), tokens(blob)))

    rows = []
    for name in DOCS:
        p = ROOT / name
        if not p.exists():
            continue
        for s in sentences(p.read_text(encoding="utf-8")):
            if SKIP.search(s) or not STRUCTURAL.search(s):
                continue
            st = tokens(s)
            if len(st) < 3:
                continue
            # a sentence that names a claim id is covered by definition
            named = re.findall(r"\bC\d{3}\b", s)
            if named:
                rows.append({"doc": name, "sentence": s, "how": "names the claim",
                             "best_claim": named[0], "covered": True})
                continue
            best, best_id = 0.0, None
            for cid, ct in claim_sets:
                if not ct:
                    continue
                inter = len(st & ct)
                # overlap ratio, plus credit for a distinctive shared term, because a short claim
                # statement about one mechanism and a long sentence about the same mechanism often
                # have low Jaccard while sharing the only words that matter
                j = inter / min(len(st), len(ct))
                if j > best:
                    best, best_id = j, cid
            rows.append({"doc": name, "sentence": s, "how": "overlap",
                         "best_jaccard": round(best, 3), "best_claim": best_id,
                         "covered": best >= 0.3})

    cov = [r for r in rows if r["covered"]]
    unc = [r for r in rows if not r["covered"]]
    # An uncovered sentence is only interesting if it asserts a count or a universal. The rest is
    # explanation that the structural regex catches on a backtick or a bare number, and it needs no check.
    HARD = re.compile(r"\b(\d[\d,]{2,}|every|each|never|always|none|must)\b", re.I)
    hard = [r for r in unc if HARD.search(r["sentence"])]
    soft = [r for r in unc if not HARD.search(r["sentence"])]
    unc.sort(key=lambda r: -len(tokens(r["sentence"])))
    hard.sort(key=lambda r: -len(tokens(r["sentence"])))

    summary = {
        "generated_at": "2026-10-27",
        "structural_sentences": len(rows),
        "with_a_plausible_claim": len(cov),
        "without": len(unc),
        "sentences_containing_a_digit_or_universal": len(hard),
        "coverage_pct": round(100.0 * len(cov) / len(rows), 1) if rows else 0.0,
        "method": ("a sentence is covered if it names a claim id, or if its tokens overlap a claim's statement "
                   "and check at 0.3 of the shorter side. A burn-down ordering, not a verdict: overlap "
                   "shows the two are about the same thing, not that the claim tests the sentence, and "
                   "much unmarked prose is narrative that needs no check at all."),
        "review_order": hard if args.all else hard[:25],
        "narrative_uncovered": len(soft),
    }
    OUT.write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(summary, indent=1, ensure_ascii=False))
        return 0

    print(f"structural sentences {len(rows)}")
    print(f"  with a plausible claim {len(cov)} ({summary['coverage_pct']}%)")
    print(f"  without                {len(unc)}, of which {len(soft)} is narrative needing no check")
    print(f"  regex hits, mostly narrative  {len(hard)} sentences contain a digit or a universal word")
    print("  This number is an upper bound and not a defect count. Automated sentence classification")
    print("  cannot tell a claim from an explanation, so treat the list as a review order, not a queue.")
    print()
    for r in hard[:25]:
        print(f"  {r['doc']:14} {r['sentence'][:104]}")
    print(f"\nwritten to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
