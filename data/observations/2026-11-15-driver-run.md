# Driver observations feed: 2026-11-15

Source: web-attack-driver engagements juice-lab-01/02/03 (90 requests, 3 full
executor/critic loops against juice-shop). This file feeds domain docs and
data/observations/ per the repo's own evidence schema.

## What the loop showed (L06/L08 relevant)

1. **OAuth branch writes a deterministic password from the email address**
   (F03, overstated: client-side derivation visible, server acceptance untested).
   L08 business-logic candidate: identity grant flows that mint predictable
   credentials from public identifiers.

2. **Basket/object APIs accept caller-supplied IDs** (F05, overstated pending
   cross-user evidence). L01 object-level candidate with a concrete test path:
   register two accounts, swap basket IDs, diff responses.

3. **Ambient-authentication password change via GET** (F10, overstated pending
   runtime proof). If confirmed it composes A02 (trust boundary) with A12
   (GET mutations bypass CSRF posture) - exactly the W01/W02 composition the
   atlas grammar predicts.

## Critic verdict distribution (why it matters for tooling)

Across 23 candidate findings in 3 runs: 5 proven, 1 refuted, 17 overstated.
The overstated share (74%) is the number scanners do not show: without a
fresh-context critic, those 17 would have shipped as confident nonsense.
This is the strongest argument for the ORCHESTRATION.md executor != critic rule.

## Machine-readable entry

    {
      "date": "2026-11-15",
      "source": "web-attack-driver juice-lab-01..03",
      "candidates": 23, "proven": 5, "refuted": 1, "overstated": 17,
      "top_proven": [
        {"id": "F01", "atom": "A01", "claim": "SQL predicate injection in /rest/products/search"},
        {"id": "F06", "atom": "A08", "claim": "/ftp directory index exposure"},
        {"id": "F08", "atom": "A08", "claim": "ORM stack trace on unauthenticated recovery lookup"}
      ],
      "lesson": "74% overstated rate = critic separation is not optional"
    }
