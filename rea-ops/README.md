# rea-ops

Code for the extraction operations `data/domains/D31.json` names as gaps. An operation lives here only
when it has a fixture and a test, because an operation with neither is a claim.

| op | what it does | tested against |
|---|---|---|
| `warc.py` | reads WARC 1.0 response records, plain or gzip, emits HAR-shaped JSON with an explicit absent field rather than a guess | a WARC this repo generates |
| `wxapkg.py` | parses a documented wxapkg layout and extracts with traversal refusal | a package this repo generates |

Run the tests:

```bash
python3 rea-ops/test-ops.py
```

Two things stated plainly rather than implied:

- **`wxapkg.py` has not been validated against a real WeChat package.** Published descriptions of the
  format disagree on header width across versions, and no real sample was available here. It is a correct
  parser for a documented shape, which is not the same as a working tool.
- Neither operation is wired into the REA MCP server. They are standalone readers today.

The remaining gaps in D31 are still gaps. Eight of ten are unbuilt.
