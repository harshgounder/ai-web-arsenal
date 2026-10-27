#!/usr/bin/env python3
"""
render-playbooks.py: generate playbooks/*.md from data/playbooks/, and validate the references.

A playbook is the answer to the complaint that started this repo: a row in an awesome list tells you a
tool exists and nothing about what to run first on the stack in front of you. So a playbook is ordered,
and every step cites a real entry with an oracle already written for it.

Data is the source. The markdown is generated, and the generator refuses to emit a step that cites an
entry id which does not exist, because a playbook pointing at nothing is worse than no playbook.

Run:
  python3 scripts/render-playbooks.py            render all
  python3 scripts/render-playbooks.py --check     validate only, exit 1 on a broken reference
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "playbooks"
OUT = ROOT / "playbooks"


def entries():
    out = {}
    for f in sorted((ROOT / "data" / "domains").glob("D*.json")):
        if f.stem.endswith(".index"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        for e in d.get("entries", []):
            out[e.get("id")] = {**e, "domain": d.get("id"), "domain_title": d.get("title")}
    return out


def render(doc, arts):
    L = []
    a = L.append
    a(f"# Playbook: {doc['stack']}")
    a("")
    a("Generated from `data/playbooks/` by `scripts/render-playbooks.py`. Do not edit by hand.")
    a("")
    a("An ordered run for this stack. Every step cites an entry in this repo with an oracle already")
    a("written for it, because the order is the part a tool list cannot give you.")
    a("")
    a("## Is it this stack")
    a("")
    for s in doc.get("detect") or []:
        a(f"- {s}")
    a("")
    a("## The order")
    a("")
    a("| # | run | why here | what proves it |")
    a("|---|---|---|---|")
    for step in doc.get("order") or []:
        art = arts.get(step["entry"]) or {}
        name = art.get("name") or step["entry"]
        dom = art.get("domain")
        slug = None
        if dom:
            for cand in (ROOT / "domains").glob(f"{dom}-*.md"):
                slug = cand.name
        link = f"../domains/{slug}" if slug else "../domains/"
        a(f"| {step['step']} | [`{name}`]({link}) | {step['why']} | {step['oracle']} |")
    a("")
    a("## What will make you wrong")
    a("")
    for p in doc.get("pitfalls") or []:
        a(f"- {p}")
    a("")
    a("## What this playbook does not cover")
    a("")
    for n in doc.get("not_covered") or []:
        a(f"- {n}")
    a("")
    a("## Where each step lives")
    a("")
    for step in doc.get("order") or []:
        art = arts.get(step["entry"]) or {}
        a(f"- step {step['step']}: `{step['entry']}` in {art.get('domain', '?')}, "
          f"{art.get('domain_title', '')}")
    a("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    arts = entries()
    files = sorted(SRC.glob("*.json"))
    if not files:
        print("no playbooks found", file=sys.stderr)
        return 1

    broken = []
    count = 0
    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        for step in doc.get("order") or []:
            if step.get("entry") not in arts:
                broken.append(f"{f.stem}: step {step.get('step')} cites {step.get('entry')}, which does not exist")
        if args.check:
            continue
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / f"{f.stem}.md").write_text(render(doc, arts), encoding="utf-8")
        count += 1

    if broken:
        print(f"{len(broken)} broken reference(s):", file=sys.stderr)
        for b in broken:
            print(f"  {b}", file=sys.stderr)
        return 1

    if args.check:
        print(f"{len(files)} playbook(s) checked, every cited entry exists")
    else:
        print(f"rendered {count} playbook(s) into {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
