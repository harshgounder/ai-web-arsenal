# Playbook: GraphQL API

Generated from `data/playbooks/` by `scripts/render-playbooks.py`. Do not edit by hand.

An ordered run for this stack. Every step cites an entry in this repo with an oracle already
written for it, because the order is the part a tool list cannot give you.

## Is it this stack

- a single POST endpoint answering a query
- error shapes naming a schema type
- a playground or GraphiQL page left enabled

## The order

| # | run | why here | what proves it |
|---|---|---|---|
| 1 | [`InQL`](../domains/D11-api-protocols.md) | if introspection is on, the whole surface is one request away | a schema returned without credentials |
| 2 | [`clairvoyance`](../domains/D11-api-protocols.md) | with introspection off, field suggestions still name fields | a recovered field the UI never calls |
| 3 | [`graphql-cop`](../domains/D11-api-protocols.md) | the known misconfigurations are cheap to check before manual work | a named weakness confirmed by a request |
| 4 | [`Autorize`](../domains/D05-authorization-tenancy-field-level-access.md) | authorisation must be per field and per edge, not per endpoint | a field returned that the caller may not read |
| 5 | [`BatchQL`](../domains/D11-api-protocols.md) | batching and aliasing multiply every check in one request | N effects from one request that passed depth limits |
| 6 | [`schemathesis`](../domains/D11-api-protocols.md) | the schema states constraints the implementation may not enforce | an input accepted that the schema forbids |
| 7 | [`This repo: prompts/04-prove-it.md`](../domains/D24-evidence-proof-and-reporting.md) | a field returned is not a finding until you show it is not yours | the same field refused to a lower role, or a second tenant's record returned |

## What will make you wrong

- introspection disabled is not the same as the schema protected
- depth limits do not bound cost; aliases and fragments do the multiplication
- a 200 with an errors array is a partial success and often still returns data

## What this playbook does not cover

- subscription transports are not modelled
- federation boundary checks have no entry

## Where each step lives

- step 1: `d11-inql` in D11, API protocols: REST, GraphQL, gRPC
- step 2: `d11-clairvoyance` in D11, API protocols: REST, GraphQL, gRPC
- step 3: `d11-graphql-cop` in D11, API protocols: REST, GraphQL, gRPC
- step 4: `d05-autorize` in D05, Authorization, tenancy, field-level access
- step 5: `d11-batchql` in D11, API protocols: REST, GraphQL, gRPC
- step 6: `d11-schemathesis` in D11, API protocols: REST, GraphQL, gRPC
- step 7: `d24-prove` in D24, Evidence, proof and reporting
