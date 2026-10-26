#!/usr/bin/env python3
"""
build-indexes.py: regenerate every domain index with rules that do not match on noise.

Previous version matched the domain pattern against name + description + every section header, which
meant D03 "fingerprint|tech|banner|server" matched the word "server" in all 8,183 rows of
awesome-mcp-servers. The index then claimed 8,136 candidates and called it a backlog.

Rules now:
  - match on name + description only, never section headers
  - per domain, require at least one SPECIFIC term, not a generic one like "server" or "tool"
  - exclude directory, book, social and badge URLs at generation, not later
  - require a description of at least 12 characters
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
E = [json.loads(l) for l in (ROOT / "data" / "corpus.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]

NOISE = re.compile(r"(glama\.ai|mcp\.so|smithery\.ai|pulsemcp\.com|mcpservers\.org|amazon\.|manning\.com|"
                   r"goodreads\.|oreilly\.|packtpub\.|youtube\.com|youtu\.be|medium\.com|twitter\.com|x\.com|"
                   r"reddit\.com|linkedin\.com|facebook\.com|discord\.|t\.me|substack\.com|"
                   r"secjuice\.com|securityweekly\.com|thehackernews\.com|bleepingcomputer\.com|"
                   r"securityweek\.com|darkreading\.com|krebsonsecurity\.com|thehackernews\.com)", re.I)
BAD = re.compile(r"\.(svg|png|jpe?g|gif|ico)(\?|$)", re.I)

P = {
 "D02": r"\b(subdomain|enumeration|crawler|spider|wayback|dork|osint|dns\b|amass|subfinder|httpx|naabu|katana|gau)",
 "D03": r"\b(fingerprint|wappalyzer|whatweb|tech.?detect|banner.?grab)",
 "D04": r"\b(oauth|oidc|saml|sso|auth0|keycloak|okta|mfa|passkey|webauthn|password.?spray)",
 "D05": r"\b(idor|bola|bfla|authz|tenant|rbac|access.?control|privilege.?escal)",
 "D06": r"\b(jwt|session|cookie|token|fixation|otp|totp)",
 "D07": r"\b(sqli|sql.?inject|xss|ssti|xxe|ldap.?inject|command.?inject|deserial|nosql)",
 "D08": r"\b(csp|postmessage|prototype.?pollution|dom.?xss|clickjack|cors|browser.?extension)",
 "D09": r"\b(smuggl|desync|cl\.te|te\.cl|h2c|request.?split|http.?quirks)",
 "D10": r"\b(cache.?poison|cache.?deception|cdn|varnish|fastly|cloudfront|edge.?worker)",
 "D11": r"\b(graphql|grpc|openapi|swagger|rest.?api|api.?secur|bola|bfla|webhook)",
 "D12": r"\b(business.?logic|race.?condition|coupon|payment|quota|idempot|workflow.?abuse)",
 "D13": r"\b(upload|traversal|lfi|rfi|zip.?slip|polyglot|file.?inclusion)",
 "D14": r"\b(ssrf|server.?side.?request|oast|interactsh|dns.?rebind)",
 "D15": r"\b(deserial|ysoserial|pickle|template.?inject|ssti|gadget.?chain)",
 "D16": r"\b(jwt|hashcat|john.?the.?ripper|padding.?oracle|secret.?scan|trufflehog|gitleaks)",
 "D17": r"\b(prowler|scoutsuite|pacu|cloudfox|iam|imds|kubernetes|kube|bucket.?policy|privilege.?escal)",
 "D18": r"\b(sbom|sigstore|slsa|scorecard|dependency.?confus|typosquat|supply.?chain)",
 "D19": r"\b(prompt.?inject|jailbreak|llm.?secur|guardrail|red.?team.?llm|garak|pyrit)",
 "D20": r"\b(tool.?poison|agent.?secur|mcp.?secur|webmcp|agent.?skill)",
 "D21": r"\b(android|apk|ios|ipa|mobile.?secur|frida|jadx|apktool|flutter|webview)",
 "D22": r"\b(waf|antibot|bot.?detect|captcha|tls.?fingerprint|ja3|curl.?impersonate)",
 "D23": r"\b(privilege.?escal|exploit.?chain|pivot|post.?exploit)",
 "D24": r"\b(cvss|epss|sarif|cwe|disclosure|triage|report.?template)",
 "D25": r"\b(sigma|suricata|yara|detection.?rule|wazuh|zeek|falco)",
 "D28": r"(?=.*\b(mcp|model.?context.?protocol)\b)(?=.*\b(secur|attack|scan|audit|vuln|inject|exploit|pwn|red.?team|threat)\b)",
 "D29": r"\b(cli.?tool|command.?line|scanner|fuzzer)",
 "D30": r"\b(agent.?framework|orchestrat|multi.?agent|autonomous.?pentest|pentest.?agent)",
 "D31": r"\b(reverse.?engineer|decompil|disassembl|sourcemap|deobfusc|asar|wasm|ghidra|radare)",
}

def ok(e):
    u = e.get("url") or ""
    n = (e.get("name") or "").strip()
    d = (e.get("desc") or "").strip()
    if not u.startswith("http"): return False
    if BAD.search(u) or NOISE.search(u): return False
    if n.startswith("!["): return False
    if len(d) < 12: return False
    if e.get("kind") not in ("tool",): return False
    return True

tot = 0
print(f"{'dom':5s} {'indexed':>8s}")
for did, pat in P.items():
    rx = re.compile(pat, re.I)
    dom = json.load(open(ROOT / "data" / "domains" / f"{did}.json"))
    enriched = {(e.get("url") or "").rstrip("/").lower() for e in dom["entries"] if e.get("url")}
    hits = []
    for e in E:
        if not ok(e): continue
        if (e.get("url") or "").rstrip("/").lower() in enriched: continue
        blob = (e.get("name") or "") + " " + (e.get("desc") or "")
        if rx.search(blob):
            hits.append({"name": e["name"], "url": e["url"], "tier": e.get("tier"),
                         "n_sources": e.get("n_sources"), "status": "PROMOTABLE"})
    hits.sort(key=lambda x: (-(x["n_sources"] or 0), x["name"] or ""))
    json.dump({"domain": did, "generated_at": "2026-10-27", "rule": "name+desc only, specific terms, noise excluded",
               "enriched": len(dom["entries"]), "indexed_not_enriched": len(hits), "entries": hits},
              open(ROOT / "data" / "domains" / f"{did}.index.json", "w"), indent=1)
    tot += len(hits)
    print(f"{did:5s} {len(hits):8d}")
print(f"\nTOTAL promotable {tot}")
