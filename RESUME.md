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

Then read `RECHECK.md` sections 3, 6 and 11, which list the instructions given, the things not done, and
the questions still open. Do not trust a remembered number over the output of that script.

## The one sentence version

Two repos. `ai-web-arsenal` holds tools, domains, corpus and install. `web-attack-atlas` holds atoms,
patterns, preconditions, oracles and counters. Join key is `entry_id`. Neither restates the other.
