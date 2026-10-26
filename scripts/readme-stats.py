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
try:
    print(f"corpus_identities {json.load(open(R/'data'/'corpus-merge-stats.json'))['entries_by_identity']}")
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
print(f"domains_with_data {doms}")
print(f"domains_rendered {rendered}")
print(f"prompt_packs {prompts}")
print("tiers " + json.dumps(tiers))
