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
