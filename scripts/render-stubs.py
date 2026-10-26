#!/usr/bin/env python3
"""
render-stubs.py: write a stub document for every domain that has no authored data yet.

A stub is not an empty placeholder. It declares:
  - the surfaces and atoms the domain is expected to exercise
  - its required cells, with the reason each cell is required
  - how much corpus material already exists for it, counted from disk
  - the exact checklist that turns it from STUB to DEEP
  - which write-suite wave in web-attack-atlas it maps onto, if any

That way the 37-domain table is honest: every domain exists, and every one says whether it has content.
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = json.load(open(ROOT / "data" / "domain-registry.json"))
OUT = ROOT / "domains"
OUT.mkdir(exist_ok=True)

SURFACE = {
    "S01": "transport and edge", "S02": "server stack and runtime", "S03": "routing and parsing",
    "S04": "identity and session", "S05": "authorization model", "S06": "data layer",
    "S07": "serialization", "S08": "client side", "S09": "API protocols",
    "S10": "business logic", "S11": "cloud control plane", "S12": "supply chain",
    "S13": "AI application surface", "S14": "agent and tooling surface", "S15": "browser and native bridge",
    "S16": "human layer", "S17": "perimeter that gates the app", "meta": "meta", "all": "cross-cutting",
}
ATOMS = json.load(open(Path.home() / "web-attack-atlas" / "data" / "atoms.json"))
AN = {a["id"]: a["name"] for a in ATOMS["atoms"]}
STAGE = {
    "L01": "scope and authorisation must be recorded before any request",
    "L02": "passive acquisition needs no target contact and should always exist",
    "L03": "you cannot test a surface you have not mapped",
    "L04": "discovery is the highest yield step and needs automation",
    "L05": "hypothesis generation from the stack is where AI either helps or hallucinates",
    "L06": "probing needs an oracle, not a guess",
    "L07": "exploitation and chaining is the step everything else serves",
    "L08": "proof with a negative control is what separates a finding from a note",
    "L09": "escalation is where a single bug becomes an incident",
    "L10": "findings without impact framing get closed as informational",
    "L11": "fix verification is the least covered stage in the industry",
    "L12": "continuous monitoring catches what a point in time test cannot",
}
ATLAS = {
    "D05": "W02", "D12": "W01", "D07": "W04", "D13": "W05", "D10": "W06",
    "D04": "W07", "D08": "W03", "D11": "W02", "D17": "W11", "D19": "W12",
}


def main():
    rows = [json.loads(l) for l in (ROOT / "data" / "corpus.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    dom_count = Counter(r.get("domain") for r in rows)
    authored = {p.stem for p in (ROOT / "data" / "domains").glob("D*.json") if not p.stem.endswith(".index")}

    made = 0
    for d in REG["domains"]:
        did = d["id"]
        if did in authored:
            continue
        import re as _re
        slug = d["title"].split(":")[0].strip().lower()
        slug = _re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
        path = OUT / f"{did}-{slug}.md"
        L = []
        a = L.append
        a(f"# {did}: {d['title']}")
        a("")
        a("Status: **STUB**. The shape is declared, the content is not written yet. This is stated at the")
        a("top rather than discovered by reading.")
        a("")
        a("## What this domain covers")
        a("")
        surf = ", ".join(f"`{s}` {SURFACE.get(s, s)}" for s in d["surfaces"])
        a(f"Surfaces: {surf}")
        a("")
        if d["atoms"]:
            a("Expected primitives: " + ", ".join(f"`{x}` {AN.get(x, '')}" for x in d["atoms"]))
        else:
            a("Expected primitives: none directly, this domain is a cross-cutting or infrastructure layer.")
        a("")
        if did in ATLAS:
            a(f"Write-suite counterpart in `web-attack-atlas`: wave **{ATLAS[did]}**.")
            a("")
        a("## Required cells, declared now")
        a("")
        a("A cell is `surface / lifecycle stage / agency level`. Each is required only if a practitioner")
        a("would want something there, and the reason is reviewable. Nothing in this domain may ship")
        a("without filling these or recording why one is impossible.")
        a("")
        a("| cell | why it is required | filled |")
        a("|---|---|---|")
        for cell in d.get("cells", []):
            parts = cell.split("/")
            stage = parts[1] if len(parts) > 1 else ""
            a(f"| `{cell}` | {STAGE.get(stage, 'domain specific requirement')} | **no** |")
        a("")
        a("## What already exists for it")
        a("")
        n = dom_count.get(did, 0)
        a(f"Corpus entries provisionally classified to this domain: **{n}**.")
        a("")
        a("Provisional means a keyword classifier put them here and no human has reviewed them. The number")
        a("is a hint about volume, not a coverage claim. The authoritative count appears only after the")
        a("domain is authored and each entry is enriched with atom, preconditions, oracle and driver.")
        a("")
        a("## Checklist to turn this from STUB to DEEP")
        a("")
        a("1. Harvest: at least three independent searches, one of them non-English or regional.")
        a("2. Enrich 50 or more entries, each with `atom`, `preconditions`, `oracle`, `evades`, `detected_by`.")
        a("3. Add a `driver` for every entry that is executable: install channel, verify command, json output.")
        a("4. Write the decision tree for the domain, as JSON in `trees/`, traversable by an agent.")
        a("5. Fill the defense mirror at one row per offensive entry, or record why not.")
        a("6. Record every empty required cell above as a gap with a build candidate.")
        a("7. Run the link checker over the new URLs, and stamp `last_verified`.")
        a("8. Render from JSON. Do not hand-write the markdown.")
        a("")
        a("---")
        a("")
        a(f"_Generated from `data/domain-registry.json` by `scripts/render-stubs.py`. "
          f"Regenerate rather than edit._")
        path.write_text("\n".join(L) + "\n")
        made += 1

    stubs = sum(1 for d in REG["domains"] if d["id"] not in authored)
    print(f"rendered {made} stubs")
    print(f"registry {len(REG['domains'])} domains: {len(authored)} authored, {stubs} stub")


if __name__ == "__main__":
    main()
