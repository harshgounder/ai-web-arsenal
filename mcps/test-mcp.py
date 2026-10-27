#!/usr/bin/env python3
"""
test-mcp.py: drive the MCP server over stdio the way a client would, and check the answers against disk.

A server that starts is not a server that answers. These tests send real protocol frames and compare the
parsed result against the same data read directly, so a drift between what the server returns and what
the repo contains fails here rather than in an agent's reasoning.

Run: python3 mcps/test-mcp.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "mcps" / "arsenal-mcp.py"
PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")


def session(frames):
    """One process, many frames: the transport is a stream, not a request per process."""
    payload = "\n".join(json.dumps(f) for f in frames) + "\n"
    r = subprocess.run([sys.executable, str(SERVER)], input=payload,
                       capture_output=True, text=True, timeout=120)
    out = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                out.append({"_unparsed": line})
    return out, r.stderr


def by_id(responses, rid):
    for r in responses:
        if r.get("id") == rid:
            return r
    return {}


def content_text(resp):
    try:
        return resp["result"]["content"][0]["text"]
    except Exception:
        return ""


def main():
    frames = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "test", "version": "0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "search_entries", "arguments": {"query": "smuggl", "limit": 5}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
         "params": {"name": "coverage", "arguments": {"factor": "L07-030"}}},
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
         "params": {"name": "gaps", "arguments": {"class": "III", "lens": "L13", "limit": 3}}},
        {"jsonrpc": "2.0", "id": 6, "method": "tools/call",
         "params": {"name": "get_entry", "arguments": {"id": "does-not-exist"}}},
        {"jsonrpc": "2.0", "id": 7, "method": "tools/call",
         "params": {"name": "no_such_tool", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 8, "method": "tools/call",
         "params": {"name": "domains", "arguments": {"authored_only": True}}},
        {"jsonrpc": "2.0", "id": 9, "method": "tools/call",
         "params": {"name": "claims", "arguments": {"id": "C102"}}},
        {"jsonrpc": "2.0", "id": 10, "method": "tools/call",
         "params": {"name": "search_patterns", "arguments": {"query": "race", "limit": 5}}},
    ]
    res, err = session(frames)

    init = by_id(res, 1)
    check("initialize returns a protocol version",
          init.get("result", {}).get("protocolVersion") == "2024-11-05")
    check("initialize names the server", "ai-web-arsenal" in
          str(init.get("result", {}).get("serverInfo", {}).get("name", "")))

    listing = by_id(res, 2)
    names = [t["name"] for t in listing.get("result", {}).get("tools", [])]
    check("tools/list returns nine tools", len(names) == 9, f"got {len(names)}")
    check("every tool has a schema",
          all(t.get("inputSchema", {}).get("type") == "object"
              for t in listing.get("result", {}).get("tools", [])))

    # search agrees with disk
    # same field list the server documents, so the comparison is about the data and not about the query
    fields = ("id", "name", "role", "preconditions", "oracle", "evades", "note")
    on_disk = 0
    for f in (ROOT / "data" / "domains").glob("D*.json"):
        if f.stem.endswith(".index"):
            continue
        for e in json.loads(f.read_text(encoding="utf-8")).get("entries", []):
            blob = " ".join(str(e.get(k) or "") for k in fields).lower()
            if "smuggl" in blob:
                on_disk += 1
    got = json.loads(content_text(by_id(res, 3)) or "{}")
    check("search_entries agrees with disk",
          got.get("matches") == on_disk, f"server {got.get('matches')}, disk {on_disk}")

    cov = json.loads(content_text(by_id(res, 4)) or "{}")
    disk_cov = None
    for line in (ROOT / "data" / "coverage" / "coverage.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip() and json.loads(line)["factor"] == "L07-030":
            disk_cov = json.loads(line)
    check("coverage returns the same grade as the ledger",
          cov.get("level") == disk_cov.get("level") == "L3", f"server {cov.get('level')}")

    gap = json.loads(content_text(by_id(res, 5)) or "{}")
    check("gaps filters by class and lens", gap.get("matches", 0) > 0
          and all(g["class"] == "III" for g in gap.get("shown", [])))

    missing = by_id(res, 6)
    check("a missing id returns an error payload, not a crash",
          json.loads(content_text(missing) or "{}").get("error"))

    bad = by_id(res, 7)
    check("an unknown tool is a protocol error", bad.get("error", {}).get("code") == -32602)

    doms = json.loads(content_text(by_id(res, 8)) or "{}")
    reg = json.loads((ROOT / "data" / "domain-registry.json").read_text(encoding="utf-8"))["domains"]
    authored = sum(1 for d in reg if d.get("status") == "DEEP")
    check("domains authored_only matches the registry", doms.get("count") == authored,
          f"server {doms.get('count')}, registry {authored}")

    claim = json.loads(content_text(by_id(res, 9)) or "{}")
    check("claims returns a real claim with its check", claim.get("id") == "C102" and claim.get("check"))

    atlas_present = (ROOT.parent / "web-attack-atlas" / "waves").exists()
    pats = json.loads(content_text(by_id(res, 10)) or "{}")
    if atlas_present:
        check("search_patterns reaches the atlas", pats.get("matches", 0) > 0)
    else:
        check("search_patterns explains a missing companion instead of returning zero",
              "not present" in json.dumps(pats))

    check("no unparsed output and nothing on stderr", not any("_unparsed" in r for r in res) and not err.strip(),
          err.strip()[:80])

    print(f"\nmcp: {len(PASS) + len(FAIL)} checks, {len(PASS)} pass, {len(FAIL)} fail")
    if not atlas_present:
        print("NOTE: the companion repo is absent, so the pattern search check ran in degraded mode. "
              "Exit 3 means this gate did not fully run.", file=sys.stderr)
        return 3 if not FAIL else 1
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
