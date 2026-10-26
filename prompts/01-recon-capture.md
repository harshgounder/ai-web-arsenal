# Prompt pack: recon-capture

**Phase:** L02 to L04. **Agency:** A3. **Prerequisites:** a captured HAR or mitmproxy flow, REA wired.

## Why this pack exists

Models hallucinate endpoints when asked "what endpoints does this app have". They stop doing that when
given a capture and told to cite byte offsets. This pack forces grounding in captured bytes.

## The prompt

```
You are analysing a network capture from an authorised web assessment.

INPUT: {capture_path} (format: {har|mitmproxy|saz|qlog})
AUTHORIZATION: {scope statement, one line}

Do this in order, and stop if a step fails:

1. List every distinct endpoint: method, host, path, and whether the path segment contains an
   identifier (uuid, integer, slug, email, base64). Do not invent endpoints. If you cannot see it in
   the capture, it does not exist for this exercise.
2. For each endpoint, state the auth requirement as observed: none, session cookie, bearer token,
   api key header, or unknown. "Unknown" is a valid and useful answer.
3. Mark the endpoints the UI never calls. Compute this from the capture only: an endpoint is UI-reachable
   if a document or script request precedes it from the same session.
4. Emit a table: method | path | id-in-path | auth | ui-reachable | request count | response size range.
5. Then, separately, list what you would need to know to test each one, as questions, not actions.

RULES
- Never speculate about an endpoint you did not see.
- If two requests differ only by a value in a path segment, treat them as the same endpoint and say so.
- Do not propose exploitation. This phase is inventory.
```

## Expected output shape

A markdown table plus a "questions" list. No prose paragraphs.

## Failure modes to watch

| failure | tell |
|---|---|
| invented endpoints | a path that appears in no request and no script |
| wrong auth classification | "none" for a request that carried a cookie |
| treating a value in a path as a different endpoint | near-duplicate paths with one differing segment |

## Verification

Cross-check the model's table against a mechanical extraction:

```bash
jq -r '.log.entries[] | "\(.request.method) \(.request.url)"' capture.har | sort | uniq -c | sort -rn
```

If the counts differ, the model invented or dropped rows. The mechanical answer wins.
