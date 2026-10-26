# ai-web-arsenal

An AI-native arsenal for testing web platforms. Capture first, reverse the artifacts, derive hypotheses
from the actual stack, then prove with an oracle and a negative control.

Two repos, one seam:

| | this repo | [`web-attack-atlas`](../web-attack-atlas) |
|---|---|---|
| owns | tools, install, drivers, MCP wiring, REA, corpus, reconciliation | atoms, patterns, preconditions, oracles, chains, counters |
| answers | what do I run, and how | what do I think, what do I try, what will stop me |
| join key | `entry_id` | `entry_id` |

Tools die every 18 months. Techniques survive decades. Separating them means the durable half does not
rot with the disposable half.

---

## Status, measured from disk on 2026-10-26

| metric | value | meaning |
|---|---|---|
| corpus entries | **24,759** | canonical, deduplicated across every source |
| sources reconciled | **19** | awesome-lists, API lists, AI-security lists, MCP lists |
| rows reconciled | **31,298** | `admitted 16,956 + excluded 14,127 + held 212 + residue 3` |
| reconciliation identity | **holds** | checked per source and in aggregate |
| tools in manifest | **64** | every install candidate verified against a real channel |
| unresolved installs | **0** | nothing invented, nothing guessed |
| prompt packs | **5** | phase-shaped, with failure modes and verification |
| domains | **37** | 28 authored (389 enriched entries), 9 explicit pointers, 0 empty |
| patterns in the atlas | **150** | W01 lifecycle, W02 authorisation, W03 second-order, gate passing |
| taxonomy items mapped | **624 of 706** | WSTG, ASVS, VRT, API Top 10, ATLAS, LLM Top 10 to atoms, 88.4% |

These numbers are produced by `scripts/readme-stats.py`. If this table and that script disagree, the
script is right.

---

## Quickstart

```bash
git clone <this repo>
cd ai-web-arsenal
bash bootstrap/00-prereqs.sh
bash bootstrap/15-install-minimal.sh   # 13 tools
bash bootstrap/90-verify.sh            # proves every binary runs
```

Dry run first: `DRY=1 bash bootstrap/15-install-minimal.sh`

Then wire the extraction spine and read `BOOTSTRAP.md`. Arch first, every tool carries a
distro-neutral fallback.

---

## The method, in order

```
capture -> inventory -> reverse artifacts -> hypotheses -> test -> prove -> critic
```

| step | what you do | pack |
|---|---|---|
| capture | one browsing pass through a proxy, no probing | |
| inventory | endpoints, auth requirement, UI-reachable or not | [`prompts/01-recon-capture.md`](prompts/01-recon-capture.md) |
| reverse | bundle graph, routes, auth logic, secret candidates | [`prompts/02-bundle-teardown.md`](prompts/02-bundle-teardown.md) |
| hypothesise | derive from the stack, rank by cost to test | [`prompts/03-hypothesis.md`](prompts/03-hypothesis.md) |
| prove | oracle plus negative control, or it is not a finding | [`prompts/04-prove-it.md`](prompts/04-prove-it.md) |
| critic | a second agent whose job is to break the first one | [`prompts/05-critic.md`](prompts/05-critic.md) |

Step 7 is the one that fixes AI pentesting. A single agent that both finds and confirms will confirm its
own hallucinations. A critic that is rewarded for REFUTED does not.

---

## What is in here

| path | what it is |
|---|---|
| `SCOPE-v1.md` | the superset derivation: 11 axes, cell model, REA spine, rival protocol |
| `BOOTSTRAP.md` | bring-your-own-AI setup, Arch first, MCP wiring |
| `manifest/tools.yaml` | single source of truth for every tool: install, verify, driver, profiles |
| `bootstrap/` | generated install scripts, one per profile, dry-run safe |
| `data/corpus.jsonl` | the full union, every entry accounted for |
| `data/reconcile/` | per-source disposition ledger with reason codes |
| `data/install-matrix.json` | verified availability, with the channel that resolved |
| `data/domains/D11.json` | the domain template: atoms, cells, tree, mirror, gaps |
| `domains/D11-api-protocols.md` | rendered from the JSON, never hand written |
| `prompts/` | five phase packs with failure modes and verification steps |
| `mcps/` | MCP configs, with the rule that a server is listed only with a working config |
| `skills/web-arsenal/` | an agent skill that encodes the order of operations |
| `trees/` | decision trees as JSON, so an agent can traverse them |
| `docs/TAXONOMY-COVERAGE.md` | every taxonomy test ID mapped to an atom, with the unmapped list printed |
| `domains/` | 37 files: 28 authored with trees, mirror and gaps, 9 pointers naming the artefact that implements them |
| `RESUME.md` | how to continue: state, rebuild commands, traps already hit |
| `LOG.md` | every step, every error, including the facts I got wrong |

---

## Coverage honesty

The corpus accounts for everything. It does not claim to be curated.

- **admitted 16,956 rows**: in scope, includes entries flagged as unreviewed tail
- **excluded 14,127 rows**: taxonomy nodes (12,009), social and video (930), out of scope (556),
  knowledge not tooling (329), non-security MCP servers (303)
- **held 212 rows**: rules could not decide, quarantined with examples, not deleted

The `admitted` number counts rows, so it double-counts entries that appear in several sources. The unique
count is 24,759. Both are reported because collapsing them would hide which one is being claimed.

A rival entry is never silently dropped. That is the entire point of the ledger.

---

## Design rules

- Every entry carries a source, a status and a date. No claim without provenance.
- Counts are recomputed from disk before being quoted, never recalled.
- An install candidate is a hypothesis until a verifier resolves it against a real channel.
- Two independent engines for any claim that matters.
- The markdown is generated from JSON. Hand-edited docs drift, generated ones cannot.
- No API keys, tokens or credentials are shipped. Bring your own AI.

---

## How the defence mirror actually works

Every domain carries a `mirror`: rows of `attack | detect | control | rule`. These describe attack
**classes**, not individual tools, and the repo does not claim a 1:1 mapping between an entry and a
detection row.

An attempt was made on 2026-10-27 to auto-link each entry to a mirror row by lexical similarity. It
produced 14 percent on one scoring method and 26 percent on another, and both numbers were artifacts of
the scoring rather than measurements of the mirror. A row describes a class; an entry's relation to a
class is semantic, and lexical overlap cannot recover it. The experiment was reverted and the script
deleted rather than tuned until it produced a number worth quoting.

What is actually true: **28 of 28 authored domains carry a mirror.** Per-entry `detected_by` breaks
down as 22 hand authored, 113 auto-linked and flagged `mirror_provisional` (lexical match, treat
as a hint not a claim), and 254 deliberately empty. A tool does not need its own detection; the class
it implements does.

## The real backlog, measured properly

An earlier version of this repo quoted **10,476 indexed, not enriched**. That number was produced by a
keyword matcher that matched the word `server` against all 8,183 rows of an MCP server directory, and
pulled in badge SVGs, book listings and cheat sheets. It was a measure of matcher noise, not a backlog.

Rebuilt on 2026-10-27 with rules that match on name and description only, require domain specific terms,
and exclude directory, book and social URLs at generation:

| | count |
|---|---|
| enriched entries in authored domains | **389** |
| genuinely promotable candidates | **1491** |
| ratio | 21% of the real candidate set is enriched |

So the gap is about 3.8x, not 27x. Still a lot of work, but a number that survives inspection.
The generator is `scripts/build-indexes.py`; the counts are re-derived on every run.

## Why the corpus matters more than it looks

Of 24,759 canonical entries, only **548 appear in two or more source collections**. The awesome-lists
are nearly disjoint. No single list is a superset of any other, which is why a union plus an exclusion
ledger is the only way to claim coverage honestly, and why every previous attempt to be "the complete
one" failed by inheriting one list's blind spots.

---

## Boundary

Tooling and methodology for authorised security testing. Every technique class carries its authorisation
requirement. Use on systems you own or have written permission to test. Unauthorised testing is illegal
and this repo does not help with it.

---

_Counts regenerated by `python3 scripts/readme-stats.py`. Reconciliation by `scripts/reconcile.py`.
Install matrix by `scripts/verify-tools.py`. Nothing in this file is typed from memory._
