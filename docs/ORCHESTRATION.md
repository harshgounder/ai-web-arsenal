# Orchestration: how to compose agents for this work

Most "multi-agent pentest" stacks are one agent with extra steps, and they fail in a specific way: the
same model proposes, executes and confirms, so it confirms its own hallucinations. This document is the
composition that avoids that, with the cheap parts first.

---

## 1. The three roles that matter

Not seven. Three.

| role | authority | may not |
|---|---|---|
| **Operator** | chooses targets, approves scope, holds the credential | act outside the recorded scope |
| **Executor** | issues requests, runs tools, records evidence | decide its own finding is confirmed |
| **Critic** | attempts to falsify, assigns verdict | issue a request to the target |

The separation that produces reliability is **Executor must not be Critic**. Everything else is
optional. A single agent doing both will report confident nonsense, and no amount of prompt engineering
fixes it, because the same context contains both the desire to succeed and the judgement.

The Operator can be a human, and for anything real it should be.

---

## 2. The minimal loop

```
Operator records scope
  -> Executor: capture, inventory, reverse artifacts        (prompts 01, 02)
  -> Executor: hypotheses, ranked by cost to test           (prompt 03)
  -> Executor: cheapest test, evidence recorded verbatim
  -> Executor: prove, with oracle and negative control      (prompt 04)
  -> Critic: falsify                                        (prompt 05)
  -> Operator: accept, downgrade or drop
```

Four properties make this loop different from a scanner:

1. **Evidence is captured before interpretation.** Requests and responses verbatim, in a file, with
   timestamps, before any prose is written. A finding assembled from memory is not a finding.
2. **The Critic has fresh context.** It sees the finding and the evidence, not the Executor's reasoning.
   If it inherits the reasoning it inherits the bias.
3. **Verdicts are constrained.** The Critic returns one of SOUND, OVERSTATED, UNSAFE_TO_REPORT, REFUTED.
   REFUTED is a success, and the loop counts it as one.
4. **The Operator is the only thing that can spend a credential or widen scope.**

---

## 3. When to add agents, and when not to

| situation | composition | why |
|---|---|---|
| one target, one stack | Operator, Executor, Critic | the default, and usually enough |
| wide surface, many hosts | add a Recon fleet, all read-only, no write capability | parallel acquisition, sequential judgement |
| long-running campaign | add a Bookkeeper that owns state and evidence | context does not fit in one window |
| unknown protocol or binary | add a Reverser (REA calls) | different toolset, different failure mode |
| novel class, no known pattern | add a Researcher that may read outside the target | must be sandboxed from the target |

Do **not** add agents for:

- speed. parallel exploitation of the same target multiplies detection and damage, not yield.
- coverage. it multiplies requests, not findings.
- confirmation. that is the Critic's job, and one Critic is enough. Two Critics agreeing is a nice
  signal, but they must not see each other's verdict first.

---

## 4. Handoff contract

Every handoff is a JSON object, not prose. Prose handoffs lose the detail that matters and gain
confident summaries of things that were never checked.

```json
{
  "id": "find-2026-10-26-001",
  "from": "executor",
  "scope": {"target": "...", "authorization": "line from the scope record", "recorded_at": "..."},
  "claim": "one sentence, falsifiable",
  "request": {"method": "", "url": "", "headers": {}, "body": ""},
  "response": {"status": 0, "headers": {}, "body_excerpt": ""},
  "control": {"request": {}, "response": {}, "expected_if_real": ""},
  "oracle": "one of: differential_body, differential_status, timing_with_control, oob_callback, state_reread, second_engine",
  "evidence_path": "path on disk with the raw bytes",
  "attempted_falsifications": ["what the executor already ruled out"],
  "wants": "REVIEW"
}
```

The Critic reads this and writes:

```json
{"id": "same", "from": "critic", "verdict": "SOUND|OVERSTATED|UNSAFE_TO_REPORT|REFUTED",
 "missing_evidence": "", "severity_adjust": "same|lower|higher", "reason": "one sentence"}
```

Two rules that matter more than the schema:

- **`evidence_path` must resolve.** A handoff pointing at nothing is rejected, not reviewed.
- **`control` is mandatory for any claim of impact.** Absent control means the verdict ceiling is
  UNCONFIRMED, automatically.

---

## 5. Budget and safety guards

An autonomous agent with network access is a liability unless it is bounded. These are non-negotiable:

| guard | rule |
|---|---|
| scope | a written allowlist of hosts and paths, enforced before the request, not after |
| rate | a global requests-per-second ceiling, per host ceilings, and a hard total cap per run |
| blast radius | no destructive methods against production unless explicitly authorised per endpoint |
| credential | the agent never holds a credential it can escalate with; least privilege per role |
| stop condition | a budget in requests, wall clock and findings, whichever comes first |
| audit | every request logged with the scope basis that permitted it |

A run that exceeds its rate is not "being thorough". It is a denial of service with a README.

---

## 6. Failure modes of multi-agent offensive work, and the tell

| failure | tell | fix |
|---|---|---|
| confirmation bias loop | high finding rate, low survival rate at review | separate Critic with fresh context |
| context collapse | later agents repeat early work | Bookkeeper with a state file |
| scope drift | requests to hosts not in the allowlist | enforcement at the request layer |
| evidence laundering | findings reference summaries, not raw bytes | evidence path must resolve |
| critic capture | Critic agrees with everything | test the Critic on a known-bad finding |
| tool thrash | many tools, few findings | hypothesis first, tool second |
| silent rate breach | rising error rate on the target | global rate ceiling, alert on it |

The first and fifth are the ones that make AI pentest look bad in public. Both are solved by the same
thing: **the agent that finds is never the agent that approves.**

---

## 7. What this repo provides

| artefact | role it serves |
|---|---|
| `prompts/01` to `prompts/05` | the loop, one pack per stage |
| `skills/web-arsenal/` | the order of operations, loadable by any agent |
| `trees/` | decision trees as JSON, so a route is data not prose |
| `mcps/` | the extraction capabilities the Executor calls |
| `data/domains/` | what to test per domain, with preconditions and oracles |
| `web-attack-atlas` | the pattern layer, with the counter for each pattern |

The Critic pack is the one that changes outcomes. If you take one thing from this document, take that.
