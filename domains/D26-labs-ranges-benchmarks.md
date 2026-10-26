# D26: labs, ranges, benchmarks

Status: **POINTER**. This domain is implemented as an artefact elsewhere in the repo, not as a
document here. A second document would be a worse copy that drifts.

**Implemented at:** `D05, D11, D12 and the atlas X06 gaps`

**Why not here:** labs are distributed per domain, not centralised, because a lab without its domain context is useless

## What this domain covers

Surfaces: `all` cross-cutting

Expected primitives: none directly, this domain is a cross-cutting or infrastructure layer.

## Required cells, declared now

A cell is `surface / lifecycle stage / agency level`. Each is required only if a practitioner
would want something there, and the reason is reviewable. Nothing in this domain may ship
without filling these or recording why one is impossible.

| cell | why it is required | filled |
|---|---|---|
| `all/L06/A3` | probing needs an oracle, not a guess | **no** |
| `all/L08/A5` | proof with a negative control is what separates a finding from a note | **no** |

## What already exists for it

Corpus entries provisionally classified to this domain: **212**.

Provisional means a keyword classifier put them here and no human has reviewed them. The number
is a hint about volume, not a coverage claim. The authoritative count appears only after the
domain is authored and each entry is enriched with atom, preconditions, oracle and driver.

## Checklist to turn this from STUB to DEEP

1. Harvest: at least three independent searches, one of them non-English or regional.
2. Enrich 50 or more entries, each with `atom`, `preconditions`, `oracle`, `evades`, `detected_by`.
3. Add a `driver` for every entry that is executable: install channel, verify command, json output.
4. Write the decision tree for the domain, as JSON in `trees/`, traversable by an agent.
5. Fill the defense mirror at one row per offensive entry, or record why not.
6. Record every empty required cell above as a gap with a build candidate.
7. Run the link checker over the new URLs, and stamp `last_verified`.
8. Render from JSON. Do not hand-write the markdown.

---

_Generated from `data/domain-registry.json` by `scripts/render-stubs.py`. Regenerate rather than edit._
