# RECHECK

**Read this first after any context compaction.** Then run:

```bash
python3 scripts/recheck.py
```

That script re-derives every number in this file from disk. If it reports `CHANGED`, either this doc is
stale or work advanced since it was written. Do not proceed until you know which.

Written 2026-10-27. Author: the same session that built everything below.

---

## 1. What exists

| path | remote | commits | tracked | state |
|---|---|---|---|---|
| `~/ai-web-arsenal` | github.com/harshgounder/ai-web-arsenal | 68 | 323 | pushed, clean |
| `~/web-attack-atlas` | github.com/harshgounder/web-attack-atlas | 12 | 25 | pushed, clean |
| `~/contest-opsec` | none | 0 | 0 | **PAUSED**, only `SCOPE.md` drafted |
| `~/operator-opsec` | none | 0 | 0 | **ABANDONED**, stale corporate-OPSEC drafts, safe to delete |

The contest repo was paused by the user: *"wait lets keep this on pause and make the other 2 repos of
ours first"*. Its format is understood (see section 9). Do not resume it without an explicit instruction.

`~/operator-opsec` contains the wrong version (corporate compliance framing). The user rejected it.
It was never committed, never pushed. `~/contest-opsec` is the correct successor and only has `SCOPE.md`.

---

## 2. The five original objectives and their status

| # | objective | status | evidence |
|---|---|---|---|
| 1 | scope expansion doc deriving the superset from first principles | **done** | `SCOPE-v1.md`: 11 axes, cell model, 37 domains |
| 2 | rival reconciliation, every entry included or in an exclusion ledger with reason | **done** | `data/reconcile/`: 19 sources, 31,298 rows, identity holds, 7 reason codes |
| 3 | layered repo: README hub + per-domain MD + machine-readable JSON | **done** | `README.md`, 37 files in `domains/`, 37 JSON in `data/domains/` |
| 4 | full AI-native layer: MCP specs, skills, prompts, orchestration, trees | **done** | `mcps/`, `skills/`, 5 `prompts/`, `docs/ORCHESTRATION.md`, 28 `trees/` |
| 5 | dated evidence per entry, web/API + adjacent, refreshed through Oct 2026 | **done** | every corpus row stamped; 323 domain URLs fetched 2026-10-27 |

Goal marked complete on round 40/40. **"Definitive" was not achieved and the README no longer claims it.**

---

## 3. Every instruction the user gave, with status

| # | instruction | delivered? |
|---|---|---|
| 1 | everything offensive + defensive, not only tools | partial. 28 domains, atlas has 13 control classes |
| 2 | everything that beats defensive tooling | partial. `counters/COUNTERS.md`, D25, D22 with F2-F7 mapping. class level, not per tool |
| 3 | beat the existing awesome-repos on completeness | yes on measurables (dates, links, ledger, drivers), **no on volume** |
| 4 | AI-native, for authorised professionals | yes |
| 5 | expand the scope FIRST | yes, `SCOPE-v1.md` was deliverable 1 |
| 6 | every AI cybersecurity company | **partial.** 460 vendors in `raw/vendors.json`, not reconciled into domains |
| 7 | latest as of Oct 26 2026, especially last 3-4 months | **partial.** ARTEX, pathrunner, STAR Fuzzer, RedAgents, Snyk Evo, Edgescan dated. no systematic Aug-Oct sweep |
| 8 | every forum, social and code host, incl Gitee, Codeberg, regional | **partial.** spot finds only (ARTEX, ThreatBook, wxapkg, Dark-Moon) |
| 9 | no single leaf unturned | **refused.** replaced with a bounded claim |
| 10 | every rival repo entry accounted for | **yes, strongest part.** identity holds |
| 11 | use REA and the extended `rea-expansion` version | partial. D31 authored with 21 real callable operations; 10 gaps named |
| 12 | write the missing REA operations as code | **NO. You chose this. Nothing built.** |
| 13 | bring-your-own-AI, Arch first, instant access | **yes.** 64 tools, 0 unresolved, 11 generated scripts, dry-run tested |
| 14 | include my byok-cyber-arsenal and web-universe-work | **yes.** both are `source_type: own` in the ledger |
| 15 | every attack method in history incl minute mutations | **reframed** into a grammar, then 150 patterns built |
| 16 | tens of thousands of ways | **NO.** 150 patterns, 444 entries |
| 17 | per language and per stack coverage | **NO.** domains are by attack surface, not by stack |
| 18 | counters to every defensive/recon tool opposite us | partial, class level |
| 19 | waves after waves of research | structure yes (23 queued), **3 of 23 built** |
| 20 | AI replicates elite human performance | defined as 5 tests in `ORCHESTRATION.md`, **never run, 0 OBSERVED** |
| 21 | separate repos for tools vs patterns | **yes** |
| 22 | get them on my GitHub, professional README/about/tags | **yes**, done late after being called out |
| 23 | plan the contest/OPSEC repo with me | **paused by user** |

---

## 4. Decisions the user made

| decision | value |
|---|---|
| scope edges | web/API + adjacent (cloud, mobile app, JS/native, auth/SSO) |
| repo shape | layered: hub + per-domain MD + machine-readable JSON |
| AI-native depth | full: agent configs, MCP specs, skills, prompt packs, orchestration |
| freshness | once, deeply, with dated evidence |
| name | `ai-web-arsenal` |
| depth | 10 domains deep, stubs for the rest |
| REA | entries + wrappers + **write the missing operations** |
| rivals | both 19 repos AND test-ID level taxonomies |
| bar | "50+ entries per domain, fewer domains overall" |
| focus | "change the internal data of a website, that side of focus" |
| sequencing | vertical slice first |
| held entries | admit unique-to-one-list as UNREVIEWED |

**Unmet user decisions, stated plainly: the 10 named REA gaps were not built into operations. The 50+ bar (19) was not met by any domain; highest is D11 at 37. 28 domains were built where the user said 10.**

---

## 5. What is actually done

```
corpus          21,384 rows, of which 8,848 are tools (8,692 identities); 9,671 carry a real URL (1 row holds an unparseable slug)
                the other rows: 11,712 taxonomy nodes, 577 social, 247 knowledge. 19 sources
reconcile       31,298 rows = 13,516 admitted + 17,506 excluded + 204 held + 71 orphan + 1 unresolved
                identity holds per source and in aggregate, every term named
taxonomy        624 of 706 test IDs mapped to 16 atoms (88.4%)
tools           64 in manifest, 0 unresolved, every channel verified live
bootstrap       11 generated scripts, 8 profiles, dry-run safe, syntax clean
domains         30 authored + 9 explicit pointers + 0 empty
enriched        515 entries, all with atom and driver; 406 with preconditions, 417 with oracle,
                175 with evades, 135 with detected_by. The mandatory-field rule is 76% met
trees           28 decision trees as JSON
atlas           150 patterns, gate passing, 13 control classes, 157 mutations
links           267 domain URLs checked, 266 answered (1 is w3.org refusing bots)
```

### Domain status

Authored (28): D02 D03 D04 D05 D06 D07 D08 D09 D10 D11 D12 D13 D14 D15 D16 D17 D18 D19 D20 D21 D22 D23
D24 D25 D28 D29 D30 D31.

Explicit pointers (9), each naming the artefact that implements it: D00 D01 D26 D27 D32 D33 D34 D35 D36.

Empty: **none**.

### Atlas waves

Done (3): W01 write primitives (50), W02 authorisation on writes (50), W03 second-order and deferred (50).
Queued (20): W04-W12, R01-R05, X01-X06.

---

## 6. What is NOT done

1. **REA missing operations.** LevelDB reader, wxapkg unpack, Flutter AOT, Hermes, HARMony HAP, WARC,
   service worker, WebAuthn attestation, signing recovery, source map recovery. Named in D31 gaps, unbuilt.
2. **20 atlas waves.** ~1,000 patterns if the bar stays at 50.
3. **1,419 promotable candidates** unenriched. Realistic yield far lower; the single-source tier is not
   mineable by keyword.
4. **0 OBSERVED patterns.** Every atlas claim is ESTABLISHED. Nothing was lab tested.
5. **4 domains have empty L11 retest cells** (D11, D17, D21, D25 + others).
6. **Per-entry defence mapping is thin:** 22 hand authored, 113 provisional lexical, 254 empty.
7. **No stack playbooks.** The original complaint ("what do I do on a Next.js app with Clerk auth") is
   still unanswered.
8. **No corpus MCP server.** The corpus is JSON nobody can query.
9. **No range/lab repo.** This is what would convert ESTABLISHED into OBSERVED.
10. **Contest repo paused**, scope drafted only.

---

## 6b. Phase 0 status (the truth layer)

Started 2026-10-27, after PLAN.md was approved.

| item | state |
|---|---|
| claims ledger | built. 40 claims in `data/claims.yaml`, all pass, superlatives blocked |
| one state document | done. RESUME.md is now a pointer, RECHECK.md is the only state |
| corpus split | done. tools, taxonomy and other are separate files and must sum to the total |
| regression tests | done. 30 tests, one per known defect class |
| determinism | done as a command. 190 files, byte identical across 11 stages |
| unified gate | done. `./scripts/gate.sh` exits 0 only when every claim holds |
| URL provenance | built. `data/url-provenance.jsonl` holds one dated record per asserted URL, and `check-domain-links.py` regenerates it |

Four things were wrong in the toolchain and are fixed here: `domain-link-check.json` had no
generator at all, so it was a memory. The rest, all now in section 8: the entry completeness claim was
false (75 percent, not 100), three bootstrap scripts were orphaned, and the REA backlog was stated as 12
when the file names 10.

---

## 6c. Phase 1 status (the denominator)

| item | state |
|---|---|
| Set D defined | 1,000 factors across 16 lenses, every factor with a definition, an observable and an evidence class |
| lens coverage | 16 of 16, minimum 62 per lens (L01-L12 at 62, L13-L16 at 64) |
| validator | passes, and it is now in the --full gate |
| what Set D is not | a list of vulnerabilities. It is the set of properties, mechanisms, constraints and actors that decide whether one is possible |

The four lenses no other collection treats as attack surface are the reason this is not a list of
payloads: L13 regulation decides what is permitted and what must be disclosed, L14 evidence science
decides what can be proven at all, L15 the detection industry decides what will be seen, and L16 the
public record is the only source of evidence about the past.

---

## 6d. Phase 2 done (the A to D join)

All sixteen lenses mapped. 1,000 factors, 1,000 coverage records.

| lens | factors | covered at L2+ | share |
|---|---|---|---|
| L01 substrate | 62 | 0 | 0% |
| L02 transport | 62 | 13 | 21% |
| L03 protocol | 62 | 13 | 21% |
| L04 frameworks | 62 | 15 | 24% |
| L05 client | 62 | 5 | 8% |
| L06 identity | 62 | 12 | 19% |
| L07 data | 62 | 8 | 13% |
| L08 money | 62 | 4 | 6% |
| L09 edge | 62 | 11 | 18% |
| L10 supply chain | 62 | 9 | 15% |
| L11 human | 62 | 0 | 0% |
| L12 AI | 62 | 5 | 8% |
| L13 regulation | 64 | 0 | 0% |
| L14 evidence | 64 | 6 | 9% |
| L15 detection | 64 | 5 | 8% |
| L16 history | 64 | 1 | 2% |
| **total** | **1,000** | **107** | **10.7%** |

**The number is 10.7 percent, and zero observed.** That is the first honest coverage figure this project
has had, and it is the reason the README no longer needs a superlative to make its point.

What the distribution says, which is more useful than the total:

- The covered lenses are the ones where a tool exists that states its own oracle. Smuggling, cache,
  GraphQL, deserialisation, hash cracking, cache poisoning, takeover. Tools carry procedures because
  they were built to be run.
- The three zeros are the three lenses where no tool can exist: substrate, human, regulation. You cannot
  ship a scanner for a speculative execution window or for a support desk. Those need authored procedure
  and a lab, which is Phase 7's job.
- Money at 6 percent is the worst return per unit of impact in the whole table. Business logic is where
  real loss lands and it is nearly unaddressed.

---

## 6e. Phase 3 done (the gap, classified)

893 uncovered factors, each in exactly one class. Generated into `docs/CEILING.md`.

| class | meaning | cost | factors |
|---|---|---|---|
| I | derivable with noise, the mechanism is published | authoring | 239 |
| II | inferable from structure, needs a probe | a lab and a target | 603 |
| III | genuinely unavailable, an internal fact | impossible from outside | 51 |

**The ceiling is 94.9 percent.** That is the share of Set D any collection could reach from outside,
given unlimited authoring and lab time. It is not a forecast.

Three things follow, and the first is surprising:

- **Almost nothing in the denominator is hidden.** The constraint on completeness is effort and lab
  access, not secrecy. 51 factors are permanently out of reach and 27 of those are organisational.
- **Class I is 239 factors of coverage available with no target and no permission.** L13 promises 50 of
  them, because statute and standards are published and this repo simply never wrote them down. That is
  the cheapest work in the entire project.
- **Class II is the real project at 603 factors**, and it is where the observed zero lives. L08 money has
  zero Class I factors at all, which is why it sits at 6 percent: every one of its 58 remaining factors
  needs a running system to test.

---

## 6f. Phase 7 started (the thin range)

One lab exists and it produced the first observation. The zero is broken, and it broke honestly.

| lab | factor | pattern | result |
|---|---|---|---|
| `range/lab-01-race` | L07-030 | W01-0001 | **OBSERVED**, obs-001 |
| `range/lab-02-jwt-alg` | L03-047 | none | **OBSERVED**, obs-002 |
| `range/lab-03-route-order` | L04-001 | none | **OBSERVED**, obs-003 |
| `range/lab-04-cache-poison` | L02-036 | none | **OBSERVED**, obs-004 |
| `range/lab-05-ssrf` | L09-031 | none | **OBSERVED**, obs-005 |
| `range/lab-06-idor` | L06-036 | none | **OBSERVED**, obs-006 |

The lab is a signup endpoint whose uniqueness check is not atomic. 24 parallel creates produced 24
records and 23 duplicates. The sequential control produced exactly one record and 23 rejections, which
is what makes the duplicate count attributable to the race rather than to a harness that retried.

Machine checks that now enforce this:

- `scripts/observe.py --verify` replays every recorded lab and reports a mismatch if a verdict changed.
- The coverage validator rejects an L3 record that names no lab with an OBSERVED verdict.
- The atlas gate rejects an OBSERVED pattern whose run record is missing, belongs to another pattern, or
  has no negative control.

Observed coverage is 6 of 1,000, so 0.6 percent. Coverage at L2 or better is 300, so 30.0. It stays
near zero until the Class II work happens, and the README says so rather than rounding up.

Six labs now, and two more defects were found inside probes rather than in targets.

lab-05's third control expected the internal 404 body, but the application wraps an upstream
non-200 into a 502, so the control could never pass. The harness returned INCONCLUSIVE and
refused to record evidence, which is exactly what it is for: a control that cannot pass is a
broken control, not a negative result. The proof was changed to the echoed target, which
shows the request reached the internal service.

A defect was also found inside a probe rather than in a target: lab-03's control stored a status code in a
field named `refused` and the control passed because 401 is truthy. A control that passes for the wrong
reason is worse than no control, so it is a boolean comparison now and the observation file was
regenerated by re-running every lab rather than edited.

---

## 6g. REA operations, first two built

D31 named ten gaps and none were built. Two now are, each with a fixture and a test in the gate.

| op | line | tested | limit |
|---|---|---|---|
| `rea-ops/warc.py` | reads WARC 1.0 response records, plain or gzip, emits HAR shaped JSON | 7 fixture checks | no revisit resolution beyond a pointer, no digest verification |
| `rea-ops/wxapkg.py` | parses a documented wxapkg layout, extracts with traversal refusal | 8 fixture checks | **not validated against a real WeChat package** |
| `rea-ops/leveldb-log.py` | reads a LevelDB write-ahead log: masked CRC32C, records spanning blocks, WriteBatch puts and deletes | 8 fixture checks | reads the log, not the sorted tables, and exits 2 saying so |
| `rea-ops/hap.py` | unpacks a HarmonyOS HAP, identifies Ark bytecode and native libraries, parses module.json | 8 fixture checks | no decompilation, no signature verification |

Six of ten remain, and the tests went from 18 to 34 checks. The two built ones are marked `status: built` in D31 with the path, and a claim
checks that every `built_at` path exists, so a gap cannot be marked done against a file that is not
there.

Two defects were found by building these: the WARC reader opened files in universal newline mode, which
rewrote every CRLF and broke every offset computed from the header terminator; and the wxapkg reader and
its fixture disagreed about header width, which the first test run caught immediately.

---

## 6h. Class I batch started (L13)

The cheapest coverage in the project is the Class I factors, because they need no target and no
permission. Started with regulation, since statute and standards are published and this lens sat at zero.

Ten entries added to D24, each one a verification procedure with an oracle rather than a summary of a
regulation. All ten URLs were checked live before being committed: 275 of 277 answer, and the two that do
not are ISO 27001 and the W3C WebAuthn page refusing automated clients.

| lens | before | after |
|---|---|---|
| L13 regulation | 0 of 64 | **26 of 64 (41%)** |
| L10 supply chain | 9 of 62 | **21 of 62 (34%)** |
| L15 detection industry | 5 of 64 | **19 of 64 (30%)** |
| L05 client and browser | 5 of 62 | **23 of 62 (37%)** |
| L14 evidence science | 6 of 64 | **13 of 64 (20%)** |
| L01 substrate | 0 of 62 | **19 of 62 (31%)** |
| L12 AI and agentic | 5 of 62 | **15 of 62 (24%)** |
| L07 data and storage | 8 of 62 | **22 of 62 (35%)** |
| L13 regulation | 26 of 64 | **40 of 64 (63%)** |
| L11 human and organisational | 0 of 62 | **12 of 62 (19%)** |
| L10 supply chain | 21 of 62 | **38 of 62 (61%)** |
| L15 detection industry | 19 of 64 | **43 of 64 (67%)** |
| L04 frameworks | 15 of 62 | **21 of 62 (34%)** |
| whole denominator | 108 of 1,000 (10.8%) | **300 of 1,000 (30.0%)** |

What the entries do that a policy document does not: each states what to look at and what result settles
it. `d24-gdpr-breach` asks for the awareness timestamp and the article 33(5) register entry, not a promise
of compliance. `d24-pci-scope` asks whether a primary account number appears in any store, log or trace.
`d24-legal-hold` asks whether a hold flag actually suspends the deletion job, which is the part most
systems implement on only one side.

Two consequences of the rebuild, both caught by the gates rather than by reading: the gap classification
had to be rebuilt, and the URL ledger re-run.

Then the cascade was engineered away. Fourteen claims hardcoded counts that any content addition
invalidated. Those literals now live in `readme-stats.py` and the claims compare against `stats[...]`
instead. The second batch of thirteen entries promoted twenty six factors and needed **zero claim edits**,
which is the difference between a ritual and a mechanism.

The link checker also caught a wrong URL: Suricata is `OISF/suricata`, and the entry had
`suricata/suricata`, which resolves to nothing. That is defect 4's class, caught before commit by a
machine rather than after by a reader.

---

## 6i. A substrate domain, so the last zero has somewhere to live

L01 was the only lens at zero on both axes and it had nowhere to put anything: substrate measurement is
not client side, not server side, and not any of the 28 existing domains. Forcing it into D08 would have
been the kind of filing that makes a repo feel organised and teaches nothing.

So D37 exists now, "Substrate: the machine under the interpreter", 8 entries, all methodology rather than
tooling, because the instrument here is a measurement and not a binary:

```
d37-timer-resolution     the granularity step, measured, and how it moves under isolation settings
d37-jit-tiers            a latency discontinuity at an iteration count, and a deopt storm
d37-wasm-pipeline        tier up timing, and a view detached by memory growth
d37-allocator-behaviour  size class adjacency, reuse order, quarantine delay
d37-collector-behaviour  address stability, finalizer ordering, pause distribution
d37-sandbox-reach        the policy and the descriptor table, enumerated
d37-parser-surface       which native decoder parses a crafted file
d37-gpu-surface          a fresh buffer's content before any write
```

L01 goes 0 to 19 of 62. Coverage 18.5 to 20.4 percent.

Each entry names the observable that ends the question rather than the concept. "Content of a fresh
buffer before any write, which should be zero" answers the GPU memory clearing question in one request.
"The granularity step, measured across many reads" answers clock coarsening without reading a setting.

The domain also carries its own gaps, including the honest one: nothing in it is observed, because there
is no substrate harness, and building one is named as the candidate.

---

## 6j. A people domain, so the second zero has somewhere to live

L11 was the last lens at zero. Like substrate it had no domain, and unlike substrate the reason was
awkward: the factors are about how an organisation runs itself, which is not a technical surface at all.

D38 exists now, "People and process: the controls that are held by humans", seven entries. Every one
produces evidence rather than advice:

```
d38-offboarding-access  a login from a leaver's account after their last day
d38-shared-account      one credential used from several distinct clients
d38-secret-storage      a live secret found outside the manager, with its location
d38-device-trust        a device with no enrollment record holding data
d38-privileged-approval an elevated session with no approval record
d38-disclosure-program  a report marked out of scope for a real issue
d38-change-review-depth a sensitive file with no named owner
```

L11 goes 0 to 12 of 62. Coverage 24.7 to 25.9 percent.

Note what stayed out. Twenty seven of L11's factors are Class III and they remain unavailable, because
whether a team keeps an exception register is not in any public source and not revealed by any probe.
The domain's own gap list says so rather than implying the gap will close.

---

## 6k. A grading correction, because the jump was too big to believe

A batch mapped 63 factors to existing entries and coverage went from 25.9 to 32.2 in one run. That is
the kind of jump that should be treated as a warning rather than a win, so the mappings were re-read
against the standard: L2 requires an entry whose stated role is a procedure **for that factor**, not an
entry that touches the same area.

Twenty two of them did not survive that reading. Examples of what was wrong:

| factor | what I had cited | why it failed |
|---|---|---|
| L15-038 decoy placement | telemetry coverage matrix | the matrix entry never discusses decoys |
| L15-042 forensic readiness | telemetry coverage matrix | the matrix covers retention and clocks, not capture before change |
| L15-056 product update channel | deploy credential scope | a security product's own updater is not a deploy credential |
| L10-038 editor extension | install time execution | an IDE extension is not `npm install` |
| L10-048 webhook target | workflow trigger trust | application egress is not a CI event |

All 22 are now L1 with the reason recorded in the record itself, and coverage settled at **30.0 percent**
rather than 32.2.

This is the third time in this project that a number moved in the flattering direction and had to be
pulled back. It is also the first time it was caught by re-reading the grading rather than by a mismatch
with disk, which suggests the standard needs to be written down where it can be enforced, not just
followed by memory.

---

## 6l. The AI layer: a server, not a reading list

The brief asked for an AI-native arsenal. Until now that meant markdown an agent could read and prompts
it could follow, which is a reading list. `mcps/arsenal-mcp.py` is an interface: nine tools over stdio,
standard library only, so an agent asks instead of inferring.

What makes it more than a grep wrapper is that the answers carry the grading. `search_entries` reports
whether each entry has an oracle, so a caller can tell a procedure from a mention without reading the
entry. `coverage` returns L0 to L3 for any factor. `gaps` returns the class that decides whether a
missing factor can be written or needs a lab.

Thirteen protocol checks in `mcps/test-mcp.py`, wired into the default gate. They compare the server's
answers against the same data read directly from disk, which is the only interesting property: a server
that restates the repo wrongly is worse than no server.

One defect found while building it: the test and the server disagreed about which fields a search covers,
so the same query returned six rows in one and eight in the other. Both now use one documented field
tuple. That is the mirror of this project's oldest lesson, from the other direction.

---

## 7. How to re-derive everything

Run in this order. All stages are idempotent.

```bash
cd ~/ai-web-arsenal
python3 scripts/parse-sources.py        # -> data/entries/*.jsonl
python3 scripts/build-corpus.py         # -> data/corpus.jsonl  (repairs names at build time)
python3 scripts/reconcile.py            # -> data/reconcile/  identity must hold
python3 scripts/taxonomy-reconcile.py   # -> data/taxonomy-coverage.json
python3 scripts/merge-identities.py     # -> data/corpus-merge-stats.json
python3 scripts/verify-tools.py         # -> data/install-matrix.json  (unresolved must be 0)
python3 scripts/gen-bootstrap.py        # -> bootstrap/*.sh
python3 scripts/normalize-atoms.py      # MUST run before validate
python3 scripts/render-domain.py --all  # -> domains/*.md
python3 scripts/render-stubs.py         # -> pointer + stub domains
python3 scripts/build-indexes.py        # -> data/domains/*.index.json
python3 scripts/dedupe-names.py
python3 scripts/validate-domains.py     # must print "all invariants hold"
python3 scripts/readme-stats.py         # every number quoted in README
python3 scripts/check-claims.py         # every prose claim in data/claims.yaml
python3 scripts/test-regressions.py     # the known defects, as tests that fail if they return
python3 scripts/check-determinism.py    # rebuild and prove byte identity
./scripts/gate.sh                       # all of the above in one command
```

Atlas:

```bash
cd ~/web-attack-atlas
python3 scripts/render-patterns.py --check --render   # gate must pass
python3 scripts/maintain.py                            # classify counters, regenerate COUNTERS.md
python3 scripts/build-index.py                         # INDEX.md + atom matrix
```

`raw/rivals` and `raw/taxonomy` are gitignored. A fresh clone must run `scripts/harvest-rivals.sh` before
the parse stage.

---

## 8. The twenty-one defects found in this project's own work

Every one was silent and plausible. None caught by reading. Do not reintroduce these.

| # | defect | lesson |
|---|---|---|
| 1 | two recalled facts wrong (a repo called stale that was active, one called live that was archived) | trust the API, never a summary page |
| 2 | link checker used `HEAD`; several real sites answer HEAD 404 and GET 200, giving 7 false dead links | check how you check |
| 3 | classifier fell back to `C02`, so every unmatched counter became "authorisation" and produced a fake 31% finding | a silent default is a claim |
| 4 | two repository URLs invented and indistinguishable from the 110 real ones | a URL not fetched is a hypothesis |
| 5 | mirror coverage metric measured its own scoring (14%, then 26%, then 52%) | when a metric needs three attempts to look good, the metric is the problem |
| 6 | backlog quoted as 10,476; real promotable count 1,419 | counted the parser's output, not the claim |
| 7 | corpus quoted as 24,759; real 21,397 after removing 3,362 image URLs, then 21,381 after badge URLs | images are not entries |
| 8 | name repair ran after its generator and was discarded; retry regex was double escaped and never matched | repairs belong inside the generator |
| 9 | corpus total quoted as "21,194 tool identities" when only 8,848 of its 21,384 rows are tools; the rest are taxonomy nodes | a row is not a tool; count the kind you name |
| 10 | 13 shields.io language-toggle badges survived the image filter because the filter only matched file extensions | a filter that matches one shape of a thing is a sample, not a filter |
| 11 | `pacman -Si` fails machine-wide when any configured repo has a bad signature, which silently reported 16 real tools as unresolved | distinguish "not packaged" from "lookup broken" |
| 12 | the recheck identity line printed "+ residue" and let 75 orphan rows hide inside a word | name every term, sum them out loud |
| 13 | 687 rows stored a bare owner/repo in the `url` field, so "rows carrying a URL" was counting identifiers | a locator is not a link |
| 14 | build-indexes printed "TOTAL promotable 1439" pre-dedupe when the real figure is 1,419 | label the stage, not just the number |
| 15 | RECHECK said 444 entries carried atom, preconditions, oracle, evades, detected_by and driver. Only 75% carry preconditions | a field list is not a coverage claim |
| 16 | bootstrap held 3 orphaned scripts from an earlier numbering, so "11 generated" sat beside 14 files | a generated directory must own its contents |
| 17 | the REA backlog was stated as 12 operations; D31 names 10 | count the file, not the memory |
| 18 | `data/domain-link-check.json` was written by hand and had no generator, so the link health claim could not be rebuilt | an artefact with no producer is a memory |
| 19 | seven entries stored a relative path in their `url` field, which the link checker cannot reach | a pointer is not a link |
| 20 | D11 was titled "REST, GraphQL, gRPC, WebSocket, SSE" while holding no WebSocket or SSE entry | a domain title is a claim about coverage |
| 21 | three artefact ids were invented while authoring the coverage ledger, and the validator caught them | cite an id, then check it exists |

**The standing rule that came out of these: if a number cannot be regenerated from disk, it is not a
number, it is a memory.**

---

## 9. Paused thread: contest repo (do not resume without instruction)

Format understood, in the user's words: a **king of the hill** style tournament. One item, one holder,
points proportional to hold duration. If anyone traces it to you, the entire field turns on you and takes
it. So: ingress undetected, take it, hold it while changing or keeping the value, egress undetected, and
leave nothing that allows retroactive attribution after the event.

Rejected framing: corporate OPSEC / documentation compliance. The user explicitly said no to that.
Accepted framing: competition evasion where **detection is a scoring event**.

Drafted `~/contest-opsec/SCOPE.md` with a 14-domain structure across 5 phases (pre-match, ingress,
takeover, hold, egress + audit, strategy). Nothing else built.

Four open questions to the user before building:

1. Which exact format (HTB King of the Hill, DEF CON style attack-defense, or custom)?
2. Is modifying the item in scope, or only holding it?
3. Are other competitors' boxes attackable?
4. Is there a post-match audit by a judge?

The strategic insight worth keeping: **KotH is a scheduling problem, not a stealth problem.**
`expected_score = hold_minutes * P(not found) - P(found) * remaining`, and P(found) rises with duration
and spikes the moment anyone sees a hostname. Taking it late may beat taking it first.

---

## 10. Rules this project must not break

1. An entry without a driver, a precondition and an oracle is a note, not an entry.
2. A pattern without a negative control is a hypothesis.
3. `OBSERVED` requires a recorded run. Nothing else may claim it.
4. Never type a count. Run the script, name the script.
5. A URL that has not been fetched is a hypothesis.
6. Counters that do not match a class go to `C99`, never folded into another class.
7. No em dashes, no AI-tell vocabulary.
8. Every technique class carries its authorisation requirement.
9. No attribution laundering, no evading law enforcement, no stealth tradecraft for unauthorised access.
10. When correcting your own work, record the correction, do not silently rewrite.

---

## 11. Open questions for the user

1. **REA operations:** build the 10 named gaps as code, or leave them as candidates?
2. **Waves:** 20 remaining, 50 patterns each is ~1,000 patterns. Reduce the bar for R and X waves?
3. **Depth vs breadth:** push domains past 50 entries, or widen to the 1,419 candidates?
4. **The range repo:** build it so `OBSERVED` stops being zero? This is the highest-value missing piece.
5. **Stack playbooks:** build the per-framework layer that answers the original complaint?
6. **Contest repo:** resume when the other two are "finished", and what does finished mean here?
