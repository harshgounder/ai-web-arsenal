# RESUME: how to continue this repo

Everything below was verified by running it on 2026-10-26. No step here depends on chat history.

---

## What is done

| layer | state |
|---|---|
| scope derivation | `SCOPE-v1.md`, 11 axes, cell model, 37 domains declared |
| rival reconciliation | 19 collections, 31,298 rows, identity holds, exclusions itemised |
| taxonomy mapping | 706 items from 6 taxonomies, 624 mapped to atoms (88.4%) |
| tool manifest | 57 tools, every install candidate resolved against a real channel, 0 unresolved |
| bootstrap | 8 profiles generated from the matrix, dry-run safe, syntax clean |
| domains | 6 authored (D04, D05, D11, D19, D20, D31), 31 stubs with declared required cells |
| AI-native layer | 5 prompt packs, 1 skill, MCP configs, orchestration doc, decision trees |
| dated evidence | every entry stamped, 298 core links actually fetched, 3.0% problems |
| corpus | 24,759 canonical entries from 19 sources plus 3 own collections |

## What is not done

- 31 domains are stubs. Each declares its required cells and its live corpus count. None has content.
- 12,749 entries are `HARVESTED`: seen in a source, never independently checked. Only the `core_web`
  tier has been link checked.
- The REA extraction gaps in D31 are named and unbuilt (10 of them).
- The atlas (`web-attack-atlas`) has 3 of 23 waves done.

## Rebuild from scratch

Every artefact is generated. This sequence reproduces the repo from the raw harvests:

```bash
bash scripts/harvest-rivals.sh          # clones 19 collections into raw/rivals (ignored by git)
python3 scripts/parse-sources.py        # -> data/entries/*.jsonl
python3 scripts/build-corpus.py         # -> data/corpus.jsonl, data/corpus-stats.json
python3 scripts/reconcile.py            # -> data/reconcile/*.json, SUMMARY.json
python3 scripts/taxonomy-reconcile.py   # -> data/taxonomy/*.json, taxonomy-coverage.json
python3 scripts/verify-tools.py         # -> data/install-matrix.json
python3 scripts/gen-bootstrap.py        # -> bootstrap/*.sh
python3 scripts/render-domain.py --all  # -> domains/*.md for authored domains
python3 scripts/render-stubs.py         # -> domains/*.md for stub domains
python3 scripts/stamp-and-check.py --check core_web --limit 400
python3 scripts/readme-stats.py         # the numbers in README
```

Verified 2026-10-26: the first nine stages reproduce the same counts. `raw/` is not committed, so a fresh
clone must run `harvest-rivals.sh` and `harvest-taxonomy` before the parse stage.

## How to author the next domain

The D11 and D05 files are the two references. Pick one and copy its shape.

1. Add `data/domains/DXX.json` with: `atoms`, `atom_notes`, `required_cells` (with a `why` per cell),
   `entries`, `tree`, `mirror`, `gaps`.
2. Every entry needs `atom`, `preconditions`, `oracle`, `evades`, `detected_by`, and a `driver` with
   install channel, verify command and whether it emits JSON.
3. If the technique depth exists in the atlas, **link to it, do not restate it** (see `d05-atlas-w02`).
4. Run `python3 scripts/render-domain.py DXX`. Never hand-write the markdown.
5. Generate its index: see the inline pattern at the bottom of this file.
6. Set `status` to `DEEP` in `data/domain-registry.json`.
7. Run the link checker over the new URLs and commit the stamped result.

### The index snippet

```python
import json, re
d = json.load(open(f"data/domains/{did}.json"))
E = [json.loads(l) for l in open("data/corpus.jsonl")]
rx = re.compile(PATTERN, re.I)
enr = {(e.get("url") or "").rstrip("/").lower() for e in d["entries"] if e.get("url")}
idx = [e for e in E if e["kind"] in ("tool","knowledge")
       and rx.search(" ".join([e["name"] or "", e["desc"] or "", " ".join(e["sections"])]))
       and (e.get("url") or "").rstrip("/").lower() not in enr]
idx.sort(key=lambda e: (-e["n_sources"], e["name"] or ""))
json.dump({"domain": did, "enriched": len(d["entries"]), "indexed_not_enriched": len(idx),
           "entries": [{"name": e["name"], "url": e["url"], "tier": e["tier"],
                        "n_sources": e["n_sources"], "status": "INDEXED_NOT_ENRICHED"} for e in idx]},
          open(f"data/domains/{did}.index.json", "w"), indent=1)
```

## Traps already hit, so do not hit them again

1. **AUR `httpx` is the python library**, not ProjectDiscovery. Use `httpx-bin`. Same class of trap:
   `apktool` is `android-apktool`, `kiterunner` is `kiterunner-bin`, PyPI `promptfoo` is a 0.2.0
   placeholder while npm has the real one.
2. **`HEAD` lies.** Several real sites answer `HEAD` 404 and `GET` 200. Link check with `GET`, a browser
   UA, and follow redirects. A dead link claim costs more than the check.
3. **VRT leaves are qualifiers**, not tests. "Long Timeout" only means something with its parent path.
   Match on the full path or lose 40 coverage points.
4. **"ASVS 240" is a file count.** It is not 240 requirements. Do not repeat it.
5. **A classifier fallback is a silent claim.** When `classify()` returned `C02` for unmatched counters,
   every unrecognised control became "authorisation" and produced a fake finding. Unmatched must have
   its own bucket.
6. **Corpus keyword matching is polluted.** `glama.ai` MCP directory pages and `bugreader` writeups
   dominate some keyword sets. Author domains deliberately; publish the skipped count in
   `DXX.index.json` rather than padding the table.

## Run order matters

`normalize-atoms.py` must run before `validate-domains.py`. Atoms written as a string were shipped
three separate times (D02, D03, D24) because the value was passed where a list was expected. It
renders as garbage, throws nothing, and is only caught by validation. The normaliser repairs it
idempotently so the class of bug cannot persist.

## The rule that decides quality here

An entry without `preconditions`, `oracle` and a `counter` is a note, not an entry. If a domain document
can be produced by importing a keyword set, it will be worthless. The value is entirely in those three
fields, and they cannot be generated.

## Where the technique layer lives

`~/web-attack-atlas`. Join key is `entry_id`. That repo owns atoms, patterns, preconditions, oracles,
chains and control classes. This repo owns tools, install, drivers and the corpus. Never restate a
pattern here.
