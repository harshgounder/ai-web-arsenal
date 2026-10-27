#!/usr/bin/env python3
"""
webauthn-attestation.py: parse a WebAuthn attestation object and its authenticator data.

Why this exists. D31 gap eight. Passkey and attestation semantics were a reference entry with no reader,
so a captured registration response could not be inspected here at all. That is the artefact that decides
which authenticator produced a credential, whether user verification actually happened, and whether the
relying party id matches the origin.

What this does: CBOR decodes the attestation object, splits it into fmt, attStmt and authData, then parses
authData into rpIdHash, flags, signCount, AAGUID, credential id and the COSE public key. It reports the
flags as booleans because that is the field people get wrong.

What it does not do: verify any signature, validate the attestation chain, or decide whether a policy
should accept the authenticator. Those are trust decisions and they need the relying party's policy,
which this tool does not have.

Usage:
  python3 rea-ops/webauthn-attestation.py response.json
  python3 rea-ops/webauthn-attestation.py --b64 attestationObjectBase64
"""
import argparse
import base64
import json
import struct
import sys


# ---------------------------------------------------------------- CBOR, definite lengths only

def _read_len(buf, i, info):
    if info < 24:
        return info, i
    if info == 24:
        return buf[i], i + 1
    if info == 25:
        return struct.unpack_from(">H", buf, i)[0], i + 2
    if info == 26:
        return struct.unpack_from(">I", buf, i)[0], i + 4
    if info == 27:
        return struct.unpack_from(">Q", buf, i)[0], i + 8
    raise ValueError(f"indefinite or reserved length {info}")


def cbor_decode(buf, i=0):
    if i >= len(buf):
        raise ValueError("cbor ended early")
    b = buf[i]
    major, info = b >> 5, b & 0x1F
    i += 1
    if major == 0:
        v, i = _read_len(buf, i, info)
        return v, i
    if major == 1:
        v, i = _read_len(buf, i, info)
        return -1 - v, i
    if major in (2, 3):
        n, i = _read_len(buf, i, info)
        raw = buf[i:i + n]
        i += n
        return (raw if major == 2 else raw.decode("utf-8", errors="replace")), i
    if major == 4:
        n, i = _read_len(buf, i, info)
        out = []
        for _ in range(n):
            v, i = cbor_decode(buf, i)
            out.append(v)
        return out, i
    if major == 5:
        n, i = _read_len(buf, i, info)
        out = {}
        for _ in range(n):
            k, i = cbor_decode(buf, i)
            v, i = cbor_decode(buf, i)
            out[k if isinstance(k, str) else k.hex() if isinstance(k, bytes) else str(k)] = v
        return out, i
    if major == 6:
        _tag, i = _read_len(buf, i, info)
        return cbor_decode(buf, i)
    if major == 7:
        if info == 20:
            return False, i
        if info == 21:
            return True, i
        if info == 22:
            return None, i
        raise ValueError(f"cbor simple value {info}")
    raise ValueError(f"cbor major type {major}")


# ---------------------------------------------------------------- authData

def jsonable(v):
    """CBOR maps carry byte strings, which JSON cannot represent. Convert with a visible marker so a
    reader can tell a hex value from a text value rather than seeing an ambiguous string."""
    if isinstance(v, (bytes, bytearray)):
        return {"bytes_hex": bytes(v).hex()}
    if isinstance(v, dict):
        return {k: jsonable(x) for k, x in v.items()}
    if isinstance(v, list):
        return [jsonable(x) for x in v]
    return v


FLAGS = [
    (0x01, "user_present"),
    (0x04, "user_verified"),
    (0x08, "backup_eligible"),
    (0x10, "backup_state"),
    (0x40, "attested_credential_data"),
    (0x80, "extension_data"),
]


def parse_auth_data(auth):
    if len(auth) < 37:
        raise ValueError(f"authData is {len(auth)} bytes, needs at least 37")
    rp_id_hash = auth[0:32]
    flags_byte = auth[32]
    sign_count = struct.unpack_from(">I", auth, 33)[0]
    out = {
        "rp_id_hash_hex": rp_id_hash.hex(),
        "flags_byte": flags_byte,
        "flags": {name: bool(flags_byte & bit) for bit, name in FLAGS},
        "sign_count": sign_count,
        "attested_credential": None,
        "extensions": None,
    }
    i = 37
    if flags_byte & 0x40:
        if len(auth) < i + 18:
            raise ValueError("attested credential flag set but the data is truncated")
        aaguid = auth[i:i + 16]
        i += 16
        cid_len = struct.unpack_from(">H", auth, i)[0]
        i += 2
        cred_id = auth[i:i + cid_len]
        i += cid_len
        cose, _ = cbor_decode(auth, i)
        out["attested_credential"] = {
            "aaguid_hex": aaguid.hex(),
            "aaguid_is_zero": aaguid == b"\x00" * 16,
            "credential_id_hex": cred_id.hex(),
            "credential_id_bytes": cid_len,
            "public_key_cose": jsonable(cose),
        }
    return out


def analyse(obj_b64):
    raw = base64.b64decode(obj_b64 + "=" * (-len(obj_b64) % 4))
    obj, consumed = cbor_decode(raw)
    if not isinstance(obj, dict):
        raise ValueError("attestation object is not a CBOR map")
    auth = obj.get("authData")
    if not isinstance(auth, (bytes, bytearray)):
        raise ValueError("attestation object has no authData byte string")
    att_stmt = obj.get("attStmt") or {}
    return {
        "bytes_total": len(raw),
        "bytes_consumed": consumed,
        "fmt": obj.get("fmt"),
        "att_stmt_fields": sorted(att_stmt.keys()) if isinstance(att_stmt, dict) else [],
        "auth_data": parse_auth_data(bytes(auth)),
        "note": "signature and chain are not verified here; this reports what the artefact says",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?")
    ap.add_argument("--b64")
    args = ap.parse_args()

    b64 = args.b64
    if not b64:
        if not args.path:
            ap.error("give a path or --b64")
        text = open(args.path, encoding="utf-8").read()
        try:
            doc = json.loads(text)
        except Exception:
            b64 = text.strip()
        else:
            # accept a raw attestation response or a JSON wrapper holding one
            b64 = (doc.get("response", {}) or {}).get("attestationObject") or doc.get("attestationObject")
            if not b64:
                print("no attestationObject in that JSON", file=sys.stderr)
                return 1
    try:
        print(json.dumps(analyse(b64), indent=1, ensure_ascii=False))
    except Exception as e:
        print(f"cannot parse: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
