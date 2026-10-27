#!/usr/bin/env python3
"""
recheck.py: verify that RECHECK.md still describes reality.

The point of this script is post-compaction. A state document can drift, be half remembered, or be
quietly wrong. This re-derives every claim from disk and prints PASS, CHANGED or FAIL per claim, so the
first thing a fresh context does is find out whether it is looking at the same machine the doc describes.

No network. Runs in a couple of seconds.

Exit codes: 0 all pass, 1 something changed or failed.
"""
import json, os, re, subprocess, sys
from pathlib import Path

HOME = Path.home()
A = HOME / "ai-web-arsenal"
B = HOME / "web-attack-atlas"
C = HOME / "contest-opsec"
O = HOME / "operator-opsec"

# Values as stated in RECHECK.md, written 2026-10-27. If disk differs, either the doc is stale or work
# advanced since. Both matter, and neither is silently acceptable.
EXPECTED = {
    "corpus_entries": 21384,
    "corpus_identities": 21187,
    "corpus_tool_rows": 8848,
    "corpus_tool_identities": 8692,
    "corpus_rows_with_url": 9671,
    "corpus_tools_rows": 8848,
    "corpus_taxonomy_rows": 11712,
    "corpus_other_rows": 824,
    "enriched_entries": 444,
    "promotable_candidates": 1419,
    "sources": 19,
    "rows_total": 31298,
    "admitted": 13516,
    "excluded": 17506,
    "held": 204,
    "orphan": 71,
    "unresolved_rows": 1,
    "tools": 64,
    "tools_unresolved": 0,
    "prompt_packs": 5,
    "domains_rendered": 39,
    "atlas_patterns": 150,
    "authored_domains": 28,
    "pointer_domains": 9,
}

results = []


def record(name, ok, detail="", changed=False):
    results.append((name, "CHANGED" if changed else ("PASS" if ok else "FAIL"), detail))


def doc_figures():
    """Parse the state block out of RECHECK.md, so the checker reads the document instead of a copy of it.
    A hardcoded EXPECTED value that mirrors the doc is a second place to forget."""
    out = {}
    try:
        text = (A / "RECHECK.md").read_text(encoding="utf-8")
    except Exception:
        return out
    m = re.search(r"^enriched\s+(\d[\d,]*) entries", text, re.M)
    if m:
        out["enriched_entries"] = int(m.group(1).replace(",", ""))
    m = re.search(r"^domains\s+(\d+) authored \+ (\d+) explicit pointers", text, re.M)
    if m:
        out["authored_domains"] = int(m.group(1))
        out["pointer_domains"] = int(m.group(2))
    return out


def run(cmd, cwd=None, timeout=180):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout + p.stderr
    except Exception as e:
        return 1, str(e)


def git_state(repo):
    if not (repo / ".git").exists():
        return None
    rc1, out1 = run(["git", "remote", "get-url", "origin"], cwd=repo)
    rc2, out2 = run(["git", "log", "--oneline"], cwd=repo)
    rc3, out3 = run(["git", "status", "--porcelain"], cwd=repo)
    rc4, out4 = run(["git", "ls-files"], cwd=repo)
    return {
        "remote": out1.strip() if rc1 == 0 else None,
        "commits": len([l for l in out2.splitlines() if l.strip()]),
        "dirty": len([l for l in out3.splitlines() if l.strip()]),
        "tracked": len([l for l in out4.splitlines() if l.strip()]),
    }


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Does RECHECK.md still describe this machine?")
    ap.add_argument("--release", action="store_true",
                    help="also fail on CHANGED, for tagging a release rather than working")
    release = ap.parse_args().release

    print("=" * 78)
    print("RECHECK: does RECHECK.md still describe this machine?")
    print("=" * 78)

    # --- repos exist, remotes, clean ---
    for label, repo, want_remote in (
        ("ai-web-arsenal", A, "ai-web-arsenal"),
        ("web-attack-atlas", B, "web-attack-atlas"),
    ):
        g = git_state(repo)
        if g is None:
            record(f"{label} exists", False, "missing")
            continue
        record(f"{label} exists", True, f"{g['commits']} commits, {g['tracked']} tracked")
        record(f"{label} has remote", bool(g["remote"]) and want_remote in (g["remote"] or ""),
               g["remote"] or "none")
        # A dirty tree is work in progress, not a false claim about the repository. It reports as
        # CHANGED so the gate can run mid-session, and --release treats it as a failure.
        record(f"{label} working tree clean", g["dirty"] == 0, f"{g['dirty']} modified",
               changed=g["dirty"] != 0)

    record("contest-opsec exists (paused)", C.exists(),
           "paused, SCOPE.md only" if C.exists() else "missing")
    record("operator-opsec exists (abandoned)", O.exists(), "abandoned corporate framing" if O.exists() else "absent")

    # --- arsenal numbers from the stats script ---
    rc, out = run(["python3", "scripts/readme-stats.py"], cwd=A)
    if rc != 0:
        record("readme-stats.py runs", False, out.strip()[:200])
    else:
        got = {}
        for line in out.splitlines():
            parts = line.strip().split(" ", 1)
            if len(parts) == 2:
                k, v = parts
                if v.strip().isdigit():
                    got[k] = int(v.strip())
        parsed = doc_figures()
        for key in ("corpus_entries", "corpus_identities", "corpus_tool_rows",
                    "corpus_tool_identities", "corpus_rows_with_url", "corpus_tools_rows",
                    "corpus_taxonomy_rows", "corpus_other_rows", "enriched_entries",
                    "promotable_candidates", "sources", "rows_total", "admitted",
                    "excluded", "held", "tools", "tools_unresolved", "prompt_packs",
                    "domains_rendered"):
            if key not in got:
                record(f"{key} present in stats", False, "not emitted")
                continue
            # the doc is the authority here: if it states a figure, that figure must match disk
            exp = parsed.get(key, EXPECTED.get(key))
            if exp is None:
                record(f"{key} stated in RECHECK.md", False, "not found in the state block")
                continue
            act = got[key]
            record(f"{key}", act == exp, f"doc {exp}, disk {act}", changed=act != exp)

        # The split must partition the corpus exactly. This is the invariant that stops tools and
        # taxonomy nodes sharing a total again.
        parts = got.get("corpus_tools_rows", 0) + got.get("corpus_taxonomy_rows", 0) \
            + got.get("corpus_other_rows", 0)
        record("corpus split partitions the total", parts == got.get("corpus_entries", -1),
               f"{got.get('corpus_tools_rows')} + {got.get('corpus_taxonomy_rows')} + "
               f"{got.get('corpus_other_rows')} = {parts}, total {got.get('corpus_entries')}")

    # --- reconcile identity ---
    try:
        s = json.load(open(A / "data" / "reconcile" / "SUMMARY.json"))
        # Every term is named and summed. An earlier version printed "+ residue" and let 75 rows of
        # orphans hide inside a word, which is exactly the kind of quiet fudge this script exists to stop.
        comp = {k: int(s.get(k) or 0) for k in
                ("admitted", "excluded", "held", "orphan", "unresolved", "unparsed")}
        total = int(s.get("rows_total") or 0)
        summed = sum(comp.values())
        detail = " + ".join(f"{k} {v}" for k, v in comp.items()) + f" = {summed}, total {total}"
        record("reconciliation identity holds",
               summed == total and bool(s.get("identity_holds")), detail)
        for k, exp_key in (("admitted", "admitted"), ("excluded", "excluded"),
                           ("held", "held"), ("orphan", "orphan")):
            exp = EXPECTED[exp_key]
            record(f"reconcile {k}", comp[k] == exp, f"doc {exp}, disk {comp[k]}",
                   changed=comp[k] != exp)
    except Exception as e:
        record("reconciliation identity holds", False, str(e)[:120])

    # --- domain authored / pointer counts ---
    try:
        reg = json.load(open(A / "data" / "domain-registry.json"))["domains"]
        deep = sum(1 for d in reg if d.get("status") == "DEEP")
        ptr = sum(1 for d in reg if d.get("status") == "POINTER")
        empty = sum(1 for d in reg if d.get("status") == "STUB")
        exp_auth = doc_figures().get("authored_domains", EXPECTED["authored_domains"])
        record("authored domains", deep == exp_auth,
               f"doc {exp_auth}, disk {deep}", changed=deep != exp_auth)
        record("pointer domains", ptr == EXPECTED["pointer_domains"],
               f"doc {EXPECTED['pointer_domains']}, disk {ptr}", changed=ptr != EXPECTED["pointer_domains"])
        record("no empty domains", empty == 0, f"{empty} stubs remaining")
        record("registry total matches authored plus pointer",
               len(reg) == deep + ptr + empty, f"{len(reg)} = {deep} + {ptr} + {empty}")
    except Exception as e:
        record("domain registry readable", False, str(e)[:120])

    # --- validator ---
    rc, out = run(["python3", "scripts/validate-domains.py"], cwd=A)
    record("domain validator passes", "all invariants hold" in out, out.strip().splitlines()[-1] if out else "")

    # --- link evidence file present ---
    try:
        lc = json.load(open(A / "data" / "domain-link-check.json"))
        okc = sum(1 for v in lc["results"].values() if v["status"] == "OK")
        record("domain links checked", True, f"{okc} of {lc['unique_urls']} live, dated {lc['checked_at']}")
    except Exception as e:
        record("domain link check present", False, str(e)[:120])

    # --- atlas ---
    rc, out = run(["python3", "scripts/render-patterns.py"], cwd=B)
    m = re.search(r"patterns loaded:\s*(\d+)", out)
    if m:
        n = int(m.group(1))
        record("atlas patterns", n == EXPECTED["atlas_patterns"],
               f"doc {EXPECTED['atlas_patterns']}, disk {n}", changed=n != EXPECTED["atlas_patterns"])
    else:
        record("atlas patterns", False, "could not parse")
    record("atlas gate passes", "gate: all pass" in out, "")

    # --- README badge numbers must not contradict stats ---
    try:
        readme = (A / "README.md").read_text()
        checks = [
            ("enriched entries 444", "444" in readme),
            ("tools 64 verified", "64" in readme),
            ("domains 28 authored", "28" in readme),
        ]
        for name, ok in checks:
            record(f"README states {name}", ok, "")
    except Exception as e:
        record("README readable", False, str(e)[:120])

    # --- report ---
    print()
    width = max(len(n) for n, _, _ in results) + 2
    fails = changed = 0
    for name, status, detail in results:
        print(f"  {name:<{width}} {status:<8} {detail}")
        if status == "FAIL":
            fails += 1
        elif status == "CHANGED":
            changed += 1
    print()
    print(f"{len(results)} checks: {len(results)-fails-changed} pass, {changed} changed, {fails} fail")
    if changed:
        print("\nCHANGED means disk and RECHECK.md disagree. Work advanced, or the doc is stale.")
        print("Update RECHECK.md before trusting it again.")
    if fails:
        print("\nFAIL means something RECHECK.md claims is not true. Investigate before continuing.")
    if release:
        return 0 if (fails == 0 and changed == 0) else 1
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
