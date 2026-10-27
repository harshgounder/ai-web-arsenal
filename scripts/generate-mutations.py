#!/usr/bin/env python3
"""
generate-mutations.py: derive candidate pattern variants from the atlas, mechanically.

Why this exists. Hand writing patterns does not scale and neither does hand writing variants, but the
variants are the part where real findings live: the same mechanism behind a different parser, a different
principal or a different timing. So this generates them from a fixed rule set.

What it produces is a **queue, not a corpus**. Every candidate is marked unverified and says what would
have to be checked for it to become a pattern. It does not enter the atlas, it does not affect coverage,
and it is not counted anywhere near the curated numbers. A generated variant that was never run is a
hypothesis with a plausible shape, and this repo has spent twenty rounds learning what happens when
hypotheses get counted as facts.

Axes, each applied only if the source pattern does not already carry it:

  principal   the same action from a lower role, another tenant, or unauthenticated
  encoding    the same payload through a different encoding or case
  timing      the same sequence parallel, staggered, delayed or replayed
  context     the same value in a different request position
  protocol    the same action over a different protocol version
  state       the same action before, during or after the transition

Usage:
  python3 scripts/generate-mutations.py
  python3 scripts/generate-mutations.py --check
  python3 scripts/generate-mutations.py --pattern W01-0001
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATLAS = ROOT.parent / "web-attack-atlas"
OUT = ROOT / "data" / "mutations" / "mutations.jsonl"
SUMMARY = ROOT / "data" / "mutations" / "SUMMARY.json"

AXES = {
    "principal": [
        ("lower_role", "as an authenticated principal with fewer rights",
         "the action succeeds for a role that should not reach it"),
        ("other_tenant", "as a principal from a different tenant",
         "the effect lands on the other tenant's object while the caller stays authenticated as themselves"),
        ("unauthenticated", "with no credential at all",
         "the effect occurs with no principal, which means the check is in the client"),
    ],
    "encoding": [
        ("unicode_normalisation", "with the identifier in a different unicode normal form",
         "the same object or principal resolves, which means the canonicaliser and the store disagree"),
        ("double_encoding", "with the value encoded twice",
         "the effect survives one decoding layer more than expected"),
        ("case_fold", "with case altered where the layer below is case insensitive",
         "the check misses and the handler still resolves"),
    ],
    "timing": [
        ("parallel", "on several requests at once",
         "more than one effect for one logical action"),
        ("staggered_ms", "with a deliberate stagger inside the check to use window",
         "the effect appears only inside the window, which bounds it"),
        ("replay", "by repeating the same request after a delay",
         "a second effect from one intended action"),
    ],
    "context": [
        ("header", "carried in a header instead of the body",
         "the effect occurs from a position the validator does not read"),
        ("path", "carried in the path instead of a parameter",
         "the effect occurs from a position the router normalises differently"),
        ("multipart", "carried inside a multipart part",
         "the effect occurs from a nested position the parser does not inspect"),
    ],
    "protocol": [
        ("http2", "over HTTP/2 rather than 1.1",
         "the effect occurs through the translated request, which is where parsers differ"),
        ("grpc_web", "over a grpc-web encoded request",
         "the effect occurs through the second decoder"),
    ],
    "state": [
        ("before_commit", "before the object is committed",
         "the effect lands on a record that should not exist yet"),
        ("after_delete", "after a soft delete",
         "the effect resurrects or reaches a deleted object"),
    ],
}


def load_patterns():
    out = []
    if not ATLAS.exists():
        return out
    for f in sorted(ATLAS.glob("waves/*/patterns.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
    return out


def already_has(pattern, axis, variant):
    for m in pattern.get("mutations") or []:
        if m.get("axis") == axis and m.get("variant") == variant:
            return True
    return False


def generate(patterns, only=None):
    rows = []
    for p in patterns:
        if only and p["id"] != only:
            continue
        if p.get("status") == "DRAFT":
            continue
        for axis, variants in AXES.items():
            for variant, premise, check in variants:
                if already_has(p, axis, variant):
                    continue
                rows.append({
                    "id": f"{p['id']}.{axis}.{variant}",
                    "from_pattern": p["id"],
                    "title": p.get("title"),
                    "atoms": p.get("atom") or [],  # the atlas field is singular
                    "axis": axis,
                    "variant": variant,
                    "premise": premise,
                    "what_changes": f"{p.get('target_state') or 'the target state'} reached {premise}",
                    "check": check,
                    "counter": p.get("counter"),
                    "status": "UNVERIFIED",
                    "promote_when": ("a run reproduces it with a negative control that shows the same "
                                     "procedure without the mutation has no effect"),
                })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--pattern")
    args = ap.parse_args()

    patterns = load_patterns()
    if not patterns:
        # exit 3 means skip, not fail: the atlas being absent is an environment fact
        print(f"skip: no patterns at {ATLAS}. Clone the companion repo beside this one:", file=sys.stderr)
        print("  git clone https://github.com/harshgounder/web-attack-atlas ../web-attack-atlas",
              file=sys.stderr)
        return 3

    rows = generate(patterns, args.pattern)
    if args.check:
        problems = []
        ids = [r["id"] for r in rows]
        if len(ids) != len(set(ids)):
            problems.append("duplicate generated id")
        for r in rows:
            for k in ("from_pattern", "axis", "variant", "premise", "check", "promote_when"):
                if not r.get(k):
                    problems.append(f"{r['id']}: empty {k}")
            if r["status"] != "UNVERIFIED":
                problems.append(f"{r['id']}: generated rows must be UNVERIFIED, found {r['status']}")
        if problems:
            print(f"{len(problems)} problem(s):", file=sys.stderr)
            for p in problems[:20]:
                print(f"  {p}", file=sys.stderr)
            return 1
        print(f"{len(rows)} candidate variant(s) checked, all UNVERIFIED and structurally complete")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")

    by_axis = Counter(r["axis"] for r in rows)
    by_base = len({r["from_pattern"] for r in rows})
    summary = {
        "generated_at": "2026-10-27",
        "source_patterns": len(patterns),
        "patterns_with_variants": by_base,
        "candidates": len(rows),
        "by_axis": dict(by_axis.most_common()),
        "status": "UNVERIFIED",
        "note": ("a queue, not a corpus. Nothing here counts as coverage, nothing enters the atlas, and "
                 "each row states what would promote it. The generator skips any axis the source pattern "
                 "already carries, so these are additions rather than duplicates of hand written work."),
    }
    SUMMARY.write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")

    print(f"{len(rows)} candidates from {by_base} patterns across {len(by_axis)} axes")
    for k, v in by_axis.most_common():
        print(f"  {k:10} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
