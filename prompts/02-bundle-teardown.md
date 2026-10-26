# Prompt pack: bundle-teardown

**Phase:** L03 to L05. **Agency:** A3. **Prerequisites:** REA with `export_web_scripts` and `analyze_web_bundle`.

## Why this pack exists

The single highest-yield action on a modern web target is reading its own JavaScript. It reveals routes,
feature flags, internal hostnames, auth logic and sometimes keys. Models do this badly when handed a
300KB minified file, and well when given structure first.

## The prompt

```
You are reversing a JavaScript bundle from an authorised assessment.

STEPS, in order:

1. Structure before content. Call analyze_web_bundle on {host}. Report: chunk count, entry chunk,
   lazy loaded chunks, any source map presence, and the vendor fingerprints it found.
2. Route extraction. List route-like string literals. Group by prefix. Say which ones the capture
   also contained and which are bundle-only. Bundle-only routes are the interesting ones.
3. Auth logic. Find how the client decides a user is authenticated and what role they hold. Quote the
   exact identifiers, not a paraphrase. If it reads a claim from a token, say which claim.
4. Feature flags and internal hosts. List them verbatim.
5. Secret candidates. Anything that looks like a key, token, or credential. For each, state whether it
   is a public identifier (safe) or a secret (a finding), and why you think so.
6. Then stop and output the three highest-value things a human should look at, with the reason.

RULES
- Quote identifiers exactly. Never paraphrase a variable name.
- Distinguish "the client checks X" from "the server enforces X". The client check is not a control.
- If a region is too minified to read, say so and name the chunk. Do not guess.
```

## Expected output shape

Sections per step, each with quoted identifiers and a one-line interpretation.

## Failure modes

| failure | tell |
|---|---|
| paraphrasing identifiers | `isAdmin` becomes "an admin flag" |
| treating client checks as controls | "the app validates the role in the UI" |
| inventing a source map | no `//# sourceMappingURL` and no `.map` fetch |

## Verification

```bash
# the ground truth for "does a source map exist"
grep -o 'sourceMappingURL=[^ ]*' bundle.js | tail -3
```
