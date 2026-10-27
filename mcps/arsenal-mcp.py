#!/usr/bin/env python3
"""
arsenal-mcp.py: a stdio MCP server over this repo's data.

Why this exists. The brief asked for an AI-native arsenal, and until now "AI-native" meant markdown an
agent could read and prompts it could follow. A file is not an interface. This exposes the same data as
tools an agent can call, so it can ask "what covers this factor" and get an answer computed from disk
rather than inferring it from prose.

Transport is newline delimited JSON-RPC 2.0 on stdin and stdout, which is what the MCP stdio transport
is. Standard library only except for one optional import: `tools_for` and `claims` parse YAML and need
PyYAML, and without it those two return a message saying so. The other seven tools run on a bare python,
because a tool that needs an install to answer a question is a worse tool than grep.

Tools exposed:

  search_entries     free text over 515 domain entries, returns id, name, role, and whether it has an oracle
  get_entry          one entry by id, complete
  search_patterns    free text over the atlas patterns, with status
  get_pattern        one pattern by id, with its counter and negative control
  coverage           the grade for a factor id, or a lens summary
  gaps               the classified gap, by class or lens
  tools_for          manifest tools matching a term, with the install channel that works
  domains            the domain registry with entry counts and write permission notes
  claims             the prose claims ledger, or one claim by id

Run: python3 mcps/arsenal-mcp.py
Test: python3 mcps/test-mcp.py
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATLAS = ROOT.parent / "web-attack-atlas"
PROTOCOL = "2024-11-05"

# The fields a free text search covers, and the same tuple is used by the test so the two cannot disagree
# about what searching means.
SEARCH_FIELDS = ("id", "name", "role", "preconditions", "oracle", "evades", "note")

_cache = {}


def load_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def entries():
    if "entries" not in _cache:
        out = []
        for f in sorted((ROOT / "data" / "domains").glob("D*.json")):
            if f.stem.endswith(".index"):
                continue
            d = json.loads(f.read_text(encoding="utf-8"))
            for e in d.get("entries", []):
                out.append({**e, "domain": d.get("id"), "domain_title": d.get("title")})
        _cache["entries"] = out
    return _cache["entries"]


def patterns():
    if "patterns" not in _cache:
        out = []
        for f in sorted(ATLAS.glob("waves/*/patterns.jsonl")) if ATLAS.exists() else []:
            for p in load_jsonl(f):
                out.append({**p, "wave": f.parent.name})
        _cache["patterns"] = out
    return _cache["patterns"]


def coverage():
    return load_jsonl(ROOT / "data" / "coverage" / "coverage.jsonl")


def gaps():
    return load_jsonl(ROOT / "data" / "gap" / "classification.jsonl")


def _yaml_or_none():
    """PyYAML is the one thing this server needs that the standard library does not provide, and it is
    needed for two of the nine tools. Making it optional means the other seven work on a bare python,
    which is the property the README claims."""
    try:
        import yaml
        return yaml
    except ImportError:
        return None


def manifest():
    if "manifest" not in _cache:
        y = _yaml_or_none()
        if y is None:
            return None
        _cache["manifest"] = y.safe_load((ROOT / "manifest" / "tools.yaml").read_text(encoding="utf-8"))
    return _cache["manifest"]


def registry():
    return json.loads((ROOT / "data" / "domain-registry.json").read_text(encoding="utf-8"))["domains"]


def claims():
    if "claims" not in _cache:
        y = _yaml_or_none()
        if y is None:
            return []
        _cache["claims"] = y.safe_load((ROOT / "data" / "claims.yaml").read_text(encoding="utf-8"))
    return _cache["claims"].get("claims", [])


def text(s):
    return [{"type": "text", "text": s}]


# ---------------------------------------------------------------- tool implementations

def t_search_entries(a):
    q = (a.get("query") or "").lower()
    limit = int(a.get("limit") or 20)
    rows = []
    for e in entries():
        blob = " ".join(str(e.get(k) or "") for k in SEARCH_FIELDS).lower()
        if q and q not in blob:
            continue
        rows.append(e)
    rows.sort(key=lambda e: (not bool(e.get("oracle")), e.get("domain") or "", e.get("id") or ""))
    out = [{"id": e["id"], "name": e.get("name"), "domain": e.get("domain"),
            "has_oracle": bool(e.get("oracle")), "has_preconditions": bool(e.get("preconditions")),
            "role": (e.get("role") or "")[:160]} for e in rows[:limit]]
    return json.dumps({"matches": len(rows), "shown": len(out), "entries": out}, indent=1)


def t_get_entry(a):
    eid = a.get("id")
    for e in entries():
        if e.get("id") == eid:
            return json.dumps(e, indent=1, ensure_ascii=False)
    return json.dumps({"error": f"no entry {eid!r}", "hint": "use search_entries"}, indent=1)


def _atlas_missing():
    return not (ATLAS / "waves").exists()


def t_search_patterns(a):
    if _atlas_missing():
        return json.dumps({"error": "companion repo not present",
                           "detail": "clone web-attack-atlas beside this repo to search patterns",
                           "path": str(ATLAS)}, indent=1)
    q = (a.get("query") or "").lower()
    limit = int(a.get("limit") or 20)
    rows = []
    for p in patterns():
        blob = " ".join(str(p.get(k) or "") for k in ("title", "target_state", "id")).lower()
        if q and q not in blob:
            continue
        rows.append(p)
    out = [{"id": p["id"], "title": p.get("title"), "status": p.get("status"),
            "target_state": (p.get("target_state") or "")[:100]} for p in rows[:limit]]
    return json.dumps({"matches": len(rows), "shown": len(out), "patterns": out}, indent=1)


def t_get_pattern(a):
    pid = a.get("id")
    for p in patterns():
        if p.get("id") == pid:
            return json.dumps(p, indent=1, ensure_ascii=False)
    return json.dumps({"error": f"no pattern {pid!r}", "hint": "use search_patterns"}, indent=1)


def t_coverage(a):
    cov = coverage()
    fid = a.get("factor")
    lens = a.get("lens")
    if fid:
        for r in cov:
            if r["factor"] == fid:
                return json.dumps(r, indent=1)
        return json.dumps({"error": f"no coverage record for {fid!r}"}, indent=1)
    if lens:
        rs = [r for r in cov if r["lens"] == lens]
        if not rs:
            return json.dumps({"error": f"no lens {lens!r}"}, indent=1)
        lvl = {}
        for r in rs:
            lvl[r["level"]] = lvl.get(r["level"], 0) + 1
        return json.dumps({"lens": lens, "factors": len(rs), "levels": lvl,
                           "covered_l2_plus": lvl.get("L2", 0) + lvl.get("L3", 0)}, indent=1)
    lvl = {}
    for r in cov:
        lvl[r["level"]] = lvl.get(r["level"], 0) + 1
    return json.dumps({"total": len(cov), "levels": lvl,
                       "covered_l2_plus": lvl.get("L2", 0) + lvl.get("L3", 0)}, indent=1)


def t_gaps(a):
    cls = (a.get("class") or "").upper()
    lens = a.get("lens")
    limit = int(a.get("limit") or 30)
    rows = [g for g in gaps()
            if (not cls or g["class"] == cls) and (not lens or g["lens"] == lens)]
    from collections import Counter
    c = Counter(g["class"] for g in gaps())
    return json.dumps({"class_totals": dict(c), "matches": len(rows),
                       "shown": [{"factor": g["factor"], "class": g["class"], "cost": g["cost"],
                                  "reason": g["reason"][:110]} for g in rows[:limit]]}, indent=1)


def t_tools_for(a):
    if manifest() is None:
        return json.dumps({"error": "PyYAML not installed",
                           "detail": "this tool parses manifest/tools.yaml; the other eight tools do not "
                                     "need it. pipx install pyyaml or use a python with yaml present"})
    q = (a.get("query") or "").lower()
    rows = []
    for t in manifest()["tools"]:
        blob = " ".join(str(t.get(k) or "") for k in ("id", "bin", "role", "kind")).lower()
        if q and q not in blob:
            continue
        inst = t.get("install") or []
        rows.append({"id": t["id"], "role": (t.get("role") or "")[:110],
                     "profiles": t.get("profiles") or [],
                     "install": [f"{c['channel']}:{c.get('pkg')}" for c in inst]})
    return json.dumps({"matches": len(rows), "tools": rows[: int(a.get("limit") or 20)]}, indent=1)


def t_domains(a):
    counts = {}
    for e in entries():
        counts[e.get("domain")] = counts.get(e.get("domain"), 0) + 1
    rows = [{"id": d["id"], "title": d.get("title"), "status": d.get("status"),
             "entries": counts.get(d["id"], 0)} for d in registry()]
    if a.get("authored_only"):
        rows = [r for r in rows if r["status"] == "DEEP"]
    return json.dumps({"count": len(rows), "domains": rows}, indent=1)


def t_claims(a):
    if _yaml_or_none() is None:
        return json.dumps({"error": "PyYAML not installed", "detail": "this tool parses data/claims.yaml"})
    cid = a.get("id")
    if cid:
        for c in claims():
            if c.get("id") == cid:
                return json.dumps(c, indent=1)
        return json.dumps({"error": f"no claim {cid!r}"}, indent=1)
    q = (a.get("query") or "").lower()
    rows = [c for c in claims() if not q or q in (c.get("statement") or "").lower()]
    return json.dumps({"matches": len(rows),
                       "claims": [{"id": c.get("id"), "statement": c.get("statement")} for c in rows[:40]]},
                      indent=1)


TOOLS = [
    {"name": "search_entries", "fn": t_search_entries,
     "description": "Search domain entries by name, role or id. Returns whether each has an oracle, so a caller can tell a procedure from a mention.",
     "inputSchema": {"type": "object", "properties": {
         "query": {"type": "string", "description": "substring, case insensitive"},
         "limit": {"type": "integer", "default": 20}}}},
    {"name": "get_entry", "fn": t_get_entry,
     "description": "Fetch one domain entry by id, complete, including preconditions, oracle, evades and driver.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}},
    {"name": "search_patterns", "fn": t_search_patterns,
     "description": "Search the companion atlas patterns by title or target state.",
     "inputSchema": {"type": "object", "properties": {
         "query": {"type": "string"}, "limit": {"type": "integer", "default": 20}}}},
    {"name": "get_pattern", "fn": t_get_pattern,
     "description": "Fetch one atlas pattern by id, including its counter and negative control.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}},
    {"name": "coverage", "fn": t_coverage,
     "description": "The coverage grade for a factor id, or a level summary for a lens, or the whole denominator.",
     "inputSchema": {"type": "object", "properties": {
         "factor": {"type": "string", "description": "for example L07-030"},
         "lens": {"type": "string", "description": "for example L01"}}}},
    {"name": "gaps", "fn": t_gaps,
     "description": "The classified gap. Class I is derivable by writing, II needs a lab, III is unavailable.",
     "inputSchema": {"type": "object", "properties": {
         "class": {"type": "string", "enum": ["I", "II", "III"]},
         "lens": {"type": "string"}, "limit": {"type": "integer", "default": 30}}}},
    {"name": "tools_for", "fn": t_tools_for,
     "description": "Manifest tools matching a term, with the install channel that actually resolves.",
     "inputSchema": {"type": "object", "properties": {
         "query": {"type": "string"}, "limit": {"type": "integer", "default": 20}}}},
    {"name": "domains", "fn": t_domains,
     "description": "The domain registry with entry counts per domain.",
     "inputSchema": {"type": "object", "properties": {"authored_only": {"type": "boolean"}}}},
    {"name": "claims", "fn": t_claims,
     "description": "The prose claims ledger, or one claim by id, so a caller can see what this repo asserts about itself.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}, "query": {"type": "string"}}}},
]

BY_NAME = {t["name"]: t for t in TOOLS}


# ---------------------------------------------------------------- protocol

def handle(req):
    method = req.get("method")
    rid = req.get("id")
    params = req.get("params") or {}

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": PROTOCOL,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "ai-web-arsenal", "version": "2.0"},
            "instructions": ("Query this arsenal rather than reading it. search_entries tells you whether "
                             "an entry has an oracle, which is the difference between a note and a test. "
                             "coverage gives the grade for any factor in the 1,000 factor denominator."),
        }}
    if method in ("notifications/initialized", "initialized"):
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": [
            {"name": t["name"], "description": t["description"], "inputSchema": t["inputSchema"]}
            for t in TOOLS]}}
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        tool = BY_NAME.get(name)
        if not tool:
            return {"jsonrpc": "2.0", "id": rid,
                    "error": {"code": -32602, "message": f"unknown tool {name!r}"}}
        try:
            body = tool["fn"](args)
            return {"jsonrpc": "2.0", "id": rid, "result": {"content": text(body), "isError": False}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": rid,
                    "result": {"content": text(f"{type(e).__name__}: {e}"), "isError": True}}
    if method in ("ping",):
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    if rid is None:
        return None
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"no method {method!r}"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            print(json.dumps({"jsonrpc": "2.0", "id": None,
                              "error": {"code": -32700, "message": "parse error"}}), flush=True)
            continue
        resp = handle(req)
        if resp is not None:
            print(json.dumps(resp), flush=True)


if __name__ == "__main__":
    main()
