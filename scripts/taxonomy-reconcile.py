#!/usr/bin/env python3
"""
taxonomy-reconcile.py: map every test ID from the six taxonomies onto the 16 atoms.

Sources and where they come from on disk:
  WSTG 131      ~/web-universe-work/universe-nodes.json  (parsed from OWASP/wstg)
  ASVS          ~/web-universe-work/universe-nodes.json  (parsed from OWASP/ASVS)
  VRT           raw/taxonomy/bugcrowd_vulnerability-rating-taxonomy/vulnerability-rating-taxonomy.json
  API Top 10    raw/taxonomy/OWASP_API-Security/editions/2023/en/0xa*.md
  ATLAS         raw/taxonomy/mitre-atlas_atlas-data/dist/ATLAS.yaml
  LLM Top 10    declared below, count asserted

Output: data/taxonomy/<name>.json and data/taxonomy-coverage.json

The point: if every taxonomy item maps to an atom, and atoms are the spine of the atlas, then the atlas
covers the taxonomies by construction. Unmapped items are the gap report, not a rounding error.
"""
import json, re, sys
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
OUT = ROOT / "data" / "taxonomy"
OUT.mkdir(parents=True, exist_ok=True)

ATOM_RULES = [
    ("A01", r"(inject|sql|xss|script|template|command|deserial|ldap|xpath|expression language|eval|code exec"
            r"|xxe|file inclusion|response splitting|header injection|log injection|crlf|ssti|orm)"),
    ("A02", r"(authoriz|authz|access control|idor|bola|bfla|privilege|permission|tenant|escalat"
            r"|direct object reference|takeover|role definition|shared link|forged request"
            r"|insecure direct|missing.*check|bypass.*control)"),
    ("A03", r"(authentic|authn|identity|impersonat|token|session|saml|oauth|oidc|sso|credential|password"
            r"|mfa|cookie|logout|security question|user enumeration|account enumeration|username policy"
            r"|remember me|password policy|weak password|credential transport)"),
    ("A04", r"(state|race|replay|ordering|concurren|double|idempot|sync|version|incubated)"),
    ("A05", r"(type|pars|mass assignment|coercion|input valid|schema|format string|overflow|null|encoding"
            r"|verb tampering|parameter pollution|duplicate|malformed)"),
    ("A06", r"(path|traversal|host header|routing|normaliz|namespace|redirect|url parsing|smuggl|desync"
            r"|parameter pollution|response splitting|relative path)"),
    ("A07", r"(resource|rate limit|exhaust|denial|quota|consum|brute force|lock ?out|flood|dos\b"
            r"|unrestricted|amplification)"),
    ("A08", r"(disclos|exposure|leak|information|verbose|debug|error|metadata|listing|enumerat"
            r"|fingerprint|attack surface|entry point|architecture|cache weakness|caching|directory"
            r"|source code|comment|backup|old file|unreferenced)"),
    ("A09", r"(crypto|encrypt|cipher|hash|signature|random|key management|tls\b|ssl\b|certificate"
            r"|padding oracle|transport layer security|hsts|weak algorithm|entropy|iv\b)"),
    ("A10", r"(business logic|logic|workflow|abuse|circumvent|integrity check|process timing"
            r"|forge request|limit.*function|anti.?automation|unexpected|sequence)"),
    ("A11", r"(supply|depend|package|component|vulnerable|outdated|sbom|third party|unmaintained"
            r"|known vulnerab|patch level)"),
    ("A12", r"(timing|race condition|toctou|concurren|atomic|parallel|simultaneous)"),
    ("A13", r"(side channel|timing attack|oracle|inference|observable)"),
    ("A14", r"(phish|social engineer|human|awareness|training|support|impersonat.*user|helpdesk)"),
    ("A15", r"(misconfig|config|default|header|setting|deploy|environment|hardening"
            r"|http method|strict transport|cross domain policy|csp\b|content security policy"
            r"|security header|ria\b|permission|platform|network infrastructure|application platform)"
            r"|(file extension|admin interface|cloud storage)"),
    ("A16", r"(prompt|llm|model|agent|rag\b|jailbreak|tool use|embedding|training data|ai\b|ml\b"
            r"|guardrail|memory|vector)"),
]

DOMAIN_RULES = [
    ("D19", r"(llm|prompt|model|ai |rag|agent)"),
    ("D20", r"(agent|mcp|tool use|skill)"),
    ("D11", r"(api|graphql|grpc|rest|webhook)"),
    ("D04", r"(authentic|authn|oauth|saml|sso|password|credential|mfa)"),
    ("D05", r"(authoriz|authz|idor|bola|bfla|access control|tenant|privilege)"),
    ("D06", r"(session|token|cookie|jwt|remember)"),
    ("D07", r"(inject|sql|ldap|xpath|command|template|ssti)"),
    ("D08", r"(xss|dom|client|cors|clickjack|postmessage|csp)"),
    ("D09", r"(smuggl|desync|host header|http method|parameter pollution)"),
    ("D10", r"(cache|cdn|proxy)"),
    ("D12", r"(business logic|race|concurren|workflow)"),
    ("D13", r"(upload|file|path|traversal)"),
    ("D14", r"(ssrf|server side request)"),
    ("D15", r"(deserial|template|xxe)"),
    ("D16", r"(crypto|secret|key|certificate|hash)"),
    ("D17", r"(cloud|aws|azure|iam|container|kubernetes)"),
    ("D18", r"(supply|depend|component|ci/cd|build)"),
    ("D21", r"(mobile|android|ios)"),
    ("D22", r"(waf|bot|rate)"),
    ("D02", r"(recon|enumeration|fingerprint|discover|information gathering)"),
    ("D03", r"(fingerprint|technology|server)"),
]


def atoms_of(text):
    t = text.lower()
    return [aid for aid, pat in ATOM_RULES if re.search(pat, t)]


def domain_of(text):
    for did, pat in DOMAIN_RULES:
        if re.search(pat, text, re.I):
            return did
    return None


def rows(name, items, id_fmt=None):
    out = []
    for i, (ident, title) in enumerate(items):
        a = atoms_of(title)
        out.append({"id": ident, "title": title, "atoms": a,
                    "atom_complete": bool(a), "domain": domain_of(title)})
    rec = {"source": name, "count": len(out),
           "mapped": sum(1 for r in out if r["atom_complete"]),
           "unmapped": sum(1 for r in out if not r["atom_complete"]),
           "items": out}
    json.dump(rec, open(OUT / f"{name}.json", "w"), indent=1)
    print(f"{name:12s} items={rec['count']:5d} mapped={rec['mapped']:5d} unmapped={rec['unmapped']:4d}")
    return rec


def get_wstg():
    u = json.load(open(HOME / "web-universe-work" / "universe-nodes.json"))
    b = u["wstg"]; items = []
    for grp, names in (b.get("nodes") or {}).items():
        gnum = grp.split("-")[0]
        gcode = re.sub(r"[^A-Z]", "", grp.split("-", 1)[1].upper())[:4] or "GEN"
        for nm in names:
            m = re.match(r"(\d+)-(.*)", nm)
            if m and "overview" not in m.group(2).lower():
                items.append((f"WSTG-{gcode}-{m.group(1)}", m.group(2)))
            else:
                items.append((f"WSTG-{gcode}-XX", nm))
    return items


ASVS_CHAPTERS = [
    ("V1", "Encoding and Sanitization"), ("V2", "Validation and Business Logic"),
    ("V3", "Web Frontend Security"), ("V4", "API and Web Service"),
    ("V5", "File Handling"), ("V6", "Authentication"),
    ("V7", "Session Management"), ("V8", "Authorization"),
    ("V9", "Self-contained Tokens"), ("V10", "OAuth and OIDC"),
    ("V11", "Cryptography"), ("V12", "Secure Communication"),
    ("V13", "Configuration"), ("V14", "Data Protection"),
    ("V15", "Secure Coding and Architecture"), ("V16", "Security Logging and Error Handling"),
    ("V17", "WebRTC"),
]


def get_asvs():
    """CORRECTION 2026-10-26: the '240' figure that has been circulating in this project is a count of
    markdown FILES in the ASVS repo, not requirements. Only 49 are under en/ and those are prefaces and
    headers. Requirement level reconciliation needs the 5.0 chapter content, which failed to clone twice.
    Until then this is chapter level, and the count is 17, not 240. Stated plainly rather than dropped."""
    return [(f"ASVS-{c}", t) for c, t in ASVS_CHAPTERS]


def get_vrt():
    d = json.load(open(ROOT / "raw/taxonomy/bugcrowd_vulnerability-rating-taxonomy/vulnerability-rating-taxonomy.json"))
    items = []
    def walk(node, idpath, namepath):
        nid = node.get("id", "?")
        name = node.get("name", nid)
        ch = node.get("children") or []
        if not ch:
            # VRT leaves are qualifiers under a vulnerability ("Long Timeout", "Over HTTP").
            # The testable unit is the full path, so matching sees the whole context.
            items.append(("-".join(idpath + [nid]), " > ".join(namepath + [name])))
        for c in ch:
            walk(c, idpath + [nid], namepath + [name])
    for cat in d["content"]:
        walk(cat, [], [])
    return items


def get_api10():
    d = ROOT / "raw/taxonomy/OWASP_API-Security/editions/2023/en"
    items = []
    for f in sorted(d.glob("0xa*.md")):
        m = re.match(r"0xa([0-9a])-(.*)\.md", f.name)
        if m:
            n = m.group(1)
            num = 10 if n == "a" else int(n)
            items.append((f"API{num}:2023", m.group(2).replace("-", " ").title()))
    return items


def get_atlas():
    import yaml
    y = yaml.safe_load(open(ROOT / "raw/taxonomy/mitre-atlas_atlas-data/dist/ATLAS.yaml"))
    items = []
    for k, v in y.items():
        if k == "techniques" and isinstance(v, list):
            for t in v:
                if isinstance(t, dict) and str(t.get("id", "")).startswith("AML.T"):
                    items.append((t["id"], t.get("name", "")))
    if not items:
        # yaml may be nested under matrices; fall back to a regex scan
        txt = open(ROOT / "raw/taxonomy/mitre-atlas_atlas-data/dist/ATLAS.yaml").read()
        for m in re.finditer(r"- id: (AML\.T\d{4})\s*\n\s*name: (.+)", txt):
            items.append((m.group(1), m.group(2).strip().strip("'")))
    return items


def get_llm10():
    # stable, published list. count asserted, not inferred.
    names = [
        ("LLM01", "Prompt Injection"), ("LLM02", "Sensitive Information Disclosure"),
        ("LLM03", "Supply Chain"), ("LLM04", "Data and Model Poisoning"),
        ("LLM05", "Improper Output Handling"), ("LLM06", "Excessive Agency"),
        ("LLM07", "System Prompt Leakage"), ("LLM08", "Vector and Embedding Weaknesses"),
        ("LLM09", "Misinformation"), ("LLM10", "Unbounded Consumption"),
    ]
    return names


def main():
    recs = {}
    recs["wstg"] = rows("wstg", get_wstg())
    recs["asvs"] = rows("asvs", get_asvs())
    recs["vrt"] = rows("vrt", get_vrt())
    recs["api_top10"] = rows("api_top10", get_api10())
    recs["atlas"] = rows("atlas", get_atlas())
    recs["llm_top10"] = rows("llm_top10", get_llm10())

    tot = sum(r["count"] for r in recs.values())
    mapped = sum(r["mapped"] for r in recs.values())
    atom_hits = Counter()
    for r in recs.values():
        for i in r["items"]:
            for a in i["atoms"]:
                atom_hits[a] += 1
    dom_hits = Counter(r["domain"] or "unmapped" for rec in recs.values() for r in rec["items"])

    cov = {
        "generated_at": "2026-10-26",
        "sources": {k: {"count": v["count"], "mapped": v["mapped"], "unmapped": v["unmapped"]}
                    for k, v in recs.items()},
        "total_items": tot, "mapped": mapped,
        "coverage_pct": round(100 * mapped / tot, 1) if tot else 0,
        "atom_hits": dict(atom_hits.most_common()),
        "atoms_unused": [f"A{i:02d}" for i in range(1, 17) if f"A{i:02d}" not in atom_hits],
        "domain_hits": dict(dom_hits.most_common()),
    }
    json.dump(cov, open(ROOT / "data" / "taxonomy-coverage.json", "w"), indent=1)
    print(f"\nTOTAL {tot} items, {mapped} mapped to at least one atom, {cov['coverage_pct']}%")
    print("atoms never triggered:", cov["atoms_unused"] or "none")
    print("atom distribution:", dict(atom_hits.most_common()))


if __name__ == "__main__":
    main()
