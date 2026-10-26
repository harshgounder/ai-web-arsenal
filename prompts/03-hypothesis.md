# Prompt pack: hypothesis

**Phase:** L05. **Agency:** A2 to A3. **Prerequisites:** a stack profile and an endpoint inventory.

## Why this pack exists

Most AI pentesting fails here, not at exploitation. The model generates a generic checklist instead of
hypotheses derived from *this* stack. This pack forces derivation and ranking.

## The prompt

```
STACK PROFILE: {runtime, framework, proxy, cdn, waf, auth provider, db, api protocol}
ENDPOINT INVENTORY: {table from recon-capture}
AUTHORIZATION: {one line}

Produce ranked hypotheses. For each:

  H-n: one sentence, falsifiable, naming the component and the mechanism
  derived_from: which specific fact in the stack profile or inventory produces this hypothesis
  precondition: what must be true on this target
  cheapest_test: the smallest request that could disprove it
  if_true: the impact, in one clause
  kill_criteria: what result would make you drop it

RANKING RULES
- A hypothesis that needs no special access outranks one that needs an account.
- A hypothesis about a component visible in the stack outranks a generic class.
- A hypothesis whose kill_criteria you can test in one request outranks one that needs setup.

Then: name the three hypotheses you would NOT test and why. Refusing well is part of the job.

RULES
- No hypothesis without derived_from. "XSS is common" is not a derivation.
- Do not list a class that the stack profile rules out. If there is no GraphQL, no GraphQL hypothesis.
```

## Expected output shape

An ordered list of 8 to 15 hypotheses in the field format above, plus a short refusal list.

## Failure modes

| failure | tell |
|---|---|
| generic checklist | derived_from says "common vulnerability" |
| unfalsifiable | no kill_criteria |
| ignoring the stack | hypotheses that need a component not in the profile |

## Verification

A human reviewer asks: could I disprove each of these in under five minutes? Count how many pass.
A healthy set is above 70 percent.
