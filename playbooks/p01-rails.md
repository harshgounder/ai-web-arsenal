# Playbook: Ruby on Rails

Generated from `data/playbooks/` by `scripts/render-playbooks.py`. Do not edit by hand.

An ordered run for this stack. Every step cites an entry in this repo with an oracle already
written for it, because the order is the part a tool list cannot give you.

## Is it this stack

- X-Powered-By or Server headers rarely help; look for a `_session_id` cookie
- asset paths containing a digest, e.g. /assets/application-<hash>.css
- 422 responses with a Rails error page on a bad authenticity token

## The order

| # | run | why here | what proves it |
|---|---|---|---|
| 1 | [`Security header posture across response variants`](../domains/D08-client-side-and-browser-trust-boundaries.md) | headers are set per response, and Rails error pages are where they go missing | at least one response variant missing a header the others carry |
| 2 | [`Binding and middleware order audit`](../domains/D07-injection-family.md) | strong parameters are per controller; one controller that forgot permits everything | an undeclared field persisted, traced to the controller |
| 3 | [`Lazy and eager loading authorisation parity`](../domains/D07-injection-family.md) | ActiveRecord scopes apply to queries but a lazy relation can bypass the scope chain | a record reachable through a lazy path that the collection query excludes |
| 4 | [`Autorize`](../domains/D05-authorization-tenancy-field-level-access.md) | authorisation usually lives in a before_action per controller, so gaps are per controller too | a request replayed as a lower role that still succeeds |
| 5 | [`fuxploider`](../domains/D13-file-handling-upload-path-archive.md) | ActiveStorage and blob uploads decide type by content, and the pipeline trusts it | an uploaded file reachable and interpreted as something else |
| 6 | [`race-the-web`](../domains/D12-business-logic-races-money-paths.md) | counter caches and optimistic locking are where Rails logic races live | a stale write accepted after a concurrent update |
| 7 | [`This repo: prompts/04-prove-it.md`](../domains/D24-evidence-proof-and-reporting.md) | before writing anything up, falsify it | the control run produces no effect |

## What will make you wrong

- a 422 on a forged token is not a CSRF finding, it is the protection working
- Rails `find` raises while `where` returns empty, so a 404 and a 200 can mean the same query
- development error pages expose the full stack, which is a finding only if reachable in production

## What this playbook does not cover

- Action Cable and Turbo Streams are WebSocket surfaces and the atlas does not model them
- ActiveJob retry semantics are named in the data lens and have no lab here

## Where each step lives

- step 1: `d08-header-posture` in D08, Client-side and browser trust boundaries
- step 2: `d07-binder-audit` in D07, Injection family
- step 3: `d07-orm-loading` in D07, Injection family
- step 4: `d05-autorize` in D05, Authorization, tenancy, field-level access
- step 5: `d13-fuxploider` in D13, File handling, upload, path, archive
- step 6: `d12-race-the-web` in D12, Business logic, races, money paths
- step 7: `d24-prove` in D24, Evidence, proof and reporting
