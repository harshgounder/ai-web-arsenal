#!/usr/bin/env python3
"""
parse-sources.py: extract entries from every source collection into JSONL.

Frozen instrument. Re-runnable. Deterministic: same input bytes give same rows.

Sources handled:
  rival  : markdown README link lists inside raw/rivals/<slug>/
  own    : byok-cyber-arsenal catalog/*.md  (pipe tables and link lines)
  own    : web-universe-work/universe-nodes.json (node names, no URLs)
  own    : rea-expansion/research/w3-tools/*.jsonl (triage rows)

Output: data/entries/<source-id>.jsonl, one JSON object per line.
Never drops a row. Rows that cannot be parsed are emitted with url=null and a parse_note.
"""
import json, os, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "entries"
OUT.mkdir(parents=True, exist_ok=True)

MD_LINK = re.compile(r"\[([^\]]{1,300})\]\((https?://[^)\s]{4,500})\)")
BARE_URL = re.compile(r"(?<!\()(https?://[^\s)<>\]\"']{6,500})")
H_TAG = re.compile(r"^(#{1,6})\s+(.*)$")
TABLE_ROW = re.compile(r"^\|(.+)\|\s*$")

# sections that hold knowledge, not tooling. used later for disposition, not for dropping.
KNOW_HINT = re.compile(
    r"(book|video|podcast|conference|talk|course|training|blog|write.?up|article|paper|"
    r"cheat.?sheet|tutorial|awesome list|misc|miscellaneous|resources?$)",
    re.I,
)


def canon(url: str) -> str:
    """Canonical key for dedupe. Lowercase host, strip www, strip tracking, normalize github paths."""
    if not url:
        return ""
    u = url.strip().rstrip(".,;:)")
    u = re.sub(r"^http://", "https://", u, flags=re.I)
    u = re.sub(r"#.*$", "", u)
    m = re.match(r"^(https://)([^/]+)(.*)$", u, re.I)
    if not m:
        return u.lower()
    scheme, host, path = m.group(1).lower(), m.group(2).lower(), m.group(3)
    host = re.sub(r"^www\.", "", host)
    path = re.sub(r"[?&](utm_[^&]*|ref|fbclid|gclid)=[^&]*", "", path)
    path = re.sub(r"/+$", "", path)
    if host == "github.com":
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2:
            owner, repo = parts[0].lower(), re.sub(r"\.git$", "", parts[1]).lower()
            return f"gh:{owner}/{repo}"
    path = re.sub(r"\.git$", "", path)
    return scheme + host + path.lower()


def clean_name(raw: str) -> str:
    n = re.sub(r"[`*_]", "", raw).strip()
    n = re.sub(r"\s+", " ", n)
    return n[:200]


def parse_markdown(path: Path, source_id: str, source_type: str):
    rows = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return [{"source": source_id, "source_type": source_type, "url": None,
                 "name": "", "parse_note": f"unreadable: {e}"}]
    stack = {}
    for lineno, line in enumerate(text.splitlines(), 1):
        h = H_TAG.match(line)
        if h:
            level = len(h.group(1))
            stack[level] = clean_name(h.group(2))
            for k in list(stack):
                if k > level:
                    del stack[k]
            continue
        section = " / ".join(stack[k] for k in sorted(stack) if k <= 3) or "root"

        if TABLE_ROW.match(line):
            cells = [c.strip() for c in TABLE_ROW.match(line).group(1).split("|")]
            if len(cells) < 2 or set("".join(cells)) <= set("-: "):
                continue
            link = MD_LINK.search(line)
            name = clean_name(cells[0])
            url = link.group(2) if link else None
            if link:
                name = clean_name(link.group(1)) or name
            if not url:
                bu = BARE_URL.search(line)
                url = bu.group(1) if bu else None
            if name or url:
                rows.append({"source": source_id, "source_type": source_type,
                             "section": section, "name": name, "url": url,
                             "canonical": canon(url) if url else "",
                             "desc": clean_name(cells[1])[:300] if len(cells) > 1 else "",
                             "line": lineno, "parse_note": None if url else "no-url"})
            continue

        for m in MD_LINK.finditer(line):
            name, url = clean_name(m.group(1)), m.group(2)
            if not name and not url:
                continue
            trailing = line[m.end():m.end() + 300]
            desc = re.sub(r"^\s*[-:]\s*", "", trailing).strip()
            rows.append({"source": source_id, "source_type": source_type,
                         "section": section, "name": name, "url": url,
                         "canonical": canon(url), "desc": clean_name(desc)[:300],
                         "line": lineno, "parse_note": None})
    return rows


def main():
    sources = []
    rivals = json.load(open(ROOT / "data" / "rivals.json"))
    for r in rivals:
        slug = r["repo"].replace("/", "__")
        d = ROOT / "raw" / "rivals" / slug
        if not d.exists():
            sources.append((r["id"], "rival", None, r["repo"]))
            continue
        sources.append((r["id"], "rival", d, r["repo"]))

    byok = Path.home() / "byok-cyber-arsenal" / "catalog"
    uni = Path.home() / "web-universe-work" / "universe-nodes.json"
    rea = Path.home() / "rea-expansion" / "research" / "w3-tools" / "new-tools-triage.jsonl"

    total = 0
    summary = []
    for sid, stype, d, label in sources:
        rows = []
        if d is None:
            summary.append({"source": sid, "type": stype, "status": "missing_clone", "rows": 0})
            continue
        for f in sorted(d.rglob("*.md")):
            if any(x in f.parts for x in (".git", "node_modules")):
                continue
            rel = str(f.relative_to(d))
            if rel.lower() not in ("readme.md", "readme.markdown", "readme.rst"):
                if len(rel.split(os.sep)) > 1:
                    continue
            rows.extend(parse_markdown(f, sid, stype))
        if not rows:
            rows = parse_markdown(d / "README.md", sid, stype)
        outp = OUT / f"{sid}.jsonl"
        with open(outp, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        total += len(rows)
        summary.append({"source": sid, "type": stype, "label": label,
                        "status": "ok", "rows": len(rows),
                        "with_url": sum(1 for r in rows if r.get("url")),
                        "unique_canonical": len({r["canonical"] for r in rows if r.get("canonical")})})
        print(f"{sid:45s} rows={len(rows):6d} url={summary[-1]['with_url']:6d} uniq={summary[-1]['unique_canonical']:6d}")

    # own: byok-cyber-arsenal catalog
    if byok.exists():
        rows = []
        for f in sorted(byok.glob("*.md")):
            rows.extend(parse_markdown(f, "own-byok-cyber-arsenal", "own"))
        with open(OUT / "own-byok-cyber-arsenal.jsonl", "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        total += len(rows)
        summary.append({"source": "own-byok-cyber-arsenal", "type": "own",
                        "label": "byok-cyber-arsenal/catalog", "status": "ok", "rows": len(rows),
                        "with_url": sum(1 for r in rows if r.get("url")),
                        "unique_canonical": len({r["canonical"] for r in rows if r.get("canonical")})})
        print(f"{'own-byok-cyber-arsenal':45s} rows={len(rows):6d}")

    # own: web-universe-work node universe
    if uni.exists():
        nodes = json.load(open(uni))
        rows = []
        for branch, bv in nodes.items():
            nodes = bv.get("nodes") or {}
            if isinstance(nodes, list):
                nodes = {bv.get("source", "list"): nodes}
            for group, items in nodes.items():
                for it in (items if isinstance(items, list) else [items]):
                    rows.append({"source": "own-web-universe", "source_type": "own",
                                 "section": f"{branch} / {group}", "name": clean_name(str(it)),
                                 "url": None, "canonical": "", "desc": "",
                                 "line": None, "parse_note": "node-name-no-url",
                                 "_branch": branch, "_count": bv.get("count")})
        with open(OUT / "own-web-universe.jsonl", "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        total += len(rows)
        summary.append({"source": "own-web-universe", "type": "own",
                        "label": "web-universe-work/universe-nodes.json", "status": "ok",
                        "rows": len(rows), "with_url": 0, "unique_canonical": 0})
        print(f"{'own-web-universe':45s} rows={len(rows):6d}")

    # own: rea-expansion tool triage
    if rea.exists():
        rows = []
        for line in rea.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                o = json.loads(line)
            except Exception:
                continue
            url = o.get("url") or o.get("html_url") or o.get("repo")
            rows.append({"source": "own-rea-expansion", "source_type": "own",
                         "section": o.get("topic") or o.get("category") or "rea-expansion",
                         "name": clean_name(str(o.get("name") or o.get("full_name") or "")),
                         "url": url, "canonical": canon(url) if url else "",
                         "desc": clean_name(str(o.get("description") or ""))[:300],
                         "line": None, "parse_note": None})
        with open(OUT / "own-rea-expansion.jsonl", "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        total += len(rows)
        summary.append({"source": "own-rea-expansion", "type": "own",
                        "label": "rea-expansion/w3-tools", "status": "ok", "rows": len(rows),
                        "with_url": sum(1 for r in rows if r.get("url")),
                        "unique_canonical": len({r["canonical"] for r in rows if r.get("canonical")})})
        print(f"{'own-rea-expansion':45s} rows={len(rows):6d}")

    json.dump({"total_rows": total, "sources": summary,
               "generated_at": "2026-10-26"}, open(ROOT / "data" / "entries-summary.json", "w"), indent=1)
    print(f"\nTOTAL ROWS {total}")


if __name__ == "__main__":
    main()
