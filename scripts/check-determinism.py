#!/usr/bin/env python3
"""
check-determinism.py: rebuild the generated artefacts and prove nothing changed.

Why this matters. Every figure in this repo is produced by a chain of twelve scripts. If that chain is
not deterministic, then a number measured today is not the number a fresh clone would produce, and the
whole "regenerate from disk" claim collapses. This was verified by hand once; now it is a command.

The online stage (`verify-tools.py`) is excluded by default because registry versions change between
runs and that is not drift, it is the world moving. Use --full to include it knowingly.

Run: python3 scripts/check-determinism.py [--full]
Exit: 0 identical, 1 drift, 2 a stage failed.
"""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OFFLINE = [
    "scripts/build-corpus.py",
    "scripts/merge-identities.py",
    "scripts/reconcile.py",
    "scripts/taxonomy-reconcile.py",
    "scripts/gen-bootstrap.py",
    "scripts/normalize-atoms.py",
    "scripts/render-domain.py --all",
    "scripts/render-stubs.py",
    "scripts/build-indexes.py",
    "scripts/dedupe-names.py",
    "scripts/validate-domains.py",
    "scripts/render-ceiling.py",
]

# Files whose content legitimately depends on the network or on when it was run.
VOLATILE = {
    "data/install-matrix.json",
    # observations are evidence, append only, and never rebuilt by a generator
    "data/observations/observations.jsonl",
}

WATCH = ["data", "domains", "bootstrap", "docs"]


def snapshot():
    out = {}
    for top in WATCH:
        for p in sorted((ROOT / top).rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(ROOT).as_posix()
            if rel in VOLATILE or rel.startswith("bootstrap/logs/"):
                continue
            out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def run(cmd):
    argv = cmd.split()
    r = subprocess.run([sys.executable] + argv, cwd=ROOT, capture_output=True, text=True, timeout=900)
    return r.returncode, (r.stdout + r.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="include the online verify stage")
    args = ap.parse_args()

    stages = list(OFFLINE)
    if args.full:
        stages.insert(5, "scripts/verify-tools.py")

    before = snapshot()
    if not before:
        print("nothing to snapshot, which cannot be right", file=sys.stderr)
        return 2

    print(f"snapshot {len(before)} files across {', '.join(WATCH)}")
    for s in stages:
        rc, out = run(s)
        if rc != 0:
            print(f"\nstage failed: {s}\n{out[-800:]}", file=sys.stderr)
            return 2

    after = snapshot()

    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(k for k in before if k in after and before[k] != after[k])

    if not (added or removed or changed):
        print(f"after {len(stages)} stages: {len(after)} files, byte identical, zero drift")
        return 0

    print(f"\nDRIFT after {len(stages)} stages", file=sys.stderr)
    for k in changed:
        print(f"  changed  {k}", file=sys.stderr)
    for k in added:
        print(f"  added    {k}", file=sys.stderr)
    for k in removed:
        print(f"  removed  {k}", file=sys.stderr)
    print("\nEither a generator is not idempotent, or a stage writes a timestamp. Both make every")
    print("number in this repo a one-off reading rather than a measurement.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
