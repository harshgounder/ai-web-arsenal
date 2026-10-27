# RESUME

This file is a pointer. It used to be a second copy of the project state, and it drifted from the first
copy, so the state now lives in exactly one place.

| you want | read |
|---|---|
| what is true right now, what is done, what is not, what to do next | **`RECHECK.md`** |
| how to add a domain, run order, traps already hit | **`AUTHORING.md`** |
| the plan: denominator, lenses, phases, gates | **`PLAN.md`** |
| why the repo is shaped this way | `SCOPE-v1.md` |
| setup, install, first run | `BOOTSTRAP.md` |
| the history of decisions and mistakes | `LOG.md` |

## After a context compaction

```bash
cd ~/ai-web-arsenal
python3 scripts/recheck.py
```

Then read `RECHECK.md` sections 3, 6 and 8. Section 3 lists the instructions given, section 6 is the record
of each phase with subsections 6b through 6v covering the build in order, and section 8 is the defect
ledger: things this project asserted and had to correct. Do not trust a remembered number over the output
of that script, and do not trust a remembered mechanic over `scripts/check-claims.py`.

## The one sentence version

Two repos. `ai-web-arsenal` holds tools, domains, corpus and install. `web-attack-atlas` holds atoms,
patterns, preconditions, oracles and counters. Neither restates the other.

The join is at **wave granularity, not pattern granularity**, and that is measured rather than intended:
8 of 562 entries point into the atlas, one at a wave's `patterns.jsonl` and six at `QUEUE.json`, which
lists waves that are not built. Zero entries reference a pattern id. Earlier versions of README, AUTHORING
and this file all said the join key was `entry_id`, which described an interface nothing used. `C120` pins
the figure so it cannot drift back into prose unnoticed.
