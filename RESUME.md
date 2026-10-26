# RESUME: how to continue this repo

Everything below was verified by running it on 2026-10-26. No step here depends on chat history.

---

## What is done, measured 2026-10-27

| layer | state |
|---|---|
| scope derivation | `SCOPE-v1.md`, 11 axes, cell model, 37 domains declared |
| rival reconciliation | 19 collections, 31,298 rows, identity holds, 17,516 exclusions itemised by reason |
| corpus | 21,194 tool identities (21,397 by URL, 203 collapsed as duplicates) |
| taxonomy mapping | 706 items from 6 taxonomies, 624 mapped to atoms (88.4%) |
| tool manifest | 64 tools, 0 unresolved, every channel verified |
| bootstrap | 11 scripts generated, 8 profiles, dry-run safe |
| domains | 28 authored, 9 explicit pointers, 0 empty, 444 enriched entries |
| AI-native layer | 5 prompt packs, 1 skill, MCP configs, orchestration doc, 28 decision trees |
| dated evidence | every entry stamped, 265 domain URLs checked (264 live), 298 corpus links |
| validator | passes on all 28 domain files |

## What is not done

- 1,419 promotable candidates remain unenriched. Measured, not guessed: see `data/domains/*.index.json`.
  The realistic yield is far lower than that number because the single-source tier is mostly
  single-author tools, dead projects and blog posts.
- 9 domains are explicit pointers rather than authored documents. Each names the artefact that
  implements it. Turning them into documents would duplicate existing files.
- The REA extraction gaps in D31 are named and unbuilt (10 of them).
- The atlas has 3 of 23 waves done.
- Per-entry `detected_by` is hand authored for 22 entries, provisional for 113, empty for 254. The
  mirror is per attack class, not per tool, and the README says so.

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


---

## Closing note, 2026-10-27

This project's recurring failure mode was a **plausible-looking artifact that nothing validated**.
Eight instances were caught, none by reading:

1. two recalled facts wrong (a repo called stale that was active, one called live that was archived)
2. link checker used HEAD, which real sites answer 404, producing 7 false dead links
3. classifier fallback turned every unmatched counter into "authorisation", inflating a finding to 31%
4. two repository URLs were invented and looked exactly like the 110 real ones
5. a mirror coverage metric was measuring its own scoring, giving 14% then 26% then 52%
6. the backlog was 10,476 until measured properly at 1,491
7. the corpus was 24,759 until image URLs were removed, giving 21,397
8. a name repair ran after its generator and was silently discarded, then the retry never matched

Every one was found by a measurement disagreeing with a claim. That is the method this repo is trying
to encode: if a number cannot be regenerated from disk, it is not a number, it is a memory.
