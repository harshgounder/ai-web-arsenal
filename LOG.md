# LOG

One line per step. What ran, what was checked, what was wrong.

## 2026-10-26, scope pass

01. Read local prior art before writing anything: `everything-map/docs/03-completeness-protocol.md`,
    `byok-cyber-arsenal/{README,METHOD,GAPS-TODO,MAP-v5}`, `web-universe-work/{UNIVERSE-SUMMARY,COVERAGE-MATRIX,universe-nodes.json}`,
    `re-arsenal/docs/{COVERAGE-vs-CLAUDE,GAP-MATRIX}`, `rea-expansion/README`.
    Reason: the ecosystem already holds four overlapping assets and the new repo must be orthogonal.
02. Established baseline counts from disk: 58 catalog files, 2,719 entries, 160 categories, 3,995-tool
    corpus, 24 domain briefs, 124 deep-research raws. Quoted only after reading the files that state them.
03. Loaded `parallel-research` skill. Keys live in `~/.dsh/.env`; MCP rows resolve from env.
04. Search wave 1a, rival collections: found qazbnm456 (13,962 stars), Awesome-WAF (7,662),
    infoslack (7,330), vavkamil, Hack-with-Github (123,695), penstriker (created 2026-09-07),
    skyvanguard (has MCP section), Swordfish and JBAhire API lists.
05. Search wave 1b, AI cyber market: Prompt Security map at 460 vendors, 14 categories, 29 countries,
    $14.8B, dated 2026-10-18. ThreatBook RedAgents 2026-10-16. Pentera AI-native web pentest 2026-07-29
    with MCP server. Hadrian $40M 2026-10-07. OpenHack YC F26.
06. Search wave 2, Aug to Oct 2026 releases: ARTEX (Chinese open-source AI pentest tool, used against
    South Korean financial firms late Sept to early Oct 2026, CrowdStrike 2026-10-09, Theori white paper
    plus detection rules 2026-10-15), pathrunner (DataDog 2026-10-20), STAR Fuzzer (Bright 2026-10-19),
    Snyk Evo (2026-10-15), Edgescan Atomic (2026-10-07).
    Also captured: Snyk audit of roughly 4,000 agent skills found at least one flaw in the set, and
    1 in 12 developers running MCP servers had a high or critical finding. Held as a claim to verify
    before it enters the repo.
07. Fetched `startups.prompt.security` full page. Confirmed machine-readable routes: `/api/vendors`,
    `/api/categories`, `/llms.txt`, and an MCP server at `/mcp` with `get_categories`,
    `get_vendors_by_categories`, `get_vendor_details`.
08. Pulled the dataset deterministically instead of reading 460 names by eye:
    `raw/vendors.json` (701,129 bytes, 460 vendors), `raw/categories.json` (4,869 bytes),
    `raw/llms.txt` (5,648 bytes).
09. Rival verification with `gh repo view` on 19 seeds. Two corrections to my own earlier draft:
    - vavkamil/awesome-bugbounty-tools is active (push 2026-10-06), not stale. My "no commit in 2 years"
      came from a third-party tracker page and was wrong.
    - arainho/awesome-api-security is archived (push 2026-05-01). I had it listed as live.
    Both corrected in `SCOPE-v1.md` section 2 with the correction visible.
10. Wrote `SCOPE-v1.md`: 17 target surfaces, 8 agency levels, 16 artifact types, 12 lifecycle stages,
    8 reverse-engineering depths, 7 defense levels, region and platform axes, the cell model, 34 domain
    documents, the REA spine with an installed versus missing table, the rival reconciliation protocol
    with its arithmetic identity, and 5 open decisions.
11. Generated `data/rivals.json` from measured values, 19 records, with tier and defect note per entry.

### Errors and corrections this pass

- First GitHub search call had no `fields` filter and returned 805 KB of unrelated repository text.
  Fix: pin `fields` and smaller `perPage` on every later search.
- Two recalled facts were wrong (step 09). Root cause: trusting a summary page instead of the API.
  Fix: every repo fact comes from `gh repo view` or the git remote, never from a listicle.
- A `find | head` pipe broke on SIGPIPE twice. Cosmetic, no data lost.

### Open, not resolved

- Vendor count moved during the day (446, then 453, then 457, then 460 across cached snapshots). The
  committed number is 460 at 2026-10-18, with the date attached, and it is a snapshot not a constant.
- ARTEX has two independent descriptions (CrowdStrike campaign analysis, Theori white paper) that agree
  on use in a real intrusion but not yet on tool internals. Internals need a direct read of the ARTEX
  repository before any claim about its architecture enters the repo.
- The 4,000-agent-skill audit figure is from one vendor's press release. Needs the primary report.

## 2026-10-26, milestone 2: D11 vertical slice

12. Goal round continued. Applied HELD policy (decision 2026-10-26): entries unique to one source are
    admitted with reason `admitted_unreviewed_tail`. Result: 16,956 admitted / 14,127 excluded /
    212 held / 2 orphan / 1 unresolved. Identity holds.
13. Cloned 6 taxonomy repos into raw/taxonomy. 5 succeeded. OWASP LLM Top 10 failed on fetch-pack
    disconnect, needs a retry or an API path. Sizes look wrong for depth 1 (ASVS 30M, API-Security 140M)
    because these repos carry built assets. Not a problem, only parsed files matter.
14. Probed availability for 7 API tools. Found three packaging traps: PyPI `graphw00f` is 0.0.1
    (placeholder), `graphql-cop` and `graphqlmap` are not on PyPI at all, `batchql` likewise. All four
    went in as `git` channel with an explicit note, not as invented package names.
    `jwt_tool` is AUR only. `schemathesis`, `inql` are pipx. `newman` is npm. `restler` needs dotnet build.
15. Manifest now 50 tools, 0 unresolved.
16. Authored data/domains/D11.json: 24 enriched entries, 9 required cells (6 filled), decision tree,
    8 defense mirror rows, 6 gaps with build candidates, 8 atoms mapped.
17. Wrote scripts/render-domain.py, generic for all 37 domains. Rendered domains/D11-api-protocols.md
    at 280 lines. Markdown is generated, JSON is source of truth.
18. Generated data/domains/D11.index.json: 885 entries are API-relevant but NOT enriched, against 24
    enriched. Ratio 2.6 percent. This is the single most important number in the project: enrichment is
    the bottleneck, not discovery. Keyword matching is over-inclusive (books, blog posts, CVE writeups),
    so the real backlog is smaller, but the order of magnitude stands.
19. Committed as milestone 2.

### Open

- LLM Top 10 repo clone needs a retry.
- D11.index needs a relevance pass to drop books and writeups (should be ~150-250 real candidates).
- The 24:885 ratio means "10 domains deep" needs a stated enriched-target per domain, otherwise deep
  means nothing.

---

## 2026-10-27, the verification pass (after a context compaction)

This entry was written after the fact, from the artifacts, not during the work. Steps 20 onward were
never logged live, so the numbering restarts at V01 to avoid pretending otherwise.

**Why this pass happened.** The user asked for the work to be checked three times independently, because
a context compaction had just happened and a remembered number is not a measured one.

**V01. Ran the verifier.** `scripts/recheck.py`: 33 of 33 passing against `RECHECK.md`. That only proves
the doc and the disk agree. If both were built from the same wrong belief, they would keep agreeing, so
it is not evidence on its own.

**V02. Recounted every headline number with different tools.** `wc -l`, `grep -c`, and shell arithmetic
instead of the Python scripts that produced them. This is what broke the agreement.

**V03. Defect found: the corpus total was quoted as a tool count.** `scripts/merge-identities.py` merged
rows of every kind, so `entries_by_identity` was 21,194 while only 8,845 rows were `kind: tool`. The rest
were 11,712 taxonomy nodes harvested from list headings, 577 social and 247 knowledge rows. The README
called all of it "tool identities". That overstates tools by 2.4x in the one table meant to bound the
claim. Fixed by computing `tool_rows`, `tool_identities` and `rows_by_kind` separately, and by never
quoting the row total as a tool count again.

**V04. Defect found: the image filter matched one shape of image.** It checked file extensions, so 13
shields.io language-toggle badges survived as `kind: tool` rows: "English-Click-yellow", "日本語-クリック-青"
and friends. A filter that matches one shape of a thing is a sample, not a filter. Fixed by matching
badge hosts and `/badge` paths too.

**V05. Near miss: three real tools were hiding behind badge URLs.** Cortex, DollhouseMCP and guardvibe
were stored as `glama.ai/mcp/servers/<owner>/<repo>/badge`. Dropping them with the badges would have lost
real MCP servers while looking like cleanup. They are repaired to their server pages now. 13 dropped,
3 recovered.

**V06. Defect found in the tooling, on this machine.** `verify-tools.py` reported 16 unresolvable tools
including `nmap`, `hashcat` and `pipx`, which is obviously false. Cause: `pacman -Si` fails machine-wide
when any configured repo has a bad signature, and this host has one, `[DEB_Arch_Extra]` from MEGA, whose
database does not validate. That is a local fault dressed up as a packaging gap. The script now falls
back to the Arch package API, records which channel answered, and prints a note when the local lookup is
broken. 0 unresolved again.

**V07. Defect found: 687 rows carried an identifier in their `url` field.** All from one harvested source
that stored a bare `owner/repo`. "Rows carrying a URL" was counting them, and the link checker could never
reach them. Expanded to real GitHub URLs where the shape is unambiguous. One (`skt elecom/bomlens`) is
malformed and is left alone rather than guessed at.

**V08. Defect found in the verifier itself.** The reconciliation identity line printed
`admitted + excluded + held + residue = total` and let 75 orphan rows hide inside the word "residue". It
passed because `identity_holds` was true, not because the arithmetic was shown. It now names all six terms
and sums them out loud: 13,516 + 17,506 + 204 + 71 + 1 = 31,298.

**V09. Defect found in a label.** `build-indexes.py` printed `TOTAL promotable 1439`, which is the figure
before cross-domain dedupe. The real promotable count is 1,419. The printed line now says which stage it
is.

**V10. Determinism check.** Snapshotted SHA-256 for all 189 generated files, re-ran the whole 12-stage
pipeline, diffed. Zero drift. The generator chain is idempotent, which is the property that lets a number
here be trusted at all.

**V11. Read the result back from GitHub.** Not from local git, from `raw.githubusercontent.com`, to confirm
the pushed bytes carry the corrected numbers rather than the local working tree only.

**V12. Fixed a claim about this file.** The README map described LOG.md as "every step, including the
twelve defects". LOG.md stopped at milestone 2 and contained none of them. Rather than quietly soften the
description, this entry exists, and `RECHECK.md` section 8 carries the full table of fourteen.

### Numbers after this pass

```
corpus        21,384 rows = 8,848 tools (8,692 identities) + 11,712 taxonomy + 577 social + 247 knowledge
urls          9,671 rows carry a real http url; 1 holds an unparseable slug
reconcile     31,298 = 13,516 admitted + 17,506 excluded + 204 held + 71 orphan + 1 unresolved
tools         64 in manifest, 0 unresolved, 19 of them resolved through the Arch API fallback
promotable    1,419 after cross-domain dedupe (1,439 before)
verifier      40 checks, 40 pass
determinism   189 generated files, byte identical on rebuild
```

### What this pass teaches

Every defect here made the project look better, not worse, and every one was invisible to reading. The
row total looked like a tool count. The badges looked like tools. The pacman failure looked like missing
packages. The residue looked like zero. The only thing that caught any of it was recomputing the same
number a second way and getting a different answer.

### Open after this pass

- `ln -s` of the contest repo, REA operations and the 50+ bar are still unmet. Unchanged by this pass.
- The `[DEB_Arch_Extra]` repo on this machine still has a bad signature. It only affects `pacman -Si` and
  whatever else validates sync databases. Fix by syncing it, or remove the repo if MEGA is not wanted.
- The 687 repaired rows have never been link-checked, because the link checker ran before they were URLs.
