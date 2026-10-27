# rea-ops

Code for the extraction operations `data/domains/D31.json` names as gaps. An operation lives here only
when it has a fixture and a test, because an operation with neither is a claim.

| op | what it does | tested against |
|---|---|---|
| `warc.py` | reads WARC 1.0 response records, plain or gzip, emits HAR-shaped JSON | a WARC this repo generates |
| `wxapkg.py` | parses a documented wxapkg layout and extracts with traversal refusal | a package this repo generates |
| `leveldb-log.py` | reads a LevelDB write-ahead log: masked CRC32C, records spanning blocks, WriteBatch puts and deletes | a log this repo generates |
| `hap.py` | unpacks a HarmonyOS HAP, identifies Ark bytecode and native libraries, parses module.json | a package this repo generates |
| `webauthn-attestation.py` | CBOR decodes an attestation object, reports flags, sign count, AAGUID, credential id and COSE key | an attestation this repo generates |

Run the tests:

```bash
python3 rea-ops/test-ops.py      # 45 checks
```

Five of ten gaps closed. What each one states plainly rather than implying:

- **`wxapkg.py` has not been validated against a real WeChat package.** Published descriptions of the
  format disagree on header width across versions, and no real sample was available here.
- **`leveldb-log.py` reads the log, not the sorted tables.** A value compacted before the log was read is
  not in the output, and the tool exits 2 with that sentence instead of returning an empty result that
  reads like absence.
- **`hap.py` does not decompile Ark bytecode and does not verify the signature.** It identifies the
  `.abc` files so a reader knows what needs a disassembler.
- **`warc.py` does not resolve revisits beyond a pointer** and does not verify digests.
- **`webauthn-attestation.py` verifies no signature and no chain.** It reports what the artefact says,
  because whether to trust the authenticator is a relying party policy decision this tool does not have.

None of the four is wired into the REA MCP server yet. They are standalone readers.

The remaining five gaps are still gaps: Flutter AOT, Hermes, service worker reconstruction, signing
recovery and source map recovery.
