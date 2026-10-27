# Playbook: WordPress

Generated from `data/playbooks/` by `scripts/render-playbooks.py`. Do not edit by hand.

An ordered run for this stack. Every step cites an entry in this repo with an oracle already
written for it, because the order is the part a tool list cannot give you.

## Is it this stack

- /wp-json/ and /wp-login.php answering
- a generator meta tag naming the version
- /wp-content/plugins/<name>/ readable directly

## The order

| # | run | why here | what proves it |
|---|---|---|---|
| 1 | [`whatweb`](../domains/D03-fingerprinting-and-stack-identification.md) | version and plugin set decide which known issues apply at all | a plugin directory or readme.txt naming a version |
| 2 | [`ffuf`](../domains/D02-recon-and-surface-mapping.md) | the plugin list is the attack surface and it is rarely complete in the UI | a plugin directory reachable that is not listed anywhere |
| 3 | [`wafw00f`](../domains/D22-waf-bot-and-anti-automation-evasion.md) | most WordPress sites sit behind something, and knowing which changes the encoding budget | a response that differs only for a blocked pattern |
| 4 | [`sqlmap`](../domains/D07-injection-family.md) | plugin queries are where injection lives; core is usually current and plugins are not | a conditional delay or a boolean difference on a plugin parameter |
| 5 | [`fuxploider`](../domains/D13-file-handling-upload-path-archive.md) | media uploads and plugin upload forms differ in type checking | a file stored and reachable as executable content |
| 6 | [`smuggler`](../domains/D09-http-semantics-smuggling-desync.md) | shared hosting and CDN fronting make framing disagreements common | a request the edge and the origin disagree about |
| 7 | [`This repo: prompts/04-prove-it.md`](../domains/D24-evidence-proof-and-reporting.md) | plugin version claims are unreliable, so prove the behaviour not the version | the control request produces no effect |

## What will make you wrong

- a readable plugin directory is a finding only with a behaviour, not on its own
- version numbers in meta tags are frequently wrong after a partial update
- xmlrpc.php open is not a finding unless a specific method does something

## What this playbook does not cover

- the block editor REST surface has no entry
- multisite tenancy is not modelled

## Where each step lives

- step 1: `d03-whatweb` in D03, Fingerprinting and stack identification
- step 2: `d02-ffuf` in D02, Recon and surface mapping
- step 3: `d22-wafw00f` in D22, WAF, bot and anti-automation evasion
- step 4: `d07-sqlmap` in D07, Injection family
- step 5: `d13-fuxploider` in D13, File handling, upload, path, archive
- step 6: `d09-smuggler` in D09, HTTP semantics, smuggling, desync
- step 7: `d24-prove` in D24, Evidence, proof and reporting
