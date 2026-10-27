#!/usr/bin/env python3
"""
observe.py: run a lab, record what happened, and refuse to call it observed unless the control is clean.

This is the only script in the repo that produces an L3 record, and it can fail. A lab that produces
duplicates in its negative control is a broken lab, and the result is recorded as INCONCLUSIVE rather
than quietly promoted.

Record shape, appended to data/observations/observations.jsonl:

  {"observation": "obs-001", "lab": "lab-01-race", "factor": "L07-030", "pattern": "W01-0001",
   "observed_at": "2026-10-27T09:12:00", "verdict": "OBSERVED", "oracle": "...",
   "attack": {...}, "negative_control": {...}, "environment": {...}, "sha256": "..."}

Usage:
  python3 scripts/observe.py lab-01-race
  python3 scripts/observe.py --list
  python3 scripts/observe.py --verify      re-run every recorded lab and report agreement
"""
import argparse
import hashlib
import json
import platform
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RANGE = ROOT / "range"
OBS = ROOT / "data" / "observations" / "observations.jsonl"


def labs():
    return sorted(p for p in RANGE.iterdir() if p.is_dir() and (p / "probe.py").exists())


def wait_port(port, timeout=15):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.15)
    return False


def run_lab(lab_dir):
    """Start the target, run the probe, capture its JSON, stop the target."""
    target = lab_dir / "target.py"
    probe = lab_dir / "probe.py"
    port = 8730 + sum(ord(c) for c in lab_dir.name) % 20
    proc = subprocess.Popen([sys.executable, str(target), str(port)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not wait_port(port):
            return None, "target did not listen"
        r = subprocess.run([sys.executable, str(probe), f"http://127.0.0.1:{port}"],
                           capture_output=True, text=True, timeout=180)
        try:
            return json.loads(r.stdout), None
        except Exception:
            return None, f"probe output was not JSON: {r.stdout[-300:]}{r.stderr[-300:]}"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


def existing():
    if not OBS.exists():
        return []
    return [json.loads(l) for l in OBS.read_text(encoding="utf-8").splitlines() if l.strip()]


def record(name, result, raw):
    prior = existing()
    n = sum(1 for o in prior if o.get("lab") == name) + 1
    obs_id = f"obs-{len(prior) + 1:03d}"
    row = {
        "observation": obs_id,
        "lab": name,
        "factor": result.get("factor"),
        "pattern": result.get("pattern"),
        "observed_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "verdict": result.get("verdict"),
        "oracle": result.get("oracle"),
        "attack": result.get("attack"),
        "negative_control": result.get("negative_control"),
        "run": n,
        "environment": {
            "python": platform.python_version(),
            "system": platform.system(),
            "machine": platform.machine(),
            "network": "loopback only, no external traffic",
        },
        "sha256": hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest(),
    }
    OBS.parent.mkdir(parents=True, exist_ok=True)
    with open(OBS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def cmd_list():
    for p in labs():
        print(f"  {p.name}")
    return 0


def cmd_run(names):
    rc = 0
    for name in names:
        d = RANGE / name
        if not d.exists():
            print(f"no such lab: {name}", file=sys.stderr)
            rc = 1
            continue
        print(f"running {name} ...")
        result, err = run_lab(d)
        if err:
            print(f"  FAILED: {err}", file=sys.stderr)
            rc = 1
            continue
        row = record(name, result, result)
        print(f"  {row['verdict']}  factor {row['factor']}  pattern {row['pattern']}  {row['observation']}")
        if row["verdict"] != "OBSERVED":
            print(f"  the control was not clean, so this is not evidence: {row['negative_control']}",
                  file=sys.stderr)
            rc = 1
    return rc


def cmd_verify():
    """Re-run every recorded lab and check the verdicts still hold."""
    seen = {}
    for o in existing():
        seen[o["lab"]] = o
    if not seen:
        print("no observations recorded yet", file=sys.stderr)
        return 1
    bad = 0
    for name, prior in sorted(seen.items()):
        result, err = run_lab(RANGE / name)
        if err:
            print(f"  {name}: could not run ({err})")
            bad += 1
            continue
        same = result.get("verdict") == prior.get("verdict")
        print(f"  {name}: recorded {prior.get('verdict')}, rerun {result.get('verdict')}"
              f"{'' if same else '  MISMATCH'}")
        if not same:
            bad += 1
    return 0 if bad == 0 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("labs", nargs="*")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.list:
        return cmd_list()
    if args.verify:
        return cmd_verify()
    names = args.labs or [p.name for p in labs()]
    return cmd_run(names)


if __name__ == "__main__":
    sys.exit(main())
