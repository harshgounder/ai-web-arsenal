# ATTACK ONTOLOGY v0: the generative model

Status: model draft. This is the layer that makes "every attack method" achievable instead of
aspirational. Read this before writing any domain document, because every domain doc's attack rows
are instances of this grammar.

---

## 1. Why a list cannot be complete, and a grammar can

The ask is every web attack method, pattern, edge case and minute mutation in history. Taken literally
that is an open set. It grows monthly, it is spread across 30 years of mailing lists, conference talks,
bug bounty reports and vendor advisories, and every new framework invents dialects of old classes.

A flat list has two failure modes and both are fatal:

- **Under-enumeration.** You always miss some, and you cannot tell which.
- **False completeness.** A 3,000 row list feels total and proves nothing.

The generative form has neither. If every technique is a point in a finite product space, then:

- you can enumerate the space mechanically
- you can prove a technique is in it or argue it is out of grammar
- new techniques are recombinations of known axes, so the model predicts them before they are published
- coverage is measurable per cell, not per list row

This is the same move that made ATT&CK useful where "list of hacker tricks" never was.

---

## 2. The grammar

```
attack = atom(sink, carrier, preconditions, oracle) x mutation(encoding, context, protocol, timing)
chain  = attack_1 . attack_2 ... where capability(attack_n) enables preconditions(attack_{n+1})
```

Six fields. Any claimed technique that does not fill all six is a slogan, not an attack.

### 2.1 Atom

The primitive. What is fundamentally being violated. There are far fewer atoms than techniques, which
is the whole point.

| atom | the violation |
|------|---------------|
| A01 interpreter confusion | data the app treats as inert is executed by a downstream interpreter |
| A02 trust boundary crossing | a lower-trust principal acts with a higher-trust identity or scope |
| A03 identity confusion | the system misidentifies who or what is acting |
| A04 state confusion | the system's view of state diverges from the real state |
| A05 type and shape confusion | the value is valid in one context and different in another |
| A06 path and namespace confusion | two components resolve the same name or path differently |
| A07 resource exhaustion | a finite resource is consumed faster than it is replenished |
| A08 information exposure | data crosses to a party that should not receive it |
| A09 cryptographic weakness | a property the design assumes is false |
| A10 logic assumption violation | the workflow assumes an invariant the attacker can break |
| A11 dependency compromise | an upstream artifact is trusted and is not trustworthy |
| A12 timing and ordering | the window between check and use is exploitable |
| A13 side channel | observable behaviour leaks protected information |
| A14 human manipulation | the human in the loop is the weak component |
| A15 configuration divergence | the deployed state differs from the intended state |
| A16 model and agent manipulation | an AI component's instruction-following is the boundary |

That is 16 atoms. Every web attack in history is a composition of one or more of these. SQL injection is
A01 with a database parser sink. SSRF is A01 plus A02. IDOR is A02 plus A03. Request smuggling is A06
plus A04. A prompt injection that calls a tool is A16 plus A01.

### 2.2 Carrier

How the payload reaches the sink. This axis is where most missed techniques live, because lists group by
class and forget that the same class has 30 carriers.

Carrier families: query string, path segment, path parameter matrix, fragment (client only), body
form-urlencoded, multipart part body, multipart filename, multipart header, JSON value, JSON key, JSON
number, deeply nested JSON, duplicate JSON keys, JSON pointer, XML text, XML attribute, XML entity, XML
DTD, XML CDATA, XML namespace, YAML alias, YAML tag, protobuf field, protobuf unknown field, msgpack
extension, CBOR tag, HTTP header value, header name, header folding, request line, request target,
absolute URI, host header, SNI, cookie name, cookie value, cookie attribute, session store key, WebSocket
frame text, WebSocket frame binary, SSE event, GraphQL query, GraphQL variable, GraphQL directive,
GraphQL fragment name, gRPC metadata, gRPC message, webhook body, file upload name, file content, image
metadata, PDF object, archive entry name, ZIP comment, environment variable inherited from a log line,
CSV cell, template literal, URL in a redirect, markdown link, rich text editor HTML, and the client
storage slot.

### 2.3 Sink

Where the carrier lands and what interprets it.

Parser sinks: SQL engine, NoSQL query, ORM and HQL, LDAP, XPath, XSLT, JSON parser, YAML parser, XML
parser, template engine per engine family, expression language per runtime, shell, eval family, regex
engine, glob, CSV parser, markdown renderer, PDF renderer, image decoder, archive extractor, URL
resolver, redirect handler, HTTP client used server side, DNS resolver, mail composer, log formatter,
query string builder, cache key builder, serializer and deserializer per language, deserialization gadget
chain, file system path resolver, browser DOM, JS engine in the page, service worker, WebAssembly module,
browser extension context, mobile webview bridge, and the AI model or agent tool dispatcher.

### 2.4 Preconditions

What must be true for the atom to land. This is the field that makes the corpus useful, because it turns
a giant list into a filter over the actual target.

Examples: reflection without encoding, error verbosity, missing object-level authorization, predictable
identifiers, shared cache, permissive CORS, trust in a header, no integrity check on a token, an admin
interface reachable without auth, a debug endpoint left enabled, a dependency with a known gadget, a
parser differential between two components, a clock the attacker can influence, a tenant identifier the
attacker controls, a feature flag that changes validation, a mobile client that the server trusts more
than the browser, and an AI component that treats retrieved text as instructions.

### 2.5 Oracle

How you know it worked, with no guessing. This is the difference between a scanner and an assessment.

Oracles: differential response body, differential status or header, differential timing with a control,
out-of-band callback, error signature change, stored state re-read, resource consumption measurable,
side effect visible in a second session, second engine confirms, and negative control passes.

Every finding in this repo must name its oracle. A finding without an oracle is a hypothesis.

### 2.6 Mutation

The transforms that defeat filters without changing the atom. This is the "minute mutation" the ask
names, and it is systematic rather than memorized.

| mutation class | what varies |
|---|---|
| encoding | URL, double URL, unicode, overlong, HTML entity, JS escape, hex, base64, gzip then base64, charset trick |
| syntax | case, whitespace, comment injection, alternative operators, equivalent constructs per dialect |
| context | JSON in JSON, XML in JSON, HTML in attribute vs text, quoted vs bare, inside a template expression |
| protocol | HTTP version, chunked vs content-length, header order, duplicate headers, h2 pseudo headers |
| normalization | dot segments, slash variants, unicode normalization, trailing dot in host, case in path |
| type | string where number expected, array where scalar, null, boolean coercion, big number precision |
| timing | interleave, race window, delayed trigger, sleep-based verification |
| volume | chunk splitting, multi-part boundary games, oversized field, compression bomb |

Mutation is orthogonal, which means one atom yields dozens of rows without anyone writing them by hand.

---

## 3. Composition: chains

A chain is where a test becomes an assessment. Two rules:

1. **Capability transfer.** Attack N must produce something attack N+1 needs: a token, a role, a file
   write, a network position, a parser state, a cache entry, an out-of-band channel, or a timing window.
2. **No unverified links.** Every hop carries its own oracle. A chain with one assumed hop is a story.

Canonical chain shapes worth naming in the corpus:

- reflection to script execution to session theft to privilege change
- file read to credential to authenticated surface to object-level authorization bypass
- SSRF to metadata credential to cloud control plane to data store
- smuggling to cache poisoning to victim request capture
- open redirect to OAuth code interception to account takeover
- prototype pollution to gadget to server-side RCE through a client library shared with the server
- mobile client trust to hidden API to missing authz on that API
- prompt injection to tool call to data exfiltration through an allowed channel
- dependency confusion to build pipeline to production artifact

---

## 4. The target model, so the grammar meets a real website

The user's criterion is: whatever composition, language or security posture the site has, the repo still
has a path. That requires the second half of the model, a target description:

```
target = stack(runtime, framework, proxy, cdn, waf, auth, db, cache, queue, storage, ai_components)
       x surface(routes, params, objects, roles, tenants, integrations)
       x posture(authn, authz, logging, rate_limit, integrity, secrets_management)
```

Then the attack set for that target is a join, not a lookup:

```
candidates(target) = atoms x carriers(surface) x sinks(stack) x preconditions(posture)
                     filtered by oracle_available
```

This is what makes the claim in the ask true in the only honest sense: not that we listed every
technique, but that for any target the corpus *derives* the candidate set and the corpus can prove its
own coverage of the axes.

---

## 5. What "complete" can mean, precisely

Three separate claims, reported separately, never merged.

1. **Axis completeness.** Every level of every axis is populated with at least one documented technique
   and at least one detection. Measurable, and this repo can hit it.
2. **Historical completeness.** Every technique that has a published name in a primary source (WSTG,
   ASVS, VRT, API Top 10, LLM Top 10, ATT&CK, HackTricks, PayloadsAllTheThings, nuclei templates, CVE
   classes) has an atom entry with provenance. Measurable against those corpora, which is what the
   rival reconciliation machinery already does.
3. **Derivational completeness.** For a given target description, the repo produces a candidate list and
   every candidate has a precondition test and an oracle. Measurable per target, at run time.

What is explicitly not claimed: that no unknown technique exists. New atoms are possible. When one
appears, it gets a new atom id and the grammar absorbs it.

---

## 6. Schema

One row per atom instance. Machine readable, so the corpus is queryable, not readable.

```json
{
  "id": "D08-XSS-CTX-0007",
  "atom": ["A01", "A05"],
  "carrier": "json.value",
  "sink": "browser.dom.innerhtml",
  "preconditions": ["reflection_unencoded", "dom_sink_reachable", "csp_absent_or_bypassable"],
  "oracle": ["differential_body", "execution_callback"],
  "mutations": ["unicode", "double_url", "context_json_in_json"],
  "evades": ["F2", "F3"],
  "detected_by": ["crs-941100", "csp-report"],
  "authorization": "written scope required, target owner consent",
  "provenance": {"source": "wstg:WSTG-CLNT-01", "verified": "2026-10-26"},
  "status": "VERIFIED"
}
```

Fields `evades` and `detected_by` are mandatory. An attack row with no defense mirror is incomplete,
because the repo answers "and does it work against this WAF" as a first-class question.

---

## 7. Build order

1. Freeze the atom list at 16. New atoms require an explicit decision, not a drive-by edit.
2. Enumerate carriers and sinks from the corpora already on disk: WSTG 131, ASVS 240, VRT 581,
   API Top 10, LLM Top 10, ATT&CK, HackTricks, PATT, nuclei templates.
3. Assign every existing test ID to at least one atom. Unmapped IDs are the first gap report.
4. Generate the mutation matrix mechanically from the mutation classes. Do not hand-write rows.
5. Add preconditions and oracles per instance. This is the slow, valuable part.
6. Attach detection rules from the defense mirror domain.
7. Publish coverage per axis cell with the count and the gap.

Step 3 is the point where the claim becomes auditable: if every WSTG and ASVS and VRT test maps to an
atom, and the atom space is fully populated, then the historical layer is covered by construction.

---

## 8. Boundary

This is a knowledge and decision-support layer for authorized security work. Every row carries its
authorization requirement. It describes classes, preconditions and verification methods. It does not
target a named third party, and it does not ship target-specific exploitation against systems the
operator does not own or have written permission to test.
