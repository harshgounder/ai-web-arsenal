#!/usr/bin/env python3
"""
repair-names.py: derive a usable name for entries whose anchor text was generic.

3,424 of 24,759 corpus entries had a name like "GitHub", "Repository", "Link", "Here" or "glama".
The URL is fine in almost every case, so the name can be recovered rather than dropped: a github
URL yields owner/repo, anything else yields the last meaningful path segment.

Derived names are marked name_derived so a reader can tell a real anchor from a reconstruction.
Run before build-indexes.py and validate-domains.py.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "data" / "corpus.jsonl"
JUNK = re.compile(r"^(github|gitlab|gitee|codeberg|repository|repo|link|here|this|site|website|web|page|"
                  r"read more|more|source|docs|documentation|tool|article|blog|post|glama|mcp|server|"
                  r"homepage|home|download|click here|unknown|n a|na)$", re.I)
# taxonomy ids and table column headers that leaked into the name field
JUNK2 = re.compile(r"^(OFF|DEF|ENG|GOV|HUM|PHY|ENB|DATA)-\d{2}$|^HARNESS-IFACE$|^BENCH-\d+$", re.I)


def derive(url):
    if not url:
        return None
    m = re.match(r"https?://(?:www\.)?github\.com/([^/]+)/([^/#?]+)", url)
    if m:
        return f"{m.group(1)}/{re.sub(r'\.git$', '', m.group(2))}"
    m = re.match(r"https?://(?:www\.)?(gitlab|gitee|codeberg)\.(?:com|org)/([^/]+)/([^/#?]+)", url)
    if m:
        return f"{m.group(2)}/{re.sub(r'\.git$', '', m.group(3))}"
    p = re.sub(r"^https?://(?:www\.)?", "", url).split("?")[0].rstrip("/")
    seg = [s for s in p.split("/") if s]
    if len(seg) >= 2:
        cand = seg[-1] if "." not in seg[-1] else seg[-2]
        return re.sub(r"[_\-]+", " ", cand).strip()[:60] or None
    return None


def main():
    rows = [json.loads(l) for l in P.read_text(encoding="utf-8").splitlines() if l.strip()]
    fixed = 0
    for e in rows:
        n = (e.get("name") or "").strip()
        if not JUNK.match(n) and not JUNK2.match(n) and not n.startswith("!["):
            continue
        d = derive(e.get("url") or "")
        if d and d.lower() != n.lower():
            e["name_original"] = n
            e["name"] = d
            e["name_derived"] = True
            fixed += 1
    P.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in rows) + "\n", encoding="utf-8")
    print(f"derived names for {fixed} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
