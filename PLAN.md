# PLAN

Written 2026-10-27. This is the working plan for finishing the two live repos:
`ai-web-arsenal` and `web-attack-atlas`. The contest repo stays paused until both are done.

Everything here is either a measurement or is labelled ESTIMATE. If a number in this file cannot be
regenerated from disk, it is not a number, it is a memory.

---

## 0. What this plan refuses to promise

<!-- claim-ok: quotes the request in order to reject it as unmeasurable -->
The ask was "the most complete in all of humanity". That sentence has no measurable content on its own,
because every awesome list in this space also believes it, and none of them can check it. So it is
converted here into something checkable:

> No collection in this space defines its own denominator. This one will, and it will publish what
> fraction is covered, classify the remainder as derivable, inferable or unavailable, and separate
> what it read from what it ran.

"Most complete" then means a number with a stated ceiling, not a feeling. If the denominator is wrong,
the number is wrong, and the denominator is published so it can be attacked.

What this plan does not promise: private vulnerability research, undisclosed vendor internals, or
zero-days. Those are Class III by construction. The ceiling report in Phase 11 states how much of the
target is permanently out of reach and why, rather than pretending the gap is closed.

---

## 1. The method

Taken from the F1 pit stop plan on the desktop, because the shape of the problem is the same: an object
that looks like a discrete event is actually the convergence point of an entire system, and every
adjacent discipline either feeds into it or is shaped by it.

### 1.1 Object as attractor, not as category

A pit stop is not 2.3 seconds. It is the output of regulations, tyre chemistry, aerodynamics, human
motor learning, meteorology, economics and game theory, compressed into one moment.

The equivalent here: **a web compromise is not a vulnerability class.** It is the convergence point of
the substrate, the protocol stack, the framework, the identity system, the business logic, the supply
chain, the organisation and the defence industry. Sorting attacks by vulnerability class, which is what
every list does, is sorting by one axis of a system that has sixteen.

That is why the atlas is organised by state mutation and not by CWE, and why the arsenal is organised by
domain and not by alphabet.

### 1.2 Set D, Set A, Set M

Three sets, defined before any building:

- **Set D**: every factor in the world that determines whether a web system can be made to do something
  its owners did not intend. Enumerated per lens (section 2). A factor is not a vulnerability. It is a
  property, mechanism, constraint or actor.
- **Set A**: what the repos actually contain, regenerated from disk.
- **Set M = D minus A**: the gap.

### 1.3 Class I, II, III

Every element of M gets exactly one class, and the class decides the response:

- **Class I, derivable with noise.** Can be produced from what exists, with a stated approximation
  error. Example: a technique documented for one framework can be generalised to its sibling runtimes
  by the shared parser. Response: write the derived record, mark the derivation.
- **Class II, inferable from structure.** Not directly present, but its effect is visible in what is
  present. Example: a WAF's rule set is not public, but its behaviour on a mutation series reveals the
  rule. Response: built a probe, not a document.
- **Class III, genuinely unavailable.** No defensible proxy. Private reports, undisclosed internals,
  vendor source. Response: state it, bound its value, stop.

Each Class III item gets a bound on what closing it would be worth, in coverage terms. That is the
ceiling. It exists so that "we are 40% short" can be distinguished from "we are 40% short and half of
that is impossible".

### 1.4 A floor model that every richer model must beat

The Kaggle method insists on a rule-based model with no learned parameters as the floor. If the machine
learning cannot beat hardcoded domain rules, the machine learning is failing.

The equivalent: the 16-atom ontology and the five-question gate are the floor. Any richer taxonomy,
mutation engine or generated corpus must demonstrably cover factors that the floor misses. If a new
layer cannot show that, it is decoration and it does not ship. This is the rule that stops the repos
growing sideways.

### 1.5 Leakage discipline

Random cross validation leaks when rows from one race appear in both folds. The same error has already
happened twice in this project: the mirror coverage metric measured its own scoring, and the classifier
fallback invented a finding. Both were leakage.

The rule from here: **never evaluate coverage on the material that produced the taxonomy.** Sources are
split into a build set and a held-out set before authoring. Coverage is reported on the held-out set.
The drop between the two is the generalisation figure, and it is published even when it is bad.

### 1.6 Quality gates

Every phase ends with a gate that can fail and blocks the next phase. A gate is a command, not an
opinion. The current equivalent is `scripts/recheck.py`, which already fails the build when a doc and
the disk disagree.

### 1.7 Blackboard

One state document, holding phase status, gate results and last run dates. **Implemented as `RECHECK.md`
rather than `data/STATE.json`:** a machine readable file still drifts unless something compares it to disk,
and `scripts/recheck.py` parses a fenced block out of the markdown and compares every number in it. A file
nobody parses is a third copy of the truth, which was the original problem
and the current measured numbers. Prose docs read from it. No phase is "done" because it feels done.

---

## 2. Set D: the sixteen lenses

Each lens is a discipline, not a category. The test for inclusion: could a real compromise turn on this
and nothing else? If yes, it belongs in D.

| id | lens | what it owns |
|---|---|---|
| L01 | substrate | CPU, memory, allocator, GC, JIT, kernel interfaces, timing primitives |
| L02 | network and transport | IP, TLS, HTTP/1.1, H2, H3/QUIC, DNS, WebSocket, SSE, WebRTC, WebTransport |
| L03 | protocol semantics | REST, GraphQL, gRPC, SOAP, JSON-RPC, MCP, A2A, SAML, OAuth/OIDC, OData |
| L04 | frameworks and runtimes | per language and framework, including their parsers and conventions |
| L05 | client and browser | DOM, JS engines, WASM, ServiceWorker, extensions, webviews, Electron, Flutter and RN web |
| L06 | identity and session | authn, authz, MFA, WebAuthn, SSO, token formats, session stores, impersonation |
| L07 | data and storage | SQL, NoSQL, object, queue, cache, search, ORMs, migrations, exports, backups |
| L08 | business logic and money | pricing, coupons, refunds, inventory, auctions, betting, ads, referrals, subscriptions |
| L09 | infrastructure and edge | CDN, proxies, load balancers, WAF, gateways, serverless, containers, IaC, control planes |
| L10 | supply chain | registries, dependencies, builds, CI/CD, signing, third-party scripts, tag managers |
| L11 | human and organisational | support, helpdesk, employees, social engineering, insider, onboarding, process |
| L12 | AI and agentic systems | LLM apps, RAG, tool use, MCP servers, agent browsers, model supply chain |
| L13 | regulation and standards | CFAA and equivalents, GDPR, PCI, scope law, standards bodies, disclosure norms |
| L14 | evidence and oracle science | how a claim is proven: differential, timing, statistical, side channel, negative control |
| L15 | detection and defence industry | products, rule languages, telemetry, IR, forensics, what each control actually sees |
| L16 | history and corpus | CVE, OSV, GHSA, disclosures, talks, writeups, thirty years of record |

Two properties make this different from a category list. First, L13 to L16 are not attack categories at
all, yet each one changes what is possible; L13 decides what may be done, L14 decides what can be
proven, L15 decides what will be seen, L16 is the only source of evidence about the past. Second, a
single compromise routinely needs four lenses at once, which is why the attack grammar multiplies atoms
by mutations rather than listing them.

---

## 3. Set A: what exists today, measured

Regenerated by `scripts/readme-stats.py` and `scripts/recheck.py` on 2026-10-27.

```
corpus        21,384 rows = 8,848 tools (8,692 identities)
                          + 11,712 taxonomy nodes + 577 social + 247 knowledge
reconcile     31,298 = 13,516 admitted + 17,506 excluded + 204 held + 71 orphan + 1 unresolved
domains       28 authored + 9 pointers, 444 enriched entries, 37 rendered
patterns      150 in 3 waves (135 ESTABLISHED, 15 PROBABLE, 0 OBSERVED)
tools         64 in manifest, 0 unresolved
taxonomy      624 of 706 framework items mapped to atoms (88.4%)
promotable    1,419 candidates indexed but not enriched
REA ops       12 identified as missing, 0 written
verifier      40 checks, 40 pass
```

The number that matters most in that block is the zero. **Nothing in either repo has been observed
running.** ESTABLISHED means read and cited. Nothing has been executed against a live target under
controlled conditions, because there is no controlled target. That is the credibility gap, and Phase 7
is the only phase that closes it.

ESTIMATE, not measured, to be replaced in Phase 2: of roughly 1,000 to 1,500 factors in D, on the order
of a quarter have any artifact in A, fewer than a tenth have an oracle, and almost none have an
observation.

---

## 4. The phases

Eleven phases plus a remediation phase. Each has a gate. Order matters: Phase 0 exists because adding
content to a base that miscounts itself multiplies the error.

### Phase 0: the truth layer (remediation)

The mess is not six wrong numbers. It is that nothing prevented six wrong numbers. Fix the mechanism.

1. **Claims ledger.** `data/claims.yaml`, one entry per factual claim in any doc: id, file, line, the
   claim text, a machine check, and a status. `scripts/check-claims.py` runs all of them. A doc sentence
   containing a number or a superlative without an entry fails the check.
2. **URL provenance.** Every URL in an authored file comes from `data/url-provenance.jsonl` with a
   checked date, method and status. An invented URL becomes impossible because nothing ships unchecked.
3. **Corpus separation.** Tools, taxonomy nodes and social rows live in separate files with separate
   counts. The 2.4x overcount happened because one file held three kinds of thing.
4. **Regression tests for all fourteen known defects.** Each defect in RECHECK section 8 becomes a test
   that fails if it returns.
5. **One state file.** One state document replaces the drift between RESUME.md and RECHECK.md. Two state
   docs already disagreed once; one is enough.
6. **Determinism gate.** Rebuild and byte-compare, as a script and as a pre-push hook.

Gate: `check-claims` passes, all fourteen tests exist and pass, one state file, rebuild is byte
identical. Exit criterion: the repo cannot quietly lie about itself any more.

### Phase 1: define the denominator

1. Enumerate D per lens at the level of factors, not vulnerabilities. Target 1,000 to 1,500 factors.
2. Each factor gets: id, lens, one-sentence definition, observability class at world level, the kind of
   evidence that would settle it, and whether a public artifact exists at all.
3. Each lens gets a falsification statement: what would prove this lens is covered.

Gate: |D| at least 1,000, every factor has a testable observation, no lens is empty, and the file is
reviewable by someone who disagrees with it.

### Phase 2: audit A against D

1. Recompute A from disk.
2. Join A to D. This join has never been attempted and is the actual contribution.
3. Output the coverage matrix and the gap list M.
4. Flag any A item that maps to no factor: either D is incomplete or the item is noise, and both are
   findings.

Gate: every A item is mapped or flagged, every unmapped item has a decision recorded.

### Phase 3: classify the gap

Every M element becomes Class I, II or III with a response, and every Class III gets a value bound.

Gate: zero unclassified, ceiling stated as a range with the method that produced it.

### Phase 4: breadth engines

Hand authoring cannot reach a thousand factors. This phase builds machines that produce records with
provenance, so that breadth is generation plus audit rather than typing.

1. **Advisory mass mapping.** Pull every web-relevant CVE, OSV and GHSA record, map each to atoms,
   mutations and lenses. One record per advisory. ESTIMATE: tens of thousands of records.
2. **Disclosure corpus.** Public bug bounty disclosures, writeups, conference archives. Mapped to atoms
   and, critically, to oracles, because a disclosure usually says how it was proven.
3. **Mutation engine.** From `atom x mutation`, generate variants mechanically. Each candidate must pass
   the five-question gate or be discarded with a reason. This is the intended multiplier on the 150
   hand-written patterns.
4. **Capability mining.** Search registries by what a tool does, not by its name. The current corpus is
   name-heavy because it was harvested from name lists.
5. **Taxonomy mining.** Close the 82 unmapped framework items and track new frameworks.

Gate: every generated record carries provenance, every candidate passes or is rejected with a reason, a
2% sample is audited by hand and the error rate is stated. A gate that cannot fail here is not a gate.

### Phase 5: depth engines, one per lens

Sixteen workstreams, each producing patterns, counters and oracles for its lens, plus the 20 queued atlas
waves, plus bringing every authored domain to the 50+ enriched bar.

Gate: per domain, 50 or more enriched entries, every pattern with procedure, oracle and negative control.

### Phase 6: stack playbooks

The original complaint about every other list was that a row does not tell an agent what to do. A
playbook is the answer: for a given stack, what fails, in what order, with which oracle, and what the
evidence looks like. One per major framework and runtime.

Gate: each playbook runs end to end against the Phase 7 range.

### Phase 7: the range

This is the phase that matters most, and the reason the zero in section 3 matters.

Containerised, local, disposable targets per atom class. Every pattern gets either a lab that
demonstrates it or an explicit UNTESTED label with the reason. This is what turns ESTABLISHED into
OBSERVED, and OBSERVED is the only status a rival list cannot fake by reading.

Gate: every ESTABLISHED pattern is OBSERVED or UNTESTED-with-reason, and the ratio is published.

### Phase 8: the counter layer

For every defensive product: how it decides, which patterns die, which survive, at what cost. For every
pattern: the counter, and the detection rule that would catch it (Sigma, Semgrep, YARA or WAF syntax as
appropriate).

Gate: every pattern has a counter and a detection, and every control class has at least one documented
bypass with its precondition.

### Phase 9: the AI-native layer, tested

MCP server over the corpus so any agent can query patterns, tools and domains live. Skills per workflow.
Prompt packs that are run against the range to see whether an agent actually completes the job.

The benchmark is the part that matters: the same lab tasks, with the repo and without it. If the repo
does not measurably improve an agent's success rate, the AI-native claim is dropped rather than asserted.

Gate: a measured improvement, or the claim is removed from the README.

### Phase 10: the REA operations

The ten gaps named in `data/domains/D31.json`, as code: LevelDB reader, wxapkg unpack, Flutter AOT
and blutter, Hermes and React Native, HarmonyOS HAP, WARC, service worker reconstruction, WebAuthn
attestation, signing recovery, and source map recovery. The count is 10, not 12; this line said twelve
until the ledger was built, which is the point of the ledger.

Each gets a fixture, a test, a doc and wiring into the MCP. This was a decision made and not honoured,
which is why it is a phase and not a nice-to-have.

Gate: every operation has a fixture and a passing test, and the MCP exposes it.

### Phase 11: synthesis and the ceiling report

Knowledge graph across D, A and evidence. Coverage ledger. The ceiling report: what fraction of D is
covered, what is parsed from public record, what was run, what is permanently out of reach, and what it
would cost to close the rest.

Gate: the headline claim in the README is generated from this report, not written by hand.

---

## 5. Sequencing

Dependencies are real, not stylistic. Phase 0 before everything, because content added to a base that
miscounts itself multiplies the error. Phase 1 before 2, because you cannot audit against an undefined
denominator. Phase 7 as early as possible among the content phases, because observation changes what the
later phases are allowed to claim.

```
0  truth layer            -> blocks all
1  denominator            -> blocks 2, 3
2  audit                  -> blocks 3
3  classify gap           -> blocks 4, 5 priority order
4  breadth engines        -> parallel with 5
5  depth engines          -> parallel with 4
6  playbooks              -> needs 5 and 7
7  range                  -> needs 5, unblocks OBSERVED
8  counters               -> needs 5
9  AI layer               -> needs 4, 5, 7
10 REA operations         -> independent, can run any time after 0
11 synthesis              -> needs all
```

Effort, in work blocks of roughly one session each. These are ESTIMATES.

| phase | blocks | why |
|---|---|---|
| 0 truth layer | 3 | mechanical but tedious, and every later phase depends on it |
| 1 denominator | 4 | 1,000+ factors written by hand, no shortcut |
| 2 audit | 2 | a join, once the schema exists |
| 3 classify | 2 | judgement, not volume |
| 4 breadth | 8 | pipelines plus audit of their output |
| 5 depth | 12 | sixteen lenses, 20 waves, 28 domains to 50+ |
| 6 playbooks | 4 | per stack |
| 7 range | 6 | containers, fixtures, per-class labs |
| 8 counters | 5 | per product and per pattern |
| 9 AI layer | 5 | MCP, skills, and an actual benchmark |
| 10 REA ops | 4 | ten operations, each with a fixture |
| 11 synthesis | 3 | graph and report |
| total | 58 | |

### The shortest path to a defensible v2

Not all 58 blocks are needed before the repo stops being embarrassing. This subset is:

**Phase 0 (3), Phase 1 (4), Phase 2 (2), Phase 3 (2), Phase 7 partial (3), Phase 11 partial (1) = 15
blocks.**

That delivers: a repo whose claims are machine-checked, a published denominator, a measured coverage
fraction, a classified gap with a ceiling, and a first batch of OBSERVED patterns. At that point the
README can say something no rival can: here is our denominator, here is our coverage, here is what we
ran, here is what is impossible. Everything after that is volume.

### What gets cut if time runs short

In order: stack playbooks (nice, not structural), counters (valuable but downstream), the AI benchmark
(drop the claim instead of faking it), then breadth engines (depth matters more than another ten
thousand rows). Phase 0, 1, 2, 3 and 7 are never cut. They are the difference between a list and an
instrument.

---

## 6. Rules that do not bend

1. A number that cannot be regenerated from disk is a memory, not a number.
2. A claim in prose is a claim. If it is not checked, it will drift, and it has drifted fourteen times.
3. Status is earned: ESTABLISHED means cited, OBSERVED means run here. They never share a column.
4. Class III is stated, not hidden. The ceiling report exists so the gap is visible.
5. Never evaluate on the material that built the taxonomy.
6. A richer model must beat the floor model or it does not ship.
7. No invented URLs, packages, versions or paths. Ever. Fourteen defects, two inventions, both mine.
8. Authorisation is a precondition in every pattern, not a footer.
9. The contest repo stays paused until both live repos pass their gates.
10. When a phase gate fails, the phase is not done, whatever the prose says.

---

## 7. Decisions

Closed 2026-10-27, before Phase 0 started.

1. **Range scope: thin first.** Three or four flagship labs, about 2 blocks, chosen for the patterns
   that carry the most weight. It breaks the zero and proves the method. The full range stays in the
   plan as a later phase rather than being cut, because per-class labs are what make OBSERVED
   comprehensive instead of illustrative.
2. **Advisory mass mapping: separate dataset with its own counts.** Generated records never mix with
   hand-authored ones, and no generated volume can inflate a curated figure. This is the same failure
   the corpus hit when tools and taxonomy shared a file, so the rule is structural, not stylistic.
3. **One state document.** RECHECK.md is the single source of state. RESUME.md becomes a pointer to it.
   Two documents already drifted once; one is enough.
4. **Version naming: tag v2 when the short path's gates pass.** Until then the repo stays v1 and the
   version number is not used as a progress signal. A tag is a claim, so it waits for the gates.

The effect on effort: thin range replaces the 6 block range with 2, so the total is 54 blocks and the
short path is 14.

| short path | blocks |
|---|---|
| Phase 0 truth layer | 3 |
| Phase 1 denominator | 4 |
| Phase 2 audit | 2 |
| Phase 3 classify gap | 2 |
| Phase 7 range, thin | 2 |
| Phase 11 ceiling report, partial | 1 |
| total | 14 |
