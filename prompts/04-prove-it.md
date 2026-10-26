# Prompt pack: prove-it

**Phase:** L08. **Agency:** A5. **Prerequisites:** a candidate finding.

## Why this pack exists

This is the pack that separates a report from a rumour. It refuses to let a model declare success.
Every claim needs an oracle and a negative control, and the model has to try to falsify itself first.

## The prompt

```
CANDIDATE FINDING: {one sentence}
OBSERVED: {exact request, exact response, headers, status}
SESSION: {whose session, what role, what object}

Work through this and do not skip:

1. FALSIFY FIRST. State the most likely reason this is a false positive. Examples: the object is
   public, the value is yours, the endpoint echoes anything, the server ignored the field.
   Then design the request that would distinguish your finding from that explanation.
2. NEGATIVE CONTROL. Give the control request: same shape, but with the element that must matter
   changed to something that should fail. State the expected result if your finding is real, and the
   expected result if it is an artifact. Run it.
3. POSITIVE REPRO. Repeat the original request from a clean session, and from a second identity.
   Does it hold for both, or only for one?
4. ORACLE. Name which oracle type you used: differential body, differential status, timing with
   control, out of band callback, stored state re-read, second engine confirms. One is enough, but
   name it.
5. VERDICT. One of: CONFIRMED (control behaved as predicted, repro holds), UNCONFIRMED (control
   ambiguous), REFUTED (control produced the same result), or NEEDS_ACCESS.

RULES
- If you cannot run the control, the verdict is UNCONFIRMED. Never CONFIRMED.
- "The response differed" is not an oracle unless you say how it differed and why that difference
  cannot be explained by the control.
- REFUTED is a good outcome. Say it plainly.
```

## Expected output shape

Numbered sections, ending in one verdict word and one sentence of impact.

## Failure modes

| failure | tell |
|---|---|
| CONFIRMED without a control | no section 2 result |
| oracle is "it worked" | no oracle type named |
| control is not actually a control | differs by more than the variable under test |

## Verification

The evidence file must contain both requests verbatim. If the control request is missing from the
record, the finding is not evidence, it is a note.
