#!/usr/bin/env python3
"""Compute the numbers that appear in README.md. Never type a count by hand."""
import json, glob
from pathlib import Path
R = Path(__file__).resolve().parent.parent
def n(p, default=0):
    try: return len([l for l in open(p) if l.strip()])
    except Exception: return default
corpus = n(R/"data"/"corpus.jsonl")
rivals = len(json.load(open(R/"data"/"rivals.json")))
mat = json.load(open(R/"data"/"install-matrix.json"))
tools = len(mat["tools"]); unres = sum(1 for t in mat["tools"] if t["status"]=="unresolved")
inst = sum(1 for t in mat["tools"] if t["status"]=="installed")
summ = json.load(open(R/"data"/"reconcile"/"SUMMARY.json"))
doms = len(glob.glob(str(R/"data"/"domains"/"D*.json")))
rendered = len(glob.glob(str(R/"domains"/"D*.md")))
prompts = len(glob.glob(str(R/"prompts"/"*.md")))
tiers = {}
for l in open(R/"data"/"corpus.jsonl"):
    t = json.loads(l)["tier"]; tiers[t] = tiers.get(t,0)+1
print(f"corpus_entries {corpus}")
_splits = {"corpus_tools_rows": "corpus.tools.jsonl",
           "corpus_taxonomy_rows": "corpus.taxonomy.jsonl",
           "corpus_other_rows": "corpus.other.jsonl"}
for _k, _f in _splits.items():
    print(f"{_k} {n(R/'data'/_f)}")
try:
    _ms = json.load(open(R/'data'/'corpus-merge-stats.json'))
    print(f"corpus_identities {_ms['entries_by_identity']}")
    print(f"corpus_tool_rows {_ms.get('tool_rows', 0)}")
    print(f"corpus_tool_identities {_ms.get('tool_identities', 0)}")
    print(f"corpus_rows_with_url {_ms.get('rows_with_url', 0)}")
except Exception:
    print("corpus_identities ?")
enr=sum(len(json.load(open(f))["entries"]) for f in glob.glob(str(R/"data"/"domains"/"D*.json")) if not f.endswith(".index.json"))
cand=sum(json.load(open(f))["indexed_not_enriched"] for f in glob.glob(str(R/"data"/"domains"/"*.index.json")))
print(f"enriched_entries {enr}")
print(f"promotable_candidates {cand}")
print(f"sources {rivals}")
print(f"rows_total {summ['rows_total']}")
print(f"admitted {summ['admitted']}")
print(f"excluded {summ['excluded']}")
print(f"held {summ['held']}")
print(f"identity {summ['identity_holds']}")
print(f"tools {tools}")
print(f"tools_unresolved {unres}")
print(f"tools_installed_already {inst}")
try:
    _den = sorted(glob.glob(str(R/"data"/"denominator"/"L*.json")))
    _fac = 0; _lens = 0
    for _f in _den:
        _d = json.load(open(_f))
        _n = len(_d.get("factors") or [])
        if _n:
            _lens += 1
            _fac += _n
    print(f"denominator_factors {_fac}")
    print(f"denominator_lenses {_lens}")
    _cov = [json.loads(l) for l in open(R/"data"/"coverage"/"coverage.jsonl") if l.strip()] if (R/"data"/"coverage"/"coverage.jsonl").exists() else []
    print(f"coverage_mapped {len(_cov)}")
    print(f"coverage_l2 {sum(1 for r in _cov if r['level'] in ('L2','L3'))}")
    print(f"coverage_l3 {sum(1 for r in _cov if r['level'] == 'L3')}")
    _gap = json.load(open(R/"data"/"gap"/"SUMMARY.json")) if (R/"data"/"gap"/"SUMMARY.json").exists() else {}
    for _k in ("reachable_by_authoring", "reachable_by_lab", "unavailable"):
        print(f"gap_{_k} {_gap.get(_k, 0)}")
    # the stats parser only accepts integers, so the ceiling is emitted in tenths
    print(f"ceiling_pct_tenths {round(float(_gap.get('ceiling_pct', 0)) * 10)}")
except Exception:
    print("denominator_factors ?")
print(f"domains_with_data {doms}")
print(f"domains_rendered {rendered}")
print(f"prompt_packs {prompts}")
print("tiers " + json.dumps(tiers))
