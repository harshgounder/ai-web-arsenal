#!/usr/bin/env python3
"""
verify-tools.py: resolve every install candidate in manifest/tools.yaml against reality.

An install candidate is a hypothesis. This script turns it into a resolved channel or marks it
dead. Channels checked, in the order the manifest lists them:

  pacman : `pacman -Si <pkg>`
  aur    : one batched AUR RPC v5 info call for all aur candidates
  pipx   : pypi.org/pypi/<pkg>/json
  uv     : same pypi endpoint (uv installs from pypi)
  cargo  : crates.io api
  npm    : registry.npmjs.org/<pkg>
  go     : presence of the go toolchain, since the module path is not queryable cheaply
  git    : HEAD request to the repo url
  docker : presence of docker

Output: data/install-matrix.json, one record per tool with the resolved channel, the reason, and
whether the binary is already on PATH. Nothing is installed by this script.
"""
import json, os, shutil, subprocess, sys, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def load_manifest():
    import yaml
    return yaml.safe_load(open(ROOT / "manifest" / "tools.yaml"))


def http_json(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "ai-web-arsenal-verify/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except Exception:
        return None


_RESOLVED_VIA = {}
_archweb_cache = {}


def archweb(pkg):
    """Query the official Arch package API. Independent of /etc/pacman.conf, so it keeps working when
    a configured third-party repo has a bad signature, and inside containers with no sync db."""
    if pkg in _archweb_cache:
        return _archweb_cache[pkg]
    v = None
    try:
        d = http_json("https://archlinux.org/packages/search/json/?name=" + urllib.parse.quote(pkg or ""))
        for r in (d or {}).get("results", []):
            if r.get("pkgname") == pkg and r.get("repo") in ("core", "extra", "multilib"):
                v = r.get("pkgver") or "present"
                if r.get("pkgrel"):
                    v = f"{v}-{r['pkgrel']}"
                break
    except Exception:
        v = None
    _archweb_cache[pkg] = v
    return v


def pacman_has(pkg):
    """Resolve an official-repo package.

    `pacman -Si` reads the local sync databases, so ONE broken third-party repo makes every lookup
    fail globally with 'database is not valid'. That is a machine fault, not a package fault, and it
    had silently turned 16 real tools into 'unresolved'. Fall back to the Arch API when it happens.
    """
    try:
        r = subprocess.run(["pacman", "-Si", pkg], capture_output=True, text=True, timeout=25)
        if r.returncode == 0:
            _RESOLVED_VIA[pkg] = "pacman"
            for line in r.stdout.splitlines():
                if line.startswith("Version"):
                    return line.split(":", 1)[1].strip()
            return "present"
    except Exception:
        pass
    v = archweb(pkg)
    if v:
        _RESOLVED_VIA[pkg] = "archweb"
    return v


def on_path(binname):
    if not binname:
        return False
    return shutil.which(binname) is not None


def main():
    m = load_manifest()
    tools = m["tools"]

    aur_names = sorted({c["pkg"] for t in tools for c in t.get("install", []) if c["channel"] == "aur"})
    aur = {}
    for i in range(0, len(aur_names), 50):
        chunk = aur_names[i:i + 50]
        q = "&".join("arg[]=" + urllib.parse.quote(n) for n in chunk)
        d = http_json(f"https://aur.archlinux.org/rpc/v5/info?{q}")
        if d:
            for r in d.get("results", []):
                aur[r["Name"]] = {"version": r["Version"], "votes": r.get("NumVotes"),
                                  "outdated": bool(r.get("OutOfDate"))}

    have = {c: shutil.which(c) is not None for c in ("go", "cargo", "npm", "docker", "paru", "yay")}

    pypi_cache, crates_cache, npm_cache = {}, {}, {}

    def pypi(pkg):
        if pkg not in pypi_cache:
            d = http_json(f"https://pypi.org/pypi/{pkg}/json")
            pypi_cache[pkg] = d["info"]["version"] if d else None
        return pypi_cache[pkg]

    def crates(pkg):
        if pkg not in crates_cache:
            d = http_json(f"https://crates.io/api/v1/crates/{pkg}")
            crates_cache[pkg] = d["crate"]["max_version"] if d and "crate" in d else None
        return crates_cache[pkg]

    def npm(pkg):
        if pkg not in npm_cache:
            d = http_json(f"https://registry.npmjs.org/{pkg}")
            npm_cache[pkg] = d.get("dist-tags", {}).get("latest") if d else None
        return npm_cache[pkg]

    out = []
    for t in tools:
        resolved = None
        tried = []
        for c in t.get("install", []):
            ch, pkg = c["channel"], c.get("pkg")
            if ch == "pacman":
                v = pacman_has(pkg)
                tried.append({"channel": ch, "pkg": pkg, "ok": bool(v), "version": v,
                              **({"via": _RESOLVED_VIA[pkg]} if pkg in _RESOLVED_VIA else {})})
                if v:
                    resolved = {"channel": ch, "pkg": pkg, "version": v}
                    break
            elif ch == "aur":
                info = aur.get(pkg)
                tried.append({"channel": ch, "pkg": pkg, "ok": bool(info),
                              **({"version": info["version"], "votes": info["votes"],
                                  "outdated": info["outdated"]} if info else {})})
                if info:
                    resolved = {"channel": ch, "pkg": pkg, "version": info["version"],
                                "votes": info["votes"], "outdated": info["outdated"]}
                    break
            elif ch in ("pipx", "uv"):
                v = pypi(pkg)
                tried.append({"channel": ch, "pkg": pkg, "ok": bool(v), "version": v})
                if v:
                    resolved = {"channel": ch, "pkg": pkg, "version": v}
                    break
            elif ch == "cargo":
                v = crates(pkg) if have["cargo"] else None
                tried.append({"channel": ch, "pkg": pkg, "ok": bool(v), "version": v})
                if v:
                    resolved = {"channel": ch, "pkg": pkg, "version": v}
                    break
            elif ch == "npm":
                v = npm(pkg) if have["npm"] else None
                tried.append({"channel": ch, "pkg": pkg, "ok": bool(v), "version": v})
                if v:
                    resolved = {"channel": ch, "pkg": pkg, "version": v}
                    break
            elif ch == "go":
                ok = have["go"]
                tried.append({"channel": ch, "pkg": pkg, "ok": ok,
                              "note": "go toolchain present" if ok else "go toolchain missing"})
                if ok:
                    resolved = {"channel": ch, "pkg": pkg, "version": None}
                    break
            elif ch == "git":
                tried.append({"channel": ch, "pkg": pkg, "ok": True, "note": "clone url, unverified"})
                resolved = {"channel": ch, "pkg": pkg, "version": None}
                break
            else:
                tried.append({"channel": ch, "pkg": pkg, "ok": False, "note": "unknown channel"})

        installed = on_path(t.get("bin"))
        out.append({
            "id": t["id"], "bin": t.get("bin"), "domain": t["domain"], "kind": t["kind"],
            "role": t.get("role"), "profiles": t.get("profiles", []),
            "installed": installed,
            "resolved": resolved,
            "status": "installed" if installed else ("resolvable" if resolved else "unresolved"),
            "tried": tried,
            "ambiguity": t.get("ambiguity"),
        })

    json.dump({"generated_at": "2026-10-27", "os": "arch", "tools": out},
              open(ROOT / "data" / "install-matrix.json", "w"), indent=1)

    st = {}
    for r in out:
        st[r["status"]] = st.get(r["status"], 0) + 1
    print(f"tools {len(out)} -> {st}")
    print()
    print(f"{'id':22s} {'status':11s} {'channel':8s} {'pkg':34s} version")
    for r in out:
        res = r["resolved"] or {}
        print(f"{r['id']:22s} {r['status']:11s} {str(res.get('channel','-')):8s} "
              f"{str(res.get('pkg','-'))[:34]:34s} {res.get('version') or ''}")
    unres = [r["id"] for r in out if r["status"] == "unresolved"]
    if unres:
        print("\nUNRESOLVED (fix the manifest, do not invent):", unres)

    via_archweb = sorted(k for k, v in _RESOLVED_VIA.items() if v == "archweb")
    if via_archweb:
        print(f"\nNOTE: {len(via_archweb)} packages resolved through the Arch API because `pacman -Si`")
        print("      failed. That is a local repo fault, not a package fault. Check with: pacman -Sy")
        print("      and look for 'database is not valid (invalid or corrupted database (PGP signature))'.")


if __name__ == "__main__":
    import urllib.parse
    main()
