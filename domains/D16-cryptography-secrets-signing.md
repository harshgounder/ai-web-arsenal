# D16: cryptography, secrets, signing

Status: **STUB**. The shape is declared, the content is not written yet. This is stated at the
top rather than discovered by reading.

## What this domain covers

Surfaces: `S04` identity and session

Expected primitives: `A09` cryptographic weakness, `A08` information exposure

## Required cells, declared now

A cell is `surface / lifecycle stage / agency level`. Each is required only if a practitioner
would want something there, and the reason is reviewable. Nothing in this domain may ship
without filling these or recording why one is impossible.

| cell | why it is required | filled |
|---|---|---|
| `S04/L06/A2` | probing needs an oracle, not a guess | **no** |
| `S04/L07/A2` | exploitation and chaining is the step everything else serves | **no** |
| `S04/L11/A2` | fix verification is the least covered stage in the industry | **no** |

## What already exists for it

Corpus entries provisionally classified to this domain: **134**.

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
