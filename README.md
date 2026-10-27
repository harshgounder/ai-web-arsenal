# ai-web-arsenal

<p align="center">
  <b>An AI-native arsenal for testing web platforms.</b><br/>
  Capture first. Reverse the artifacts. Derive hypotheses from the actual stack.<br/>
  Then prove it with an oracle and a negative control.
</p>

<p align="center">
  <a href="#quickstart"><img alt="quickstart" src="https://img.shields.io/badge/quickstart-2%20commands-2ea44f?style=flat-square"/></a>
  <img alt="platform" src="https://img.shields.io/badge/platform-Arch%20%7C%20CachyOS-1793d1?style=flat-square"/>
  <img alt="tools" src="https://img.shields.io/badge/tools-64%20verified%2C%200%20unresolved-blue?style=flat-square"/>
  <img alt="domains" src="https://img.shields.io/badge/domains-28%20authored%20%2B%209%20pointers-8a2be2?style=flat-square"/>
  <img alt="entries" src="https://img.shields.io/badge/enriched%20entries-444-orange?style=flat-square"/>
  <img alt="license" src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square"/>
</p>

<p align="center">
  <a href="#what-this-is-precisely">What this is</a> ·
  <a href="#quickstart">Quickstart</a> ·
  <a href="#the-method">The method</a> ·
  <a href="#domain-coverage">Domains</a> ·
  <a href="#measured-bounds">Bounds</a> ·
  <a href="#companion-repo">Companion repo</a> ·
  <a href="#contributing">Contributing</a>
</p>

---

## What this is, precisely

**It is the deduplicated superset of what 19 public collections knew as of October 2026, plus 28 authored domains of method, mapped onto 16 primitives.**

**It is not the set of everything that exists.** Three things bound it, and all three are measured rather than estimated:

| bound | number | measured by |
|---|---|---|
| the corpus is what 19 lists knew | **21,194** tool identities | `scripts/merge-identities.py` |
| the authored content is what this build produced | **444** enriched entries | `data/domains/*.json` |
| the backlog is real and mapped | **1,419** promotable candidates | `data/domains/*.index.json` |

A repo that claims completeness is making a claim it cannot check. This one publishes its own shortfall as a table, and every number in this file is regenerated from disk before it is quoted.

---

## Why it exists

Every web security list on GitHub fails the same way. Sorted by vulnerability class. No dates. No evidence standard. No driver information, so an agent cannot act on a row. And links that rot silently while the README implies completeness.

The collections this repo reconciled are near disjoint. Of 21,194 tool identities, only a few hundred appear in more than one collection. No single list is a superset of any other, which is why a union plus an exclusion ledger is the only honest way to claim coverage.

This repo answers three questions that a list cannot:

1. **What do I run, and how?** Every tool carries an install channel resolved against a real package manager, a verify command, a JSON output flag, and a one line agent usage note.
2. **What do I think, and in what order?** Every domain carries a machine readable decision tree.
3. **What will stop me, and what proves it?** Every domain carries a defence mirror, and every atlas pattern carries a counter.

---

## Quickstart

Two commands to a working toolkit on Arch, CachyOS, EndeavourOS or Manjaro.

```bash
git clone https://github.com/harshgounder/ai-web-arsenal.git
cd ai-web-arsenal
bash bootstrap/00-prereqs.sh          # base-devel, git, AUR helper, uv
bash bootstrap/15-install-minimal.sh  # 13 tools
bash bootstrap/90-verify.sh           # proves every binary runs
```

Dry run first, if you prefer to see what it does:

```bash
DRY=1 bash bootstrap/15-install-minimal.sh
```

The installer refuses to run as root, never pipes curl to sh, and is idempotent. Every run logs to `bootstrap/logs/`.

Then wire the extraction spine and follow [`BOOTSTRAP.md`](BOOTSTRAP.md) for the full bring-your-own-AI setup.

### Profiles

| profile | script | tools | for |
|---|---|---|---|
| minimal | `15-install-minimal.sh` | 13 | start today |
| recon | `20-install-recon.sh` | 12 | surface mapping |
| web | `25-install-web.sh` | 19 | requests, fuzzing, browser |
| api | `30-install-api.sh` | 15 | REST, GraphQL, gRPC, spec recovery |
| ai-agent | `35-install-ai-agent.sh` | 7 | LLM and agent security |
| mobile | `40-install-mobile.sh` | 3 | the client behind the web app |
| re | `45-install-re.sh` | 4 | REA spine and binaries |
| all | `50-install-all.sh` | 64 | everything |

Counts are written by the generator. If a count and a script disagree, the count is wrong.

---

## The method

```
capture -> inventory -> reverse artifacts -> hypotheses -> test -> prove -> critic
```

| step | what you do | pack |
|---|---|---|
| capture | one browsing pass through a proxy. no probing | |
| inventory | endpoints, auth requirement, UI reachable or not | [`prompts/01-recon-capture.md`](prompts/01-recon-capture.md) |
| reverse | bundle graph, routes, auth logic, secret candidates | [`prompts/02-bundle-teardown.md`](prompts/02-bundle-teardown.md) |
| hypothesise | derive from the stack, rank by cost to test | [`prompts/03-hypothesis.md`](prompts/03-hypothesis.md) |
| prove | oracle plus negative control, or it is not a finding | [`prompts/04-prove-it.md`](prompts/04-prove-it.md) |
| critic | a second agent whose job is to break the first one | [`prompts/05-critic.md`](prompts/05-critic.md) |

Step seven is the one that fixes AI pentesting. A single agent that both finds and confirms will confirm its own hallucinations. [`docs/ORCHESTRATION.md`](docs/ORCHESTRATION.md) states the rule and the handoff contract.

---

## Repository map

```
ai-web-arsenal/
├── README.md                  you are here
├── SCOPE-v1.md                the superset derivation: 11 axes, cell model
├── BOOTSTRAP.md               bring-your-own-AI setup, Arch first
├── RESUME.md                  state, rebuild commands, traps already paid for
├── LOG.md                     every step, including the eight defects
├── manifest/tools.yaml        single source of truth for 64 tools
├── bootstrap/                 11 generated installer scripts
├── data/
│   ├── corpus.jsonl           the union, every entry accounted for
│   ├── reconcile/             per-source disposition ledger and summary
│   ├── taxonomy/              6 taxonomies parsed to test IDs
│   ├── install-matrix.json    verified availability per tool
│   └── domains/D*.json        the machine readable source of every domain
├── domains/                   37 domain documents, 28 authored, 9 pointers
├── trees/                     decision trees as JSON
├── prompts/                   5 phase packs with failure modes
├── mcps/                      working MCP configs
├── skills/web-arsenal/        the order of operations as a loadable skill
├── docs/                      taxonomy coverage, link health, orchestration
└── scripts/                   13 reproducible pipeline stages
```

---

## Domain coverage

28 domains are authored. Each carries entries with atom, preconditions, oracle, driver and defence mapping, plus a decision tree and a mirror.

| id | domain | entries | tree | mirror |
|---|---|---|---|---|
| D02 | Recon and surface mapping | 29 | 3 | 5 |
| D03 | Fingerprinting and stack identification | 11 | 4 | 3 |
| D04 | Authentication and identity providers | 21 | 3 | 7 |
| D05 | Authorization, tenancy, field-level access | 20 | 3 | 7 |
| D06 | Session, token, cookie, key material | 13 | 4 | 5 |
| D07 | Injection family | 22 | 6 | 7 |
| D08 | Client-side and browser trust boundaries | 13 | 5 | 5 |
| D09 | HTTP semantics, smuggling, desync | 11 | 3 | 4 |
| D10 | Cache, CDN, edge behaviour | 6 | 4 | 3 |
| D11 | API protocols: REST, GraphQL, gRPC, WebSocket | 37 | 2 | 8 |
| D12 | Business logic, races, money paths | 8 | 4 | 5 |
| D13 | File handling, upload, path, archive | 12 | 5 | 5 |
| D14 | Server-side request and fetch (SSRF) | 10 | 4 | 5 |
| D15 | Deserialization and template engines | 10 | 5 | 4 |
| D16 | Cryptography, secrets, signing | 10 | 5 | 5 |
| D17 | Cloud and control plane | 15 | 4 | 5 |
| D18 | Supply chain and CI/CD | 10 | 4 | 5 |
| D19 | AI application attacks | 12 | 3 | 7 |
| D20 | Agent, MCP and skill attacks | 11 | 3 | 5 |
| D21 | Mobile app and webview bridge | 14 | 4 | 5 |
| D22 | WAF, bot and anti-automation evasion | 15 | 5 | 5 |
| D23 | Exploitation and chaining | 8 | 4 | 4 |
| D24 | Evidence, proof and reporting | 10 | 3 | 4 |
| D25 | Detection and defense mirror | 12 | 4 | 3 |
| D28 | MCP servers for web work | 8 | 4 | 4 |
| D29 | CLI tools an agent can drive | 60 | 3 | 3 |
| D30 | Agent frameworks and orchestrators | 13 | 4 | 4 |
| D31 | REA spine: target artifact extraction | 23 | 4 | 5 |

Nine further domains are **explicit pointers** rather than documents, because each is implemented as an artefact elsewhere in the repo and a second document would be a worse copy that drifts. For example D33 is `data/reconcile/`, D35 is `BOOTSTRAP.md`, D36 is the companion atlas ontology.

---

## What a row actually looks like

Every entry carries fields a list omits. This is D11's `clairvoyance` entry:

```json
{
  "name": "clairvoyance",
  "driver": { "install": "pipx:clairvoyance", "verify": "clairvoyance --help", "json": true },
  "atom": ["A01", "A08"],
  "preconditions": ["introspection disabled", "field suggestions enabled"],
  "oracle": ["schema_partial_recovery", "suggestion_error_differential"],
  "evades": ["F3"],
  "detected_by": ["field suggestion abuse pattern"],
  "procedure": [
    "confirm introspection is actually off with a direct query",
    "clairvoyance -o schema.json -w wordlist URL/graphql",
    "compare recovered fields to what the UI calls, the gap is the unauthorised surface"
  ]
}
```

The `procedure` field is what makes a row executable instead of descriptive. All 37 D11 entries have one.

---

## Measured bounds

Run `python3 scripts/readme-stats.py` to reproduce every number in this file.

| metric | value |
|---|---|
| sources reconciled | 19 |
| rows reconciled | 31,298 |
| reconciliation identity | holds, per source and in aggregate |
| corpus, by tool identity | 21,194 |
| corpus, by URL | 21,397 |
| excluded with a reason | 17,516 |
| held, awaiting a rule | 204 |
| taxonomy items mapped to atoms | 624 of 706 (88.4%) |
| tools verified | 64, 0 unresolved |
| domain URLs checked | 265, 264 live |
| atlas patterns | 150, gate passing |

Nothing was silently dropped. Every excluded row carries one of: `TAXONOMY_NODE`, `SOCIAL_OR_VIDEO`, `OUT_OF_SCOPE_NONWEB`, `KNOWLEDGE_NOT_TOOL`, `MCP_NON_SECURITY`, `IMAGE_NOT_ENTRY`, `UNCLASSIFIED_LOW_SIGNAL`.

---

## Companion repo

| | this repo | [web-attack-atlas](https://github.com/harshgounder/web-attack-atlas) |
|---|---|---|
| owns | tools, install, drivers, MCP wiring, REA, corpus, reconciliation | atoms, patterns, preconditions, oracles, chains, counters |
| answers | what do I run, and how | what do I think, what do I try, what will stop me |
| join key | `entry_id` | `entry_id` |

Tools die every 18 months. Techniques survive decades. Separating them means the durable half does not rot with the disposable half.

---

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md). The short version: an entry without a driver, a precondition and an oracle is a note, not an entry. Numbers are regenerated, never typed.

## Security

Read [SECURITY.md](SECURITY.md) before running anything from this repo. It is methodology and tooling for testing systems you own or are authorised to test.

## License

[MIT](LICENSE). Use it on systems you own or have written permission to test. Unauthorised testing is illegal and this repo does not help with it.

<p align="center"><sub>Every count in this file is regenerated from disk. If a number here disagrees with <code>scripts/readme-stats.py</code>, the script is right.</sub></p>
