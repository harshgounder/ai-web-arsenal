# SCOPE v1: the superset derivation

Status: draft for approval. Nothing here is a final taxonomy.
Built: 2026-10-26. Author: DSH session, from local prior art plus a dated research wave.
Rule that governs this file: **examples are seeds, never boundaries.** Every example named below is a
member of a set that is derived first, in writing. The set is not the example.

---

## 0. What this repo is

An AI-native arsenal for attacking and defending web platforms. Layered: README hub, one document per
domain, plus machine-readable data an agent can load without parsing prose.

Three things separate it from every list currently on GitHub.

1. **Axes, not buckets.** Existing lists sort by tool type. This one measures coverage across
   target-surface x agency-level x lifecycle-stage x artifact-type, so a missing cell is a visible hole
   rather than an invisible absence.
2. **Rival reconciliation.** Every entry in every comparable collection is either in this repo or in an
   exclusion ledger with a reason code. The claim "nothing left out" is arithmetic, not adjectives.
3. **REA spine.** A reverse-engineering extraction layer that turns a live web target into machine-usable
   state (bundle graph, endpoints, schemas, native mobile artifacts, WASM, captures, storage) before any
   exploitation reasoning begins. Most offensive AI tooling starts at the HTTP request. This starts
   earlier, at the artifact.

Not a fork of BYOK Cyber Arsenal. That repo maps all of security. This one goes deep on one attack
surface and adds the agent layer, the reasoning layer and the extraction layer.

---

## 1. Inherited hard rules

From `everything-map/docs/03-completeness-protocol.md` and `byok-cyber-arsenal/METHOD.md`, both already
house law:

- Maps come from research waves. A row with no landing file behind it does not exist.
- Provenance on every claim. Disagreements recorded, never smoothed.
- Not-found ledger is permanent. "Complete" is never claimed, only high-confidence-not-exhaustive.
- Counts are recomputed from disk before being quoted, never recalled.
- Status ladder: VERIFIED-DR > VERIFIED (search, dated) > ANCHORED-ACTIVE > CHAT > TBD. DISPUTED held,
  never deleted.
- Examples are seeds. Derive the superset before mapping.
- Safety boundary: mapping attack classes is research. Operational assistance for unauthorized access is
  out of scope, and each technique class carries its authorization requirement.

New rules for this repo:

- No em dashes anywhere. No emoji in data files, sparing use in prose.
- Every entry carries `first_seen`, `last_verified`, `source_url`, `status`.
- Two independent engines for any claim that matters. One tool output is not evidence.
- Regional sources are first-class, not an appendix. Gitee, GitLab, Codeberg, SourceHut, GitFlic,
  GitVerse, Hugging Face and vendor blogs count the same as GitHub.

---

## 2. Diagnosis: why the current lists fail

Measured on 2026-10-26, not recalled.

Every value below was measured with `gh repo view` on 2026-10-26 and is stored in `data/rivals.json`.
Two earlier claims in this draft came from memory and were wrong. Both are corrected here rather than
quietly overwritten, because the correction is the evidence that the method works.

| collection | stars | created | last push | the defect |
|---|---|---|---|---|
| qazbnm456/awesome-web-security | 13,962 | 2017-01-29 | 2026-09-14 | 26 open issues, 1,839 forks. Structure frozen in the pre-API era: no API protocol, no cloud, no agent layer, no AI app surface. |
| infoslack/awesome-web-hacking | 7,330 | 2015-05-03 | 2026-09-18 | tool dump by category. No reasoning, no evidence standard, no stack playbooks. |
| 0xInfection/Awesome-WAF | 7,662 | 2019-01-08 | 2026-08-26 | deep on one layer, WAF, and nothing else. Correct as a specialist document, wrong as a scope model. |
| vavkamil/awesome-bugbounty-tools | 6,425 | 2021-01-11 | 2026-10-06 | **correction**: it is active, not stale. 338 links over 37 sections. The real defect is no per-entry dates, no driver model, no AI layer. |
| arainho/awesome-api-security | 3,867 | 2020-08-14 | 2026-05-01 | **archived**. The canonical API security list is frozen. This is the single clearest hole in the ecosystem. |
| Hack-with-Github/Awesome-Hacking | 123,695 | 2016-03-30 | 2026-07-26 | an index of indexes. Its job is pointing at other lists, several of which are dead. |
| carpedm20/awesome-hacking | 17,353 | 2014-12-16 | 2024-06-02 | stale by more than two years. Historical value only. |
| devanshbatham/Awesome-Bugbounty-Writeups | 6,167 | 2020-05-04 | 2023-08-06 | writeup corpus frozen at 2023, while the field moved to API, cloud and AI surfaces. |
| penstriker/awesome-ai-pentest-tools | 0 | 2026-09-07 | 2026-09-07 | 2 commits, single-vendor curated. Correct era, wrong provenance. |
| skyvanguard/awesome-ai-pentesting | 95 | 2026-02-17 | 2026-10-25 | closest in spirit, has an MCP section, active. Still a link list with no extraction layer and no reconciliation. |
| RandomAdversary/Awesome-AI-Security | 1,689 | 2017-09-07 | 2026-03-08 | broad AI security, mostly defensive framing. No web attack surface model. |
| punkpeye/awesome-mcp-servers | 96,900 | 2024-11-30 | 2026-10-23 | the MCP universe at 3,880-plus rows. Security is a small slice and needs filtering, not mirroring. |

Seven structural defects that repeat across all of them:

1. **Vulnerability-class myopia.** Sorted by XSS, SQLi, SSRF. Nobody sorts by "what do I do when the
   target is a Next.js app on Vercel with Clerk auth and a GraphQL gateway". Stack determines technique.
2. **Tool without driver.** A row says `nuclei` and gives a link. It does not say how an agent invokes it,
   what JSON it emits, whether it reads stdin, or what its false-positive profile is. An agent cannot use
   that row.
3. **No agency axis.** Everything is listed as if a human runs it. Autonomy level is the single most
   important property in 2026 and no list encodes it.
4. **No artifact model.** Nothing tells you how to get the client bundle, the mobile APK, the source map,
   the HAR, the WASM, the protobuf schema. The list starts after the data is already in hand.
5. **No defense mirror.** Offense rows sit alone. The rule that catches that technique, and the control
   that blocks it, are the other half of the same fact.
6. **Stale by construction.** A README with 400 links and no date column cannot be audited. Nobody knows
   which rows died.
7. **Western and GitHub-only.** Gitee, Chinese agent frameworks, Korean offensive vendors, Russian tooling
   scenes, Indian community corpora: mostly absent. ARTEX alone shows the cost of that blind spot.

---

## 2b. The generative layer

DECIDED 2026-10-26: the atlas is a **separate repo**, `web-attack-atlas`. This repo keeps tools,
installs, drivers, MCP wiring, REA, the corpus and the reconciliation ledger. That repo keeps atoms,
patterns, preconditions, oracles, chains, playbooks and counters. Join key is `entry_id`.

The grammar lives there, at `web-attack-atlas/docs/ONTOLOGY.md`:

```
attack = atom(sink, carrier, preconditions, oracle) x mutation(encoding, context, protocol, timing)
chain  = attack_1 . attack_2 ... where capability(attack_n) enables preconditions(attack_{n+1})
```

16 atoms. Every technique in history is a composition of them. This is what makes "every attack method"
tractable: the axes are finite and enumerable, mutations are generated, and coverage becomes a measured
cell count instead of a row count. Nothing in the domain docs gets written until it fits the grammar.

---

## 3. Axis A: target surface (17 levels)

This is the primary sort. Each level is a thing that can be attacked, independent of technique.

| id | surface | what it covers |
|---|---|---|
| S01 | transport and edge | DNS, TLS, HTTP/1.1, HTTP/2, HTTP/3 and QUIC, CDN behaviour, ALPN, certs, connection reuse |
| S02 | server stack and runtime | IIS, nginx, Apache, Tomcat, Jetty, Node, Deno, Bun, PHP-FPM, Gunicorn, uWSGI, JVM, CLR, Go net/http |
| S03 | routing and parsing | path normalization, host header, absolute URI, content-type confusion, request smuggling and desync, parameter pollution |
| S04 | identity and session | cookies, JWT, JWE, OAuth 2.x, OIDC, SAML, SCIM, passkeys and WebAuthn, MFA, device code, PRT, session fixation |
| S05 | authorization model | BOLA, BFLA, tenant isolation, role graph, ABAC and policy engines, field-level authz, delegated access |
| S06 | data layer | SQL, NoSQL, graph DB, search engine, cache, object storage, ORM, query builders, database wire protocols |
| S07 | serialization | JSON, XML, YAML, Java serialization, .NET format, PHP unserialize, Python pickle, Ruby Marshal, protobuf, CBOR, msgpack, AMF |
| S08 | client side | DOM sinks, framework internals (React, Vue, Angular, Svelte, Next), storage, postMessage, WebSocket, service worker, CSP, SRI, trust boundaries |
| S09 | API protocols | REST, GraphQL, gRPC and gRPC-Web, SOAP, WebSocket, SSE, webhooks, AsyncAPI, MCP |
| S10 | business logic | state machines, money flow, quotas, coupons, races, replay, multi-step workflows, idempotency, time-of-check to time-of-use |
| S11 | cloud control plane | IAM, storage buckets, serverless, metadata and IMDS, K8s API, service mesh, secrets managers |
| S12 | supply chain | package registries, dependency confusion, CI/CD pipelines, artifact repos, build caches, signing |
| S13 | AI application surface | prompt injection, tool call abuse, RAG poisoning, model endpoints, embeddings, output handling, agent permissions |
| S14 | agent and tooling surface | MCP servers, agent skills, plugin marketplaces, tool registries, the AI stack as a target in itself |
| S15 | browser and native bridge | webviews, deep links, Electron, custom URL schemes, mobile app trust boundary, push, clipboard |
| S16 | human layer | helpdesk, phishing resistance, social engineering, insider, support impersonation |
| S17 | perimeter that gates the app | WAF, bot management, VPN, zero trust, rate limiting, fingerprinting, challenge systems |

---

## 4. Axis B: agency level (8 levels)

How much of the work the AI actually does. This axis is absent from every list found so far.

| id | level | definition |
|---|---|---|
| A0 | literature | knowledge that changes a human's plan. No target touched. |
| A1 | copilot | human drives, model suggests payload, next step, or interpretation |
| A2 | tool-calling agent | model selects and calls tools, human approves state-changing actions |
| A3 | autonomous loop | plan, act, observe, replan, within a budget and scope guard |
| A4 | supervised multi-agent | distinct roles (recon, hypothesis, exploit, critic, reporter) with a coordinator |
| A5 | self-verifying agent | finding must survive a negative control before it is reported. The agent is its own skeptic. |
| A6 | continuous | monitors, diffs target state over time, re-tests on change |
| A7 | self-extending | writes new tools, skills or detectors from what it learned on this target |

Most 2026 "AI pentest" products sit at A2 or A3 and advertise as if they were A5. The gap between A3 and
A5 is where almost all false positives in AI pentesting live. This repo should say so per row.

---

## 5. Axis C: artifact type (16 levels)

What the thing physically is. Determines how an agent loads it.

K01 CLI tool. K02 library or SDK. K03 MCP server. K04 agent framework or orchestrator. K05 skill, plugin or
prompt pack. K06 wordlist, payload corpus or template. K07 detection rule (Sigma, Suricata, CRS, YARA).
K08 benchmark, lab or target range. K09 dataset. K10 paper, spec or RFC. K11 writeup or case study.
K12 cheatsheet, checklist or taxonomy. K13 model, LLM or classifier. K14 decision tree or playbook.
K15 evidence format or reporting schema. K16 harness, runner or sandbox.

---

## 6. Axis D: lifecycle stage (12 levels)

L01 scope and authorization. L02 passive recon and OSINT. L03 active surface mapping and fingerprinting.
L04 content and endpoint discovery. L05 hypothesis generation and per-stack threat model. L06 probing and
validation. L07 exploitation and chaining. L08 proof of impact and negative control. L09 escalation and
pivot. L10 reporting and triage. L11 remediation advice and fix verification. L12 continuous monitoring
and regression.

---

## 7. Axis E: reverse-engineering depth (8 levels)

This is the REA axis, and the reason this repo can start earlier than its competitors.

| id | depth | what you hold |
|---|---|---|
| R0 | black box | HTTP responses only |
| R1 | front-end artifact | JS bundle, source map, WASM, CSS, manifest, service worker |
| R2 | client application | APK, IPA, Electron app, ASAR, extension CRX, mini-program package |
| R3 | server artifact | jar, dll, php source, node_modules leak, docker image, backup file |
| R4 | compiled binary | native module, WASM compiled from C, embedded firmware |
| R5 | protocol reverse | undocumented wire format recovered from capture |
| R6 | cryptographic recovery | request signing, custom encryption, key derivation recovered from client code |
| R7 | full reconstruction | the application's logic rebuilt well enough to reason about business rules offline |

R5 to R7 is where normal bug bounty stops and where this repo should not.

---

## 8. Axis F: defense autonomy (7 levels)

The mirror axis, for "beat every defensive tool".

| id | defense | what it does to the attack |
|---|---|---|
| F1 | none | nothing |
| F2 | signature WAF | pattern match, bypassed by encoding and context |
| F3 | protocol-aware WAF | parses the request properly, needs semantic bypass |
| F4 | RASP and in-app | sees runtime context, needs logic-level attack |
| F5 | bot management | fingerprints the client, needs a real browser or a solved challenge |
| F6 | zero trust and conditional access | identity-centric, needs token or session theft |
| F7 | AI detection | model-based anomaly scoring, needs normal-looking traffic and pace control |

Every offensive row gets an `evades` field listing which F levels it addresses, and a `detected_by` field
pointing at the rule or control on the other side.

---

## 9. Axis G: region and platform (11 + 10)

Region: global, CN, RU, IN, BR, EU, JP, KR, IL, IR, TR.
Platform: GitHub, GitLab, Gitee, Codeberg, SourceHut, GitFlic, GitVerse, Radicle, Hugging Face, and
package registries (npm, PyPI, crates, Maven, NuGet, Packagist, RubyGems).

The point is not decoration. A tool with 40 stars on Gitee and a working Chinese-language UI can be the
only thing that handles a WeChat mini-program target, and no Western list will ever include it.

---

## 10. The cell model, and how "complete" is measured

Coverage is not a count of links. It is the filled fraction of a sparse product space.

```
cell = (surface, lifecycle_stage, agency_level)
```

Not every cell is meaningful. A cell is *required* if a reasonable practitioner would want something
there. Required cells are declared per domain document, with a reason, and the reason is reviewable.

```
coverage(required) = filled / required
gap(required)      = required - filled      # each becomes a NO-TOOL GAP record or a BUILD CANDIDATE
```

Two numbers are reported separately and never merged:

- **Discovery coverage**: do we know the category exists.
- **Implementation depth**: do we know how to rebuild or drive it.

A repo can know every category and implement almost none. Saying so is the honest position, and it is what
`byok-cyber-arsenal` learned the hard way when v3 published 158 covered and the reproducible count was 137.

---

## 11. Domain map: 37 documents

README is the hub. Each row below is one file plus one JSON.

| id | domain | primary axes it stresses |
|---|---|---|
| D00 | how to use this repo | meta |
| D01 | reasoning models and decision trees | K14, all surfaces |
| D02 | recon and surface mapping | S01, S02, L02, L03 |
| D03 | fingerprinting and stack identification | S02, L03 |
| D04 | authentication and identity providers | S04, R2 |
| D05 | authorization, tenancy, field-level access | S05, L07 |
| D06 | session, token, cookie, key material | S04, S08, R6 |
| D07 | injection family (SQL, NoSQL, LDAP, XPath, OS, expression) | S06, S07 |
| D08 | client-side and browser trust boundaries | S08, S15 |
| D09 | HTTP semantics, smuggling, desync | S01, S03 |
| D10 | cache, CDN, edge behaviour | S01, S17 |
| D11 | API protocols: REST, GraphQL, gRPC, WS, SSE, MCP | S09, R5 |
| D12 | business logic, races, money paths | S10 |
| D13 | file handling, upload, path, archive | S06, S07 |
| D14 | server-side request and fetch (SSRF and friends) | S02, S11 |
| D15 | deserialization and template engines | S07, R3 |
| D16 | cryptography, secrets, signing | S04, R6 |
| D17 | cloud and control plane | S11 |
| D18 | supply chain and CI/CD | S12 |
| D19 | AI application attacks | S13, R1 |
| D20 | agent, MCP and skill attacks | S14 |
| D21 | mobile app and webview bridge | S15, R2 |
| D22 | WAF, bot and anti-automation evasion | S17, F2 to F7 |
| D23 | exploitation and chaining | L07, L08, L09 |
| D24 | evidence, proof and reporting | K15, L08, L10 |
| D25 | detection and defense mirror | K07, F1 to F7 |
| D26 | labs, ranges, benchmarks | K08 |
| D27 | knowledge corpora: writeups, payloads, taxonomies | K06, K11, K12 |
| D28 | MCP servers for web work | K03 |
| D29 | CLI tools an agent can drive | K01 |
| D30 | agent frameworks and orchestrators | K04 |
| D31 | REA spine: target artifact extraction | R0 to R7 |
| D32 | vendors and market, dated | K13, meta |
| D33 | rival reconciliation ledger | meta |
| D34 | freshness engine and maintenance | meta |
| D35 | bootstrap and BYO-AI onboarding | K16, meta |
| D36 | attack pattern ontology | K12, K14, all surfaces |

---

## 12. The REA spine (D31), spelled out

The extraction layer runs before hypothesis. It converts a target into state.

### 12.1 What REA already gives a web target

Available in this session, each is a real callable operation:

| operation | what it yields on a web target |
|---|---|
| `analyze_web_bundle` | chunk graph, route candidates, endpoint candidates, vendor fingerprints, page-declared WebMCP metadata, optional source-map fetch |
| `export_web_scripts` | JS bytes out of a capture, with provenance and a manifest |
| `inspect_web_page` | DOM, accessibility tree, script list, resources, storage key inventory, JSON body shapes, WebSocket shapes |
| `inspect_web_event_listeners` | every listener on a selector, with source ownership and exact script text |
| `inspect_web_network_capture` | HAR, mitmproxy, SAZ, qlog, with exact byte ranges |
| `trace_web_source_location` | generated position to original source, through a paired source map |
| `trace_web_module_imports` | ES import and re-export graph from an exported script |
| `recover_javascript_sources` | Wakaru deobfuscation into readable modules |
| `analyze_javascript_application` | ASAR or extracted JS app as an execution-free graph |
| `reconcile_javascript_runtime` | static bundle graph against observed runtime scripts |
| `discover_webmcp_tools` | page-registered WebMCP tool inventory and schemas |
| `capture_browser_scenario` | controlled scenario with network, storage, DOM and screenshot capture |
| `inspect_electron_page`, `inspect_electron_fuses` | Electron surface and packaged fuse state |
| `inspect_android_package`, `decode_android_resources`, `search_android_classes`, `inspect_android_method`, `trace_android_references` | the mobile client, at class and resource level |
| `inspect_wasm_artifact` | WASM validation, imports, exports, WAT |
| `inspect_sqlite_database` | client-side database schema and rows |
| `compare_web_captures`, `compare_web_screenshots` | change detection between two states |
| `inspect_artifact`, `extract_artifact` | archive and package inventory, safely extracted |

That set is already stronger than what most web pentest tooling offers as an extraction story. It is the
reason D31 exists as a domain rather than a footnote.

### 12.2 What REA does not yet do, from your own `rea-expansion` research

These are the extension targets. Each becomes either an entry, a wrapper spec, or a build candidate.

Named in `re-arsenal/docs/GAP-MATRIX.md` and `rea-expansion`:

- Chromium LevelDB readers for LocalStorage and IndexedDB (gap, unzip plus a LevelDB library)
- WebView2 host artifacts
- WeChat and Alipay mini-program unpacking (`wxapkg`), a China-only lane
- Flutter AOT (`blutter`) for apps whose logic is not in DEX
- Hermes and React Native bundle recovery
- HarmonyOS HAP and ABC bytecode
- WARC archive reading
- Service worker and cache storage reconstruction
- WebAuthn and FIDO attestation parsing
- Request signing recovery when the algorithm lives in obfuscated JS
- GraphQL schema recovery when introspection is disabled (clairvoyance class)
- protobuf and gRPC schema recovery from a capture (pbtk and mitmproxy2swagger are installed and mapped)
- source map reconstruction when the map is absent but the bundle is not
- bundle diffing across deploys to find new endpoints
- CSP analysis and bypass corpus, keyed to framework
- certificate transparency and SAN mining as a recon input

### 12.3 Beyond a normal REA repo

Four things nobody does, and they are the differentiator:

1. **Extraction-first pipeline.** The repo's default workflow is artifact acquisition, then REA analysis,
   then hypothesis, then probe. Not request, then guess.
2. **A web-target profile for REA.** A named set of operations, prompts and wrappers tuned for web
   artifacts, so an agent does not have to rediscover how to use a binary RE tool on a JS bundle.
3. **Cross-artifact reconciliation.** Bundle says endpoint A. Mobile app says endpoint B. HAR shows A and
   C. The repo's job is to reconcile the three and flag what exists but is undocumented.
4. **Findings with a negative control.** Every claim from the extraction layer can be re-verified by a
   second engine, and the repo records which pair was used.

---

## 13. Rival reconciliation protocol (D33)

The answer to "not a single thing left out", made checkable.

### 13.1 Registry

`data/rivals.json`, one record per collection:

```json
{
  "id": "awesome-web-security",
  "repo": "qazbnm456/awesome-web-security",
  "url": "https://github.com/qazbnm456/awesome-web-security",
  "stars": 13962,
  "created": "2017-01-29",
  "last_push": "2026-10-26",
  "harvest_method": "readme_links",
  "harvested_at": "2026-10-26",
  "entries_raw": 0,
  "entries_canonical": 0
}
```

Seed set, from the 2026-10-26 sweep: qazbnm456/awesome-web-security, infoslack/awesome-web-hacking,
0xInfection/Awesome-WAF, vavkamil/awesome-bugbounty-tools, Hack-with-Github/Awesome-Hacking,
enaqx/awesome-pentest, carpedm20/awesome-hacking, devanshbatham/Awesome-Bugbounty-Writeups,
arainho/awesome-api-security, Swordfish-Security/awesome-api-security, JBAhire/awesome-api-security-essentials,
WangYihang/awesome-web-security, skyvanguard/awesome-ai-pentesting, penstriker/awesome-ai-pentest-tools,
spinov001-art/awesome-security-tools-2026, marchev/awesome-ai-web3-security, RandomAdversary/Awesome-AI-Security,
TupleType/awesome-cicd-attacks, EnableSecurity/awesome-rtc-hacking, punkpeye/awesome-mcp-servers,
plus the taxonomy sources already harvested in `web-universe-work`: WSTG, ASVS, VRT, API Top 10, HackTricks,
PayloadsAllTheThings, SecLists, nuclei-templates, Metasploit.

### 13.2 Canonicalization

URL key: lowercase host, strip `www.`, strip trailing slash, strip tracking params, keep path case.
Fallback key when URL is missing: slug of name plus owner.

### 13.3 Disposition

Every rival entry gets exactly one disposition:

| code | meaning |
|---|---|
| MATCHED | already in this repo, by canonical key |
| ADDED | not present, admitted after review |
| DUP | appears twice within the rival itself |
| DEAD | 404, archived, or no push in 3 years |
| NONWEB | real but outside this repo's scope, recorded not dropped |
| LIB | a library, not an agent-drivable artifact |
| KNOW | a writeup, paper or cheatsheet, routed to D27 |
| LOWQ | no description, no README, no usage, or unmaintained toy |
| UNVERIFIABLE | link cannot be resolved |
| HELD | needs a human decision |

### 13.4 The arithmetic that makes the claim

```
entries_canonical = MATCHED + ADDED + DUP + DEAD + NONWEB + LIB + KNOW + LOWQ + UNVERIFIABLE + HELD
```

No rival file is closed until that identity holds and is printed in `data/reconcile/<rival>.summary.json`.
The repo's README publishes the aggregate: rivals reconciled, entries accounted, unresolved HELD count.

A rival entry is never silently dropped. That is the entire point.

---

## 14. The AI-native layer (cross-cutting)

Shipped artifacts, not just links.

| artifact | form | purpose |
|---|---|---|
| `mcps/` | server spec plus client config per server | what an agent can call, and the exact wiring |
| `skills/` | skill files, one per domain | task-shaped instructions an agent loads on demand |
| `prompts/` | prompt packs per phase, with a test case | reproducible agent behaviour, versioned |
| `trees/` | decision trees in JSON, not prose | machine-traversable reasoning |
| `harness/` | runner contracts, budget rules, scope guards | how an agent is allowed to act |
| `evidence/` | finding schema and negative-control protocol | what counts as proof |
| `agents/` | role definitions: recon, hypothesis, exploiter, critic, reporter | multi-agent composition |

Design constraint: every artifact must be usable without reading the Markdown. If it only works after a
human explains it, it is not AI-native, it is a blog post.

---

## 15. Freshness engine

- Every entry: `first_seen`, `last_verified`, `source_url`, `status`.
- Windows: 2026-Q4 (Aug to Oct 2026), 2026, 2024 to 2025, legacy, historical.
- A refresh run re-checks liveness, stars, last push, and release notes, and rewrites the status.
- Staleness is visible, not hidden. An entry unverified for 180 days is flagged.

Dated evidence already in hand for the 2026-Q4 window, so the window is real and not a promise:

| date | thing | why it matters here |
|---|---|---|
| 2026-10-20 | `pathrunner`, DataDog, AWS privesc framework, open source | cloud control plane, S11, new this month |
| 2026-10-19 | STAR Fuzzer, Bright Security, agentic fuzzing that writes its own harnesses | AI builds the harness, not the payloads |
| 2026-10-16 | ThreatBook RedAgents, a pentest-agent aggregator, Singapore, Seoul, Palo Alto | agent-of-agents as a product category |
| 2026-10-15 | Snyk Evo Agentic AppSec | agent writes code, agents attack it, independent verifier |
| 2026-10-15 | Theori white paper on ARTEX plus free detection rules | offense and defense shipped together |
| 2026-10-09 | CrowdStrike on ARTEX used against South Korean financial firms | first widely reported real intrusion using an open-source AI pentest tool |
| 2026-10-07 | Edgescan Atomic, autonomous pentest validation | attacker-path validation, not scanning |
| 2026-10-07 | Hadrian, 40M dollars for autonomous offensive security | market confirmation |
| 2026-10-18 | Prompt Security map, 460 vendors, 14 categories, 29 countries | the vendor universe, machine-readable via JSON API and MCP |
| 2026-07-29 | Pentera AI-native web app pentesting, MCP server, GA in Q4 | incumbent with an MCP surface |

ARTEX is the important one. A Chinese open-source AI pentest tool, used in a real campaign, with
CrowdStrike analysis and a Theori white paper inside two weeks, and it is not in any Western awesome-list.
That single row justifies the regional axis.

---

## 16. Definition of done for the repo

It is not done when the README is long. It is done when:

1. All 37 domain documents exist, each with a required-cell declaration and its own gap ledger.
2. Every rival in the registry has a closed reconciliation with the arithmetic identity holding.
3. Aggregate: every rival entry has a disposition. HELD count published.
4. Every entry has dated provenance and a status.
5. The REA profile exists, with installed, wrapper-needed and build-candidate states, each verified by a
   real command.
6. The AI-native artifacts load without human explanation, proven by a dry run.
7. The defense mirror covers every offensive class with at least one rule or control.
8. Coverage numbers are computed by script from disk and committed as JSON, not typed into prose.

---

## 17. Explicitly out of scope

- Network and internal pentest beyond what gates a web app. That is `byok-cyber-arsenal`.
- Hardware, RF, OT, ICS. Same reason.
- Operational assistance for unauthorized access. Attack classes are described at methodology level, each
  with its authorization requirement.
- Licence bypass and DRM circumvention.
- Stealth malware development, C2 implants, evasion into persistence beyond web app scope.

---

## 18. Decisions, all closed 2026-10-26

1. **Repo name.** `ai-web-arsenal`. Directory `~/ai-web-arsenal`.
2. **Depth.** 10 domains deep now, 27 stubs with declared required-cells. Stubs hold shape, not prose.
3. **REA ambition.** Entries plus wrapper specs plus write the missing operations. The gaps from
   `rea-expansion` are in scope as code, not as a wish list.
4. **Rival reach.** Both. 19 rival repos entry by entry, plus taxonomy reconciliation at test-ID level
   against WSTG, ASVS, VRT, API Top 10, LLM Top 10, ATT&CK and ATLAS.
5. **Bootstrap.** BYO-AI, Arch first. One manifest generates the install scripts, the README tables and
   the MCP configs, so nothing can drift.
