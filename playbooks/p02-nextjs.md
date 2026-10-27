# Playbook: Next.js and React server rendering

Generated from `data/playbooks/` by `scripts/render-playbooks.py`. Do not edit by hand.

An ordered run for this stack. Every step cites an entry in this repo with an oracle already
written for it, because the order is the part a tool list cannot give you.

## Is it this stack

- /_next/static/ asset paths with a build id
- a `__NEXT_DATA__` script tag on server rendered pages
- RSC payloads in the flight stream, which look like `self.__next_f.push` calls

## The order

| # | run | why here | what proves it |
|---|---|---|---|
| 1 | [`rea analyze_web_bundle`](../domains/D03-fingerprinting-and-stack-identification.md) | the client bundle and the flight payload together are the real route table | a route or action present in the payload that the sitemap does not list |
| 2 | [`rea inspect_web_page`](../domains/D06-session-token-cookie-key-material.md) | the app stores session state client side more often than it admits | a token or a tenant id readable from storage or from the flight payload |
| 3 | [`Security header posture across response variants`](../domains/D08-client-side-and-browser-trust-boundaries.md) | static assets, API routes and error boundaries each carry their own headers | one variant missing a header the others carry |
| 4 | [`kiterunner`](../domains/D11-api-protocols.md) | route handlers and server actions are easy to add and easy to forget to guard | an undocumented route or action that answers |
| 5 | [`Web Cache Vulnerability Scanner`](../domains/D10-cache-cdn-edge-behaviour.md) | full route cache and ISR mean a response can outlive the permission under it | a personalised response served to a second client |
| 6 | [`smuggler`](../domains/D09-http-semantics-smuggling-desync.md) | server actions are POSTs to the page route, so framing disagreements land on them | a smuggled prefix that becomes a second action invocation |
| 7 | [`This repo: prompts/04-prove-it.md`](../domains/D24-evidence-proof-and-reporting.md) | cache findings are the easiest to fake, so control them | the same request with the header removed produces the benign page |

## What will make you wrong

- a personalised response is not a cache finding unless a second client receives it
- the flight payload often contains more than the HTML does, including server-only props
- middleware runs at the edge and can be bypassed by a mismatched route, so test the handler and not the redirect

## What this playbook does not cover

- React Server Component serialisation has no dedicated entry
- edge middleware ordering is not modelled

## Where each step lives

- step 1: `d03-rea-bundle` in D03, Fingerprinting and stack identification
- step 2: `d06-rea-page` in D06, Session, token, cookie, key material
- step 3: `d08-header-posture` in D08, Client-side and browser trust boundaries
- step 4: `d11-kiterunner` in D11, API protocols: REST, GraphQL, gRPC
- step 5: `d10-wcvs` in D10, Cache, CDN, edge behaviour
- step 6: `d09-smuggler` in D09, HTTP semantics, smuggling, desync
- step 7: `d24-prove` in D24, Evidence, proof and reporting
