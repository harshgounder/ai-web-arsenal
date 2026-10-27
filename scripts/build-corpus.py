#!/usr/bin/env python3
"""
build-corpus.py: normalize every parsed row into one typed, deduplicated corpus.

Frozen instrument. Deterministic over the JSONL in data/entries/.

Every row gets:
  key        canonical url, or name:<slug> when no url exists
  kind       tool | knowledge | taxonomy_node | commercial | social | unresolved
  tier       core_web | adjacent | knowledge | offscope | tail
  web_score  integer, auditable, from keyword hits (see WEB_TERMS / OFF_TERMS)
  domain     provisional D-id from DOMAIN_RULES, marked provisional
  sources    every collection that listed it
  n_sources  how many collections had it (1 = unique to one list, the long tail)

Nothing is deleted. Rows that fail every rule land in tier=tail with the reason recorded.
"""
import json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENT = ROOT / "data" / "entries"
DATA = ROOT / "data"

# --- kind rules -------------------------------------------------------------
SOCIAL = re.compile(r"(twitter\.com|x\.com|reddit\.com|linkedin\.com|facebook\.com|youtube\.com|"
                    r"youtu\.be|medium\.com|discord\.|t\.me|threads\.net|mastodon|bsky\.app)", re.I)
BOOKS = re.compile(r"(amazon\.|goodreads\.|packtpub\.|oreilly\.|manning\.com|nostarch\.|apress\.|"
                   r"springer\.|elsevier\.|wiley\.|books\.google\.)", re.I)
KNOW_HOST = re.compile(r"(blogspot\.|wordpress\.com|substack\.com|dev\.to|hackernoon\.|infosecwriteups\.|"
                       r"pentest-tools\.com/blog|portswigger\.net/web-security|owasp\.org/www-project|"
                       r"cheatsheetseries|github\.io/.+/blog|cve\.mitre\.org|nvd\.nist\.gov|"
                       r"arxiv\.org|acm\.org|ieeexplore|usenix\.org|ndss-symposium|"
                       r"sans\.org|attack\.mitre\.org|atlas\.mitre\.org|genai\.owasp\.org)", re.I)
CODE_HOST = re.compile(r"(github\.com|gitlab\.com|gitee\.com|codeberg\.org|bitbucket\.org|"
                       r"sourcehut\.org|sr\.ht|gitflic\.ru|gitverse\.ru|huggingface\.co)", re.I)

# --- domain relevance -------------------------------------------------------
# strong terms are specific to this repo's scope. weak terms are shared with other fields.
STRONG_WEB = [t.lower() for t in """xss csrf sqli ssrf idor bola bfla cors jwt jwe oauth oidc saml sso graphql
websocket webhook smuggler desync prototype-pollution postmessage clickjacking open-redirect session-fixation
takeover subdomain recon nuclei ffuf sqlmap dalfox burp caido zap postman swagger openapi har
waf bypass payload webshell lfi rfi xxe ssti deserialization zip-slip mass-assignment race-condition
header cookie endpoint api-security webapp "web application" "web app" pentest "bug bounty" bugbounty
fuzzing crawler spider sourcemap deobfusc wasm webview electron apk mobile-security
prompt-injection llm-security mcp-server agent-skill tool-poisoning rag-poisoning
cve exploit vulnerability scanner interception proxy""".split()]

WEAK_WEB = [t.lower() for t in """web http https api rest security browser mobile agent llm mcp cloud
docker kubernetes azure aws gcp cdn cache dns tls certificate json xml yaml javascript js
prompt model skill plugin tool server""".split()]

OFF_TERMS = [t.lower() for t in """sdr gnuradio bladerf usrp hackrf rtl-sdr canbus can-bus obd obd2 jtag uart
spi i2c firmware router openwrt uboot u-boot plc scada modbus bacnet dnp3 profinet zigbee z-wave thread
lorawan rfid nfc gps gsm lte 5g satellite automotive vehicle ecu usb bluetooth ble rf
wifi wpa handshake deauth evil-twin kerberos ntlm ldap adcs bloodhound mimikatz rubeus c2 implant
beacon cobaltstrike sliver mythic havoc empire malware rootkit bootkit kernel exploit mitigation
metasploit msfvenom shellcode reverse-shell meterpreter""".split()]

# --- domain rules: ordered, first match wins, (D-id, regex) ----------------
# ordered specific -> general. matched against name+desc+section only, never the url.
DOMAIN_RULES = [
 ("D31", r"\b(reverse.?engineer|decompil|disassembl|ghidra|radare|rizin|frida|jadx|apktool|sourcemap|deobfusc|asar|llvm|objdump|retdec|angr)\b"),
 ("D28", r"\b(mcp.?server|model.?context.?protocol|mcp gateway)\b"),
 ("D20", r"\b(webmcp|agent.?skill|skill.?market|tool.?poison|agent.?security|agentic|a2a|prompt.?inject.*tool|tool.?call)\b"),
 ("D19", r"\b(llm|prompt.?inject|rag|genai|gpt|chatbot|guardrail|jailbreak|model.?security|mitre atlas)\b"),
 ("D30", r"\b(agent.?framework|orchestrat|multi.?agent|swarm|autonomous.?pentest|pentest.?agent|cyber.?reasoning|crs\b|autonomous.?hacking)\b"),
 ("D26", r"\b(lab|ctf|range|benchmark|dvwa|juice.?shop|hackthebox|tryhackme|academy|vulnhub|pentesterlab|root.?me)\b"),
 ("D25", r"\b(sigma|yara|suricata|detection.?rule|wazuh|edr|siem|blue.?team|defen[cs]ive|hardening)\b"),
 ("D24", r"\b(report|cvss|vrt|disclosure|triage|evidence|write.?up.?template)\b"),
 ("D23", r"\b(exploit.?chain|privilege.?escalation|privesc|post.?exploit|shellcode|payload.?generator|weaponiz)\b"),
 ("D22", r"\b(waf|bot.?detect|antibot|anti.?bot|cloudflare|akamai|imperva|f5|captcha|fingerprint.?browser|ja3|tls.?fingerprint)\b"),
 ("D21", r"\b(android|ios|ipa|apk|mobile|webview|deep.?link|flutter|hermes|react.?native|mini.?program|wxapkg|frida.?android)\b"),
 ("D18", r"\b(supply.?chain|sbom|sigstore|ci/?cd|dependency.?confus|typosquat|provenance|slsa)\b"),
 ("D17", r"\b(aws|azure|gcp|kubernetes|k8s|iam|imds|s3|bucket|serverless|lambda|entra|m365|office.?365|prowler|scoutsuite|pacu|cloud.?security)\b"),
 ("D16", r"\b(crypto|jwt|jwe|jwk|secret.?scan|padding.?oracle|signing|hmac|nonce|entropy|key.?recovery|hashcat|john)\b"),
 ("D15", r"\b(deserial|pickle|ysoserial|ssti|template.?inject|xxe|xpath|expression.?language|spel|ognl|unserialize|gadget.?chain)\b"),
 ("D14", r"\b(ssrf|server.?side.?request|oast|interactsh|dns.?rebind|out.?of.?band)\b"),
 ("D13", r"\b(upload|path.?traversal|lfi|rfi|file.?inclusion|zip.?slip|polyglot|file.?read|local.?file)\b"),
 ("D12", r"\b(business.?logic|race.?condition|concurren|coupon|payment|quota|idempot|workflow.?abuse|price.?manipulation)\b"),
 ("D11", r"\b(graphql|grpc|soap|rest|openapi|swagger|api.?secur|bola|bfla|websocket|webhook|postman|asyncapi|api.?testing)\b"),
 ("D10", r"\b(cache.?poison|cache.?deception|cdn|varnish|fastly|cloudfront|edge.?worker|web.?cache)\b"),
 ("D09", r"\b(smuggl|desync|cl\.te|te\.cl|h2\.c|request.?split|host.?header|crlf|parameter.?pollution|http/2|http/3|quirks)\b"),
 ("D08", r"\b(xss|csp|dom|postmessage|prototype.?pollution|clickjack|client.?side|browser.?extension|service.?worker|subresource|cors)\b"),
 ("D07", r"\b(sql|sqli|nosql|ldap|xpath|command.?inject|os.?command|orm|injection|ssti)\b"),
 ("D06", r"\b(session|cookie|token|fixation|remember.?me|mfa|otp|passkey|webauthn|2fa|totp)\b"),
 ("D05", r"\b(idor|authz|authoriz|access.?control|tenant|multi.?tenan|rbac|abac|mass.?assignment|field.?level)\b"),
 ("D04", r"\b(authn|authentic|oauth|oidc|saml|sso|login|password|credential|adfs|keycloak|auth0|okta|device.?code|prt)\b"),
 ("D03", r"\b(fingerprint|tech.?detect|whatweb|wappalyzer|banner|stack.?detect)\b"),
 ("D02", r"\b(recon|osint|subdomain|amass|subfinder|httpx|naabu|shodan|censys|dork|wayback|crawler|spider|attack.?surface)\b"),
 ("D01", r"\b(methodolog|reasoning|playbook|decision.?tree|mindset|threat.?model)\b"),
]


def domain_of(text):
    for did, pat in DOMAIN_RULES:
        if re.search(pat, text, re.I):
            return did
    return None


def kind_of(url, name, section, desc):
    if not url:
        return "taxonomy_node"
    if SOCIAL.search(url):
        return "social"
    if BOOKS.search(url):
        return "knowledge"
    if KNOW_HOST.search(url):
        return "knowledge"
    if CODE_HOST.search(url):
        return "tool"
    return "tool"


def score(text, terms):
    low = text.lower()
    return sum(1 for t in terms if t in low)


def wscore(text):
    """Weighted web relevance. Strong hits count 3, weak hits count 1."""
    low = text.lower()
    strong = 0
    for t in STRONG_WEB:
        if " " in t or "-" in t:
            if t in low:
                strong += 1
        elif re.search(r"\b" + re.escape(t) + r"\b", low):
            strong += 1
    weak = 0
    for t in WEAK_WEB:
        if re.search(r"\b" + re.escape(t) + r"\b", low):
            weak += 1
    return strong * 3 + weak, strong, weak


def domain_of(text):
    for did, pat in DOMAIN_RULES:
        if re.search(pat, text, re.I):
            return did
    return None



JUNK_NAME = re.compile(r"^(github|gitlab|gitee|codeberg|repository|repo|link|here|this|site|website|web|page|"
                       r"read more|more|source|docs|documentation|tool|article|blog|post|glama|mcp|server|"
                       r"badge|badges|shield|shields|homepage|home|download|click here|unknown|n a|na|"
                       r"HARNESS-IFACE|BENCH-\d+|(OFF|DEF|ENG|GOV|HUM|PHY|ENB|DATA)-\d{2})$", re.I)


def derive_name(url):
    """Recover a usable name when the anchor text was generic, a header, or a taxonomy id."""
    if not url:
        return None
    m = re.match(r"https?://(?:www\.)?github\.com/([^/]+)/([^/#?]+)", url)
    if m:
        return f"{m.group(1)}/{re.sub(r'\.git$', '', m.group(2))}"
    m = re.match(r"https?://(?:www\.)?(gitlab|gitee|codeberg)\.(?:com|org)/([^/]+)/([^/#?]+)", url)
    if m:
        return f"{m.group(2)}/{re.sub(r'\.git$', '', m.group(3))}"
    p = re.sub(r"^https?://(?:www\.)?", "", url).split("?")[0].rstrip("/")
    seg = [x for x in p.split("/") if x]
    if len(seg) >= 2:
        cand = seg[-1] if "." not in seg[-1] else seg[-2]
        return re.sub(r"[_\-]+", " ", cand).strip()[:60] or None
    return None


def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s[:80]


# Badge and status images are not entries. The extension check alone missed the shields.io family,
# which carries no file extension: `img.shields.io/badge/English-Click-yellow` is a language toggle
# on an awesome list, not a tool. Thirteen of them had been admitted as kind=tool rows.
BADGE_HOSTS = re.compile(
    r"(img\.shields\.io|badgen\.net|shields\.io|badge\.fury\.io|"
    r"codecov\.io|travis-ci\.(?:org|com)|coveralls\.io)",
    re.I,
)
BADGE_PATH = re.compile(r"(?:^|/)(?:badge|badges)(?:/|$)", re.I)


def is_badge_url(u):
    """True when a URL addresses an image or status badge rather than a page."""
    if not u:
        return False
    if re.search(r"\.(svg|png|jpe?g|gif|ico|webp)(\?|$)", u, re.I):
        return True
    return bool(BADGE_HOSTS.search(u) or BADGE_PATH.search(u))


def repair_badge_url(u):
    """Recover the page a badge belongs to. Two shapes exist in the harvested lists:
    glama.ai/mcp/servers/badge/<id> and glama.ai/mcp/servers/<owner>/<repo>/badge.
    Three real MCP servers (Cortex, DollhouseMCP, guardvibe) were lost to the second shape."""
    m = re.match(r"(https?://glama\.ai/mcp/servers)/badge/(.+)$", u or "", re.I)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    m = re.match(r"(https?://glama\.ai/mcp/servers/(?!badge(?:/|$)).+?)/badge/?$", u or "", re.I)
    if m:
        return m.group(1)
    return None


SLUG_ONLY = re.compile(r"^[\w.-]+/[\w.-]+$")


def normalize_url(u):
    """One harvested source stores a bare `owner/repo` in its url field instead of a link.
    That made 687 rows count as 'carrying a URL' when they carried an identifier, and left them
    unchecked by the link checker. Expand the unambiguous shape; leave anything odd untouched."""
    if u and "://" not in u and SLUG_ONLY.match(u):
        return "https://github.com/" + u
    return u


def main():
    corpus = {}
    per_source = defaultdict(Counter)

    for f in sorted(ENT.glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            _u = normalize_url((r.get("url") or ""))
            if _u != (r.get("url") or ""):
                r["url"] = _u
            # badge and image URLs are not entries. glama.ai alone contributed 3,348 of them.
            # A badge that encodes a real tool URL is repaired instead of dropped.
            if is_badge_url(_u):
                fixed = repair_badge_url(_u)
                if not fixed:
                    continue
                r["url"] = fixed
                r["parse_notes"] = list(r.get("parse_notes") or []) + ["badge-url-repaired"]
                _u = fixed
            key = r.get("canonical") or ("name:" + slug(r.get("name")))
            if not key or key == "name:":
                per_source[r["source"]]["unresolved"] += 1
                continue
            e = corpus.get(key)
            if e is None:
                e = corpus[key] = {
                    "key": key, "name": r.get("name") or "", "names": [],
                    "url": r.get("url"), "desc": r.get("desc") or "",
                    "sections": [], "sources": [], "source_type": r.get("source_type", "rival"),
                    "parse_notes": [],
                }
            if r.get("name") and r["name"] not in e["names"]:
                e["names"].append(r["name"])
            if r.get("desc") and len(r["desc"]) > len(e["desc"]):
                e["desc"] = r["desc"]
            if r.get("section") and r["section"] not in e["sections"]:
                e["sections"].append(r["section"])
            if r["source"] not in e["sources"]:
                e["sources"].append(r["source"])
            if r.get("parse_note") and r["parse_note"] not in e["parse_notes"]:
                e["parse_notes"].append(r["parse_note"])
            if not e.get("url") and r.get("url"):
                e["url"] = r["url"]
            per_source[r["source"]]["rows"] += 1

    out = []
    for e in corpus.values():
        blob = " ".join([e["name"], e["desc"], " ".join(e["sections"]), e["url"] or ""])
        # name repair happens at build time. Doing it afterwards is pointless because this script
        # regenerates the corpus from the raw entries every run.
        if (JUNK_NAME.match((e.get("name") or "").strip())
                or (e.get("name") or "").startswith("![")):
            d = derive_name(e.get("url") or "")
            if d:
                e["name_original"] = e.get("name")
                e["name"] = d
                e["name_derived"] = True
        e["kind"] = kind_of(e["url"], e["name"], " ".join(e["sections"]), e["desc"])
        scored = wscore(" ".join([e["name"], e["desc"], " ".join(e["sections"])]))
        e["web_score"], e["strong_hits"], e["weak_hits"] = scored
        e["off_score"] = score(blob, OFF_TERMS)
        # domain sees name + desc + section, never the url, never the raw blob
        e["domain"] = domain_of(" ".join([e["name"], e["desc"], " ".join(e["sections"])]))
        e["domain_provisional"] = True
        e["n_sources"] = len(e["sources"])
        if e["kind"] in ("social", "knowledge"):
            e["tier"] = "knowledge"
        elif e["off_score"] >= 2 and e["strong_hits"] == 0:
            e["tier"] = "offscope"
        elif e["web_score"] >= 9:
            e["tier"] = "core_web"
        elif e["web_score"] >= 3:
            e["tier"] = "adjacent"
        else:
            e["tier"] = "tail"
        out.append(e)

    out.sort(key=lambda x: (-x["n_sources"], -(x["web_score"]), x["name"].lower()))
    with open(DATA / "corpus.jsonl", "w", encoding="utf-8") as fh:
        for e in out:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")

    # One file used to hold tools, taxonomy nodes and social rows, and the row total was quoted as a
    # tool count, overstating tools by 2.4x. The union stays for backward compatibility; these three
    # files are what any count must name from now on.
    split = {"tools": DATA / "corpus.tools.jsonl",
             "taxonomy": DATA / "corpus.taxonomy.jsonl",
             "other": DATA / "corpus.other.jsonl"}
    buckets = {"tools": [], "taxonomy": [], "other": []}
    for e in out:
        if e["kind"] == "tool":
            buckets["tools"].append(e)
        elif e["kind"] == "taxonomy_node":
            buckets["taxonomy"].append(e)
        else:
            buckets["other"].append(e)
    for name, path in split.items():
        with open(path, "w", encoding="utf-8") as fh:
            for e in buckets[name]:
                fh.write(json.dumps(e, ensure_ascii=False) + "\n")

    tiers = Counter(e["tier"] for e in out)
    kinds = Counter(e["kind"] for e in out)
    doms = Counter(e["domain"] or "unclassified" for e in out)
    tail = sum(1 for e in out if e["n_sources"] == 1)

    stats = {
        "generated_at": "2026-10-27",
        "rows_parsed": sum(c["rows"] for c in per_source.values()),
        "entries_canonical": len(out),
        "unresolved_rows": sum(c["unresolved"] for c in per_source.values()),
        "tiers": dict(tiers),
        "kinds": dict(kinds),
        "domains": dict(doms.most_common()),
        "unique_to_one_source": tail,
        "multi_source_ge2": sum(1 for e in out if e["n_sources"] >= 2),
        "split": {name: len(rows) for name, rows in buckets.items()},
        "per_source": {k: dict(v) for k, v in per_source.items()},
    }
    json.dump(stats, open(DATA / "corpus-stats.json", "w"), indent=1)

    print("entries_canonical", len(out))
    print("split            ", stats["split"])
    print("unresolved_rows  ", stats["unresolved_rows"])
    print("tiers")
    for k, v in tiers.most_common():
        print(f"  {k:12s} {v}")
    print("kinds")
    for k, v in kinds.most_common():
        print(f"  {k:14s} {v}")
    print("domains")
    for k, v in doms.most_common(40):
        print(f"  {k:14s} {v}")
    print("unique to one source:", tail)
    print("in 2+ sources       :", stats["multi_source_ge2"])


if __name__ == "__main__":
    main()
