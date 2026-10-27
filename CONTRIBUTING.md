# Contributing

## The bar

An entry without a `driver`, a `precondition` and an `oracle` is a note, not an entry. That rule is why
this repo is different from a link list, and it is not negotiable.

A pull request that adds a row with only a name and a URL will be closed with that sentence.

## Adding a tool

1. Add it to `manifest/tools.yaml` with every install candidate you believe resolves, in preference order.
2. Run `python3 scripts/verify-tools.py`. It resolves each candidate against pacman, the AUR RPC, PyPI,
   crates, npm or the git remote. An unresolved candidate must be fixed, not marked.
3. Run `python3 scripts/gen-bootstrap.py` to regenerate the installers. Never hand edit `bootstrap/`.
4. Reference the tool from a domain entry with `driver.install` matching the resolved channel.

## Adding or editing a domain

1. Edit `data/domains/DXX.json`. Never edit `domains/DXX-*.md` by hand, it is generated.
2. Every entry needs: `atom`, `preconditions`, `oracle`, `evades`, `detected_by`, and all four `driver`
   fields.
3. Every probing or exploit entry (stage L06 to L08) must have a non-empty `oracle`.
4. Run the gate sequence:

```bash
python3 scripts/normalize-atoms.py
python3 scripts/render-domain.py DXX
python3 scripts/validate-domains.py
python3 scripts/build-indexes.py
python3 scripts/dedupe-names.py
```

## Numbers

Never type a count into a document. Run the script that produces it. If you must quote a number, name
the script next to it.

## Links

Every URL must be fetched before it lands. `python3 scripts/stamp-and-check.py --check core_web` for the
corpus, and the domain link check for domain entries. A URL that has not been fetched is a hypothesis,
and two repositories were invented in this project's own history by skipping that rule.

## Commit style

One logical change per commit. State what changed and why. If you fixed a defect in your own work,
say so in the message rather than quietly rewriting history.

## What is out of scope

Operational assistance for unauthorised access. Attack classes are described at methodology level with
their authorisation requirement. Contributions that cross that line are rejected.
