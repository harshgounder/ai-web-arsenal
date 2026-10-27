#!/usr/bin/env python3
"""
preflight.py: check whether this machine can validate and rebuild the repo, before anything runs.

A fresh clone proved the need for this. Three gates failed there not because the repo was wrong but
because the companion repo was not beside it, and one of them failed with a traceback. An environment
problem reported as a repository problem is the most expensive kind of false alarm: it teaches people to
ignore the gate.

So this checks the four things that are actually environmental and prints exactly what to run for each:

  1. python version
  2. companion repo present
  3. raw harvest present (without it the corpus cannot be rebuilt from scratch)
  4. gh authenticated (only needed to re-run capability mining)

Exit 0 when everything a default gate needs is present, 1 when something needed is missing.

Run: python3 scripts/preflight.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATLAS = ROOT.parent / "web-attack-atlas"


def line(ok, name, detail, fix=""):
    mark = "ok  " if ok else "MISS"
    print(f"  {mark}  {name:34s} {detail}")
    if not ok and fix:
        print(f"        {fix}")


def main():
    print("preflight: can this machine validate and rebuild the repo?\n")
    problems = 0

    v = sys.version_info
    ok = (v.major == 3 and v.minor >= 10)
    line(ok, "python", f"{v.major}.{v.minor}.{v.micro}",
         "3.10 or newer is needed for the walrus and match-free stdlib features used here")
    problems += 0 if ok else 1

    atlas_ok = (ATLAS / "waves").exists() and (ATLAS / "data" / "atoms.json").exists()
    line(atlas_ok, "companion repo", str(ATLAS) if atlas_ok else "not found",
         f"git clone https://github.com/harshgounder/web-attack-atlas {ATLAS}")
    problems += 0 if atlas_ok else 1

    rivals = ROOT / "raw" / "rivals"
    taxonomy = ROOT / "raw" / "taxonomy"
    n_rivals = len(list(rivals.iterdir())) if rivals.exists() else 0
    n_tax = len(list(taxonomy.iterdir())) if taxonomy.exists() else 0
    raw_ok = n_rivals > 0 and n_tax > 0
    line(raw_ok, "raw harvest", f"{n_rivals} rival clones, {n_tax} taxonomy clones" if raw_ok
         else f"{n_rivals} rivals, {n_tax} taxonomy",
         "bash scripts/harvest-rivals.sh && bash scripts/harvest-taxonomy.sh   "
         "(needed only to rebuild the corpus from scratch, not to validate the committed data)")
    if not raw_ok:
        print("        note: the committed corpus and ledger are complete without this; only a")
        print("        from-scratch rebuild needs the raw clones")

    # A dependency outside this repo, discovered while checking reproducibility. WSTG and ASVS rows in
    # the taxonomy reconciliation are read from a sibling project, so the 624 of 706 figure cannot be
    # rebuilt from this repo alone. Stated rather than hidden.
    universe = Path.home() / "web-universe-work" / "universe-nodes.json"
    line(universe.exists(), "external: universe-nodes.json",
         str(universe) if universe.exists() else "not found",
         "needed only to rebuild the WSTG and ASVS taxonomy rows; the committed "
         "data/taxonomy-coverage.json stands without it")

    gh_ok = shutil.which("gh") is not None
    auth = "not installed"
    if gh_ok:
        r = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, timeout=30)
        auth = "authenticated" if r.returncode == 0 else "installed, not authenticated"
        gh_ok = r.returncode == 0
    line(gh_ok, "gh cli", auth, "gh auth login   (only needed to re-run capability mining)")

    print()
    if problems:
        print(f"{problems} item(s) needed for the default gate are missing. Everything else works.")
        return 1
    print("environment is sufficient. Run ./scripts/gate.sh next.")
    if not raw_ok:
        print("A from-scratch corpus rebuild additionally needs the raw harvest.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
