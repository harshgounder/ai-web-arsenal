# BOOTSTRAP: bring your AI, get a working arsenal

The promise: you already have an AI, a shell, and Arch. Two commands and you have the toolkit, the MCP
servers wired, the prompt packs in place, and a smoke test that tells you what actually works. No
hunting through READMEs, no guessing package names.

Everything in this file is **generated** from `manifest/tools.yaml` through
`scripts/verify-tools.py` and `scripts/gen-bootstrap.py`. If a package name here is wrong, the manifest
is wrong. Nothing is typed by hand into a script.

---

## 1. The 10 minute path

```bash
git clone https://github.com/<you>/ai-web-arsenal
cd ai-web-arsenal
bash bootstrap/00-prereqs.sh          # base-devel, git, AUR helper, uv
bash bootstrap/15-install-minimal.sh  # 13 tools, the ones you actually use on day one
bash bootstrap/90-verify.sh           # proves every binary runs
```

Dry run first if you prefer to see what it does:

```bash
DRY=1 bash bootstrap/15-install-minimal.sh
```

The installer refuses to run as root, never pipes curl to sh, and is idempotent. Running it twice is safe.
Every run logs to `bootstrap/logs/`.

---

## 2. What you get per profile

| profile | script | tools | what it is for |
|---|---|---|---|
| minimal | `15-install-minimal.sh` | 13 | start today: recon, fuzz, scan, intercept, browser |
| recon | `20-install-recon.sh` | 12 | surface mapping and content discovery |
| web | `25-install-web.sh` | 18 | requests, fuzzing, injection, browser driving |
| api | `30-install-api.sh` | 8 | REST, GraphQL, gRPC, spec recovery |
| mobile | `35-install-mobile.sh` | 3 | the client behind the web app |
| re | `40-install-re.sh` | 4 | REA spine and binary work |
| all | `45-install-all.sh` | 43 | everything |

Counts are written by the generator. If the count and the script disagree, the count is wrong.

Install channels actually resolved on 2026-10-26 against this machine: pacman 19, AUR 16, pipx 6,
git 2. Four were already present. Zero unresolved.

---

## 3. Why Arch first, and what if you are not on Arch

Arch is the shortest path because the AUR already carries the ProjectDiscovery tools, `nuclei-bin`,
`httpx-bin`, `kiterunner-bin` and `android-apktool`, which are the packages that are annoying elsewhere.
On Arch that is one command each. On Debian you are building from source or adding a third-party repo.

Non-Arch users: every tool in `manifest/tools.yaml` carries a distro-neutral fallback in its `install:`
list (go, cargo, npm, pipx, uv, or git). `docs/INSTALL-OTHER.md` renders the same matrix as plain
commands per channel, generated from the same file, so it cannot drift either.

Deliberately not automated: BlackArch. It replaces the whole repo stack and conflicts with CachyOS
repos. If you want it, install it yourself and do not mix.

---

## 4. Wiring MCP servers

The AI layer is the point. These are the servers worth wiring, in order.

### 4.1 REA, the extraction spine

REA is the reason this repo can start at the artifact instead of the request. It is an MCP server, so any
MCP-capable client can use it.

Requirements: Node 22.19+, 24.11+ or 26+. Not 23, not 25.

Generic stdio config (`mcpServers` shape, works in Claude Desktop, Cursor, most clients):

```json
{
  "mcpServers": {
    "rea": {
      "command": "npx",
      "args": ["-y", "rea-agents@6.4.0", "mcp"]
    }
  }
}
```

Claude Code:

```bash
claude mcp add rea -- npx -y rea-agents@6.4.0 mcp
```

Hermes Agent:

```bash
hermes plugins install rea
hermes plugins enable rea
```

What it gives you on a web target, and why it matters here:

| call | web use |
|---|---|
| `analyze_web_bundle` | chunk graph, route and endpoint candidates, vendor fingerprints, source maps |
| `export_web_scripts` | the actual JS bytes, with a manifest |
| `inspect_web_network_capture` | HAR, mitmproxy dump, SAZ, qlog |
| `trace_web_source_location` | generated position back to original source |
| `recover_javascript_sources` | deobfuscated modules |
| `discover_webmcp_tools` | page-registered WebMCP tool inventory |
| `capture_browser_scenario` | controlled scenario with network and storage capture |
| `inspect_android_package` | the mobile client, class and resource level |
| `inspect_wasm_artifact` | WASM imports, exports, WAT |

DSH profile row (streamable-http and stdio both supported):

```yaml
- id: mcp-rea
  name: "@deepseek-ai/dsh-mcp-client"
  config:
    transport: stdio
    command: npx
    args: ["-y", "rea-agents@6.4.0", "mcp"]
    toolCallTimeoutMs: 300000
    failOnStartupError: false
```

### 4.2 Everything else

MCP servers are catalogued in `D28` and in `mcps/`. The rule for this repo: a server is listed only with
a working config and a stated capability, never as a name and a link. Servers whose repo I could not
verify are marked `UNVERIFIED` and stay out of the generated configs.

---

## 5. First 15 minutes with a target, in order

This is the pipeline the repo is built around: artifact first, hypothesis second.

```bash
# 1. capture, do not poke. browse the target once through the proxy.
mitmdump -w flows.mitm

# 2. ask your AI, with REA wired:
#    "inspect flows.mitm, list every endpoint and its auth requirement,
#     flag any endpoint the UI never calls"
#    -> rea inspect_web_network_capture, then analyze_web_bundle on the host

# 3. pull the client artifacts
#    -> export_web_scripts, trace_web_source_location, recover_javascript_sources
#    -> for the mobile client: inspect_android_package

# 4. only now form hypotheses
#    -> D01 decision trees, D36 grammar, per-stack playbook

# 5. prove, with an oracle, or drop it
#    -> D24 evidence schema, negative control required
```

Step 2 and 3 are the ones most writeups skip, and they are why the findings hold up better than a
scanner's.

---

## 6. Prompt packs

`prompts/` holds versioned packs, one per phase. Each pack has the prompt, the expected output shape, and
a worked example so you can tell if your model is doing the job or riffing.

| pack | use |
|---|---|
| `recon-capture.md` | turn a capture into an endpoint and auth inventory |
| `bundle-teardown.md` | turn a JS bundle into routes, secrets candidates, signing logic |
| `hypothesis.md` | turn a stack profile into ranked, testable hypotheses |
| `prove-it.md` | force an oracle, a control, and a falsification attempt |
| `report.md` | finding to report, with the evidence the schema demands |
| `critic.md` | adversarial review of another agent's finding |

The critic pack is the one that fixes AI pentesting. A single agent that both finds and confirms will
confirm its own hallucinations. A second agent whose only job is to break the first one's finding does
not.

---

## 7. Verify, do not trust

```bash
bash bootstrap/90-verify.sh
```

It runs each tool's real version command and reports three states: present and working, present but the
command failed, and not on PATH. Anything in the third state simply means that profile is not installed,
which is fine.

The matrix behind it is `data/install-matrix.json`, regenerated by:

```bash
python3 scripts/verify-tools.py
```

That script installs nothing. It only asks pacman, the AUR RPC, PyPI, crates.io, npm and the git remote
what exists, and records the answer with a date. Re-run it whenever a tool goes missing, because AUR
packages do get dropped.

---

## 8. Troubleshooting the things that actually break

| symptom | cause | fix |
|---|---|---|
| `httpx` installs a python library | AUR `httpx` is the python package | use `httpx-bin`, already encoded in the manifest |
| `apktool` not found in AUR | it is named `android-apktool` | already encoded |
| `kiterunner` not found | it is `kiterunner-bin` | already encoded |
| AUR build fails on a stale key | pacman keyring | `sudo pacman -Sy archlinux-keyring` |
| REA will not start | Node 23 or 25 | install Node 22 LTS or 24 |
| no `paru` | fresh Arch | `00-prereqs.sh` builds it, or use `yay` |
| scanner silence | rate limiting or WAF | that is data, record it, do not raise the rate |

---

## 9. What this bootstrap deliberately does not do

- It does not install BlackArch or replace your repo stack.
- It does not install commercial tooling (Burp Pro, Caido Pro, IDA, Binary Ninja). Those are listed in
  the domain docs with the free alternative named next to them.
- It does not add API keys, tokens or credentials anywhere. The AI layer uses the model you already pay
  for.
- It does not run anything against a target. Scope and authorization are yours, and `D24` requires you to
  record them before the first request.
