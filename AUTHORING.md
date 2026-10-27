# AUTHORING

How to add to this repo without breaking it. State lives in `RECHECK.md`. This file is method.

Everything here was learned by breaking it first. The traps section is a list of failures, not advice.

---

## Adding a domain

`data/domains/D11.json` and `D05.json` are the two references. Pick the closer shape and copy it.

1. Write `data/domains/DXX.json` with `atoms`, `atom_notes`, `required_cells` (each cell carries a
   `why`), `entries`, `tree`, `mirror`, `gaps`.
2. Every entry needs `atom`, `preconditions`, `oracle`, `evades`, `detected_by`, and a `driver` with
   install channel, verify command, and whether it emits JSON. An entry missing `preconditions`,
   `oracle` or a counter is a note, not an entry.
3. If the technique already exists in the atlas, link to it by `entry_id`. Never restate a pattern here.
   The atlas owns atoms, patterns, preconditions, oracles, chains and control classes. This repo owns
   tools, install, drivers and the corpus.
4. Render the markdown with `python3 scripts/render-domain.py DXX`. Never hand-write the generated file.
5. Generate the index with `python3 scripts/build-indexes.py`, then `python3 scripts/dedupe-names.py`.
   Do not reimplement the matcher inline. An earlier version of this file published a snippet, it drifted
   from the script, and it is exactly how two counting bugs started.
6. Set `status` to `DEEP` in `data/domain-registry.json`.
7. Run the link checker over the new URLs and commit the stamped result.

## Run order

Some stages are order dependent. Running them out of order silently discards work.

```
parse-sources -> build-corpus -> reconcile -> taxonomy-reconcile -> merge-identities
  -> verify-tools -> gen-bootstrap -> normalize-atoms -> render-domain --all
  -> render-stubs -> build-indexes -> dedupe-names -> validate-domains -> readme-stats
```

- `normalize-atoms.py` **must** run before `validate-domains.py`. Atoms written as a string were shipped
  three separate times (D02, D03, D24) because a value was passed where a list was expected. It renders
  as garbage, throws nothing, and only validation catches it.
- Name repair lives **inside** `build-corpus.py`, not after it. A separate repair script ran after its
  own generator and every repair was discarded on the next build.
- `build-indexes.py` reports the count **before** cross-domain dedupe. `dedupe-names.py` is the final
  word. The published figure is the one after dedupe.

## Traps already hit

Each of these was a real failure that produced a plausible wrong answer.

1. **AUR `httpx` is the Python library**, not ProjectDiscovery. Use `httpx-bin`. Same class:
   `apktool` is `android-apktool`, `kiterunner` is `kiterunner-bin`, PyPI `promptfoo` is a 0.2.0
   placeholder while npm has the real one.
2. **`HEAD` lies.** Several real sites answer HEAD 404 and GET 200. Link check with GET, a browser UA,
   and follow redirects. A false dead-link claim costs more than the check saves.
3. **VRT leaves are qualifiers**, not tests. "Long Timeout" only means something with its parent path.
   Match the full path or lose coverage points.
4. **"ASVS 240" is a file count.** Not 240 requirements. Do not repeat it.
5. **A classifier fallback is a silent claim.** When `classify()` returned `C02` for unmatched counters,
   every unrecognised control became "authorisation" and produced a fake finding. Unmatched must have
   its own bucket, and it must be reported separately.
6. **Corpus keyword matching is polluted** by directory pages and writeups. Author domains deliberately
   and publish the skipped count instead of padding a table.
7. **A row is not a tool.** The corpus holds tools, taxonomy nodes, social rows and knowledge rows. Only
   `kind: tool` counts as a tool. Quoting the row total as a tool count overstated tools by 2.4x once.
8. **A filter that matches one shape of a thing is a sample.** The image filter matched file extensions,
   so thirteen shields.io language badges shipped as tools. Match hosts and paths too, and check what a
   badge is hiding behind it before deleting it, because three real MCP servers were.
9. **A machine-wide lookup failure is not a missing package.** `pacman -Si` fails for every package when
   any configured repo has a bad signature. That reported sixteen packaged tools as unresolvable. Fall
   back to an independent source and record which one answered.
10. **An identifier is not a link.** Several hundred rows held `owner/repo` in their `url` field, so
    "rows with a URL" counted identifiers and the link checker could never reach them.

## The rule that decides quality here

The value of an entry is entirely in `preconditions`, `oracle` and `counter`. Those fields cannot be
generated, which is why the enriched count is small and the promotable count is large. If a domain
document could be produced by importing a keyword set, it would be worthless.

**Measured 2026-10-27, the rule is not met across the corpus.** Of 444 entries: 335 declare
preconditions (75 percent), 346 declare an oracle (78), 175 declare evades (39), and 135 declare what
detects them (30). Seven entries are deliberate pointers into the atlas and carry none of these by
design, because they join on `entry_id` rather than restating a pattern. The remaining shortfall is
real work, tracked in `RECHECK.md` and checked by `C053` to `C053d`. A new entry should satisfy the rule
even though the existing corpus does not, and the ratio should move up, not stay flat.

## Grading coverage

A coverage record says how far an artefact goes for one factor. The levels are strict on purpose:

```
L0 absent      nothing addresses the factor
L1 named       a tool or entry mentions the concept, with no procedure and no oracle
L2 procedure   a procedure and an oracle, so a competent reader could test it
L3 observed    a lab here demonstrates it
```

L2 means the cited entry states a procedure for **that factor**, not that it touches the same area. The
difference is the whole value of the number, and it erodes quietly: this project mapped 63 factors in one
pass, then pulled 22 of them back to L1 because the cited entries were adjacent rather than operative.

So check it, with a command rather than a resolution:

```bash
python3 scripts/coverage.py --sample 10 --seed 3
```

That prints ten random graded records next to the role of the entry each cites. Judge whether the note is
a procedure for the factor as written. Anything adjacent is L1. Do this every few batches, and always
after one that moves the number by more than two points.

## Counting

A number that cannot be regenerated from disk is a memory. `scripts/readme-stats.py` emits every figure
that appears in a document, `scripts/recheck.py` compares those figures to what the documents claim, and
`scripts/check-claims.py` checks the prose claims that contain no numbers.

If a claim cannot be checked by a command, either make it checkable or do not make it.
