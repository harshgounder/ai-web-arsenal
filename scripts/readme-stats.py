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
_dom_entries = []
for _f in glob.glob(str(R/"data"/"domains"/"D*.json")):
    if _f.endswith(".index.json"):
        continue
    _dom_entries.extend(json.load(open(_f)).get("entries", []))
print(f"entries_total {len(_dom_entries)}")
for _k in ("preconditions", "oracle", "evades", "detected_by"):
    print(f"entries_with_{_k} {sum(1 for e in _dom_entries if e.get(_k))}")
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
    # coverage_l2 means exactly L2. An earlier version counted L2+L3 here, which made the label a
    # lie and broke a claim that compared it against a pure L2 count.
    print(f"coverage_l2 {sum(1 for r in _cov if r['level'] == 'L2')}")
    print(f"coverage_l3 {sum(1 for r in _cov if r['level'] == 'L3')}")
    print(f"coverage_l2plus {sum(1 for r in _cov if r['level'] in ('L2', 'L3'))}")
    _gap = json.load(open(R/"data"/"gap"/"SUMMARY.json")) if (R/"data"/"gap"/"SUMMARY.json").exists() else {}
    print(f"gap_total {_gap.get('gap_total', 0)}")
    for _k in ("reachable_by_authoring", "reachable_by_lab", "unavailable"):
        print(f"gap_{_k} {_gap.get(_k, 0)}")
    # the stats parser only accepts integers, so the ceiling is emitted in tenths
    print(f"ceiling_pct_tenths {round(float(_gap.get('ceiling_pct', 0)) * 10)}")
except Exception:
    print("denominator_factors ?")
try:
    _lc = json.load(open(R/"data"/"domain-link-check.json"))
    print(f"link_urls {_lc['unique_urls']}")
    print(f"link_ok {sum(1 for r in _lc['results'].values() if r['status'] == 'OK')}")
except Exception:
    print("link_urls 0")
try:
    _reg = json.load(open(R/"data"/"domain-registry.json"))["domains"]
    print(f"domains_total {len(_reg)}")
    print(f"domains_authored {sum(1 for d in _reg if d.get('status') == 'DEEP')}")
    print(f"domains_pointer {sum(1 for d in _reg if d.get('status') == 'POINTER')}")
except Exception:
    print("domains_total 0")
print(f"domains_with_data {doms}")
print(f"domains_rendered {rendered}")
print(f"prompt_packs {prompts}")
try:
    _cc = json.load(open(R/"data"/"counters"/"classes.json"))
    print(f"counter_classes {len(_cc['classes'])}")
except Exception:
    print("counter_classes 0")
try:
    _adv = json.load(open(R/"data"/"advisories"/"SUMMARY.json"))
    print(f"advisories_total {_adv['total']}")
    print(f"advisories_mapped {_adv['mapped']}")
    print(f"advisories_unmapped {_adv['unmapped']}")
except Exception:
    print("advisories_total 0")
try:
    _mu = json.load(open(R/"data"/"mutations"/"SUMMARY.json"))
    print(f"mutation_candidates {_mu['candidates']}")
except Exception:
    print("mutation_candidates 0")
try:
    _cap = json.load(open(R/"data"/"capability"/"SUMMARY.json"))
    print(f"capability_candidates {_cap['candidates']}")
    print(f"capability_relevant {_cap['relevant']}")
    print(f"capability_new {_cap['new_to_the_lists']}")
except Exception:
    print("advisories_total 0")
try:
    _d31 = json.load(open(R/"data"/"domains"/"D31.json"))
    print(f"rea_gaps_built {sum(1 for g in _d31['gaps'] if g.get('status') == 'built')}")
    print(f"rea_gaps_partial {sum(1 for g in _d31['gaps'] if g.get('status') == 'partial')}")
except Exception:
    print("rea_gaps_built 0")
print("tiers " + json.dumps(tiers))
