---
name: web-arsenal
description: Drive an authorised web assessment with the ai-web-arsenal method: capture first, reverse the artifacts, derive hypotheses from the stack, then prove with an oracle and a negative control. Use when the task is testing a web app or API, or when you need to know what to run and in what order.
---

# web-arsenal

## Order of operations

Do not start with a scanner. Start at the artifact.

1. **Capture.** `mitmdump -w flows.mitm` while browsing once. No probing yet.
2. **Inventory.** Use REA `inspect_web_network_capture` on the flow. Apply `prompts/01-recon-capture.md`.
   Output: endpoints, auth requirement, UI-reachable or not.
3. **Artefacts.** REA `analyze_web_bundle`, then `export_web_scripts`, then `recover_javascript_sources`
   if obfuscated. Mobile client if there is one: `inspect_android_package`. Apply
   `prompts/02-bundle-teardown.md`.
4. **Hypotheses.** Build the stack profile. Apply `prompts/03-hypothesis.md`. Rank by cost to test.
5. **Test.** Cheapest first. Every test records the exact request and response.
6. **Prove.** Apply `prompts/04-prove-it.md`. No verdict of CONFIRMED without a negative control.
7. **Critic.** A second agent applies `prompts/05-critic.md`. Its job is to break the finding.

## Non-negotiables

- Every request has a recorded authorization basis. If it is missing, stop.
- Rate limit. An agent that ignores rate is a denial of service.
- A finding without a negative control is a hypothesis, not a finding.
- The client enforces nothing. Client checks are hints about server behaviour, not controls.
- Two engines for any claim that matters. One tool output is not evidence.

## Lookup

- tool drivers and install: `manifest/tools.yaml`, `data/install-matrix.json`
- domains: `domains/`, `data/domains/`
- patterns and counters: the companion repo, `web-attack-atlas`
- bootstrap: `BOOTSTRAP.md`
