# Link health

Checked 2026-10-26 by `scripts/stamp-and-check.py`. Every entry in the corpus now carries an evidence
state and a date. This file reports the failures, because a link that 404s is a finding about the
ecosystem, not a defect in the list.

**298 entries actually checked. 289 live, 9 problems.**

| status | count | meaning |
|---|---|---|
| LINK_OK | 289 | answered 2xx after redirects, as a browser would see it |
| LINK_DEAD | 3 | 404 or 410, the resource is gone |
| LINK_ERROR | 3 | timeout or transport failure, status unknown |
| LINK_BLOCKED | 3 | 401/403/429, exists but refuses automated clients |
| HARVESTED | 12749 | seen in a source, never independently checked |
| NO_URL | 11712 | taxonomy nodes and name-only rows, nothing to check |

## A correction, because the first run was wrong

The first pass reported 16 problem links out of 298, a 5.4 percent failure rate. Seven of those were
false: the checker sent `HEAD` first, and several real sites answer `HEAD` with 404 while `GET` returns
200. `https://portswigger.net/burp/` is the clearest case, and the implausibility of PortSwigger being
gone is what triggered the second look.

Two bugs, both fixed:

1. `HEAD` is unreliable. The checker now does `GET`, reads one byte, follows redirects, and sends a
   realistic browser user agent.
2. There was no recheck path. `--recheck-failures` now re-tests every non-OK entry, which is how the
   seven false failures were recovered.

The corrected failure rate is **3.0 percent**, and every failure below was re-verified with the
corrected method rather than inherited from the buggy one.

## Remaining failures

| status | http | name | url | sources |
|---|---|---|---|---|
| LINK_BLOCKED | 403 | DNS Trails | https://securitytrails.com/dns-trails | 0xinfection__awesome-waf |
| LINK_BLOCKED | 403 | Neat tricks to bypass CSRF-protection | https://zhuanlan.zhihu.com/p/32716181 | qazbnm456__awesome-web-security |
| LINK_BLOCKED | 403 | Twosecurity | https://twosecurity.io/ | qazbnm456__awesome-web-security |
| LINK_DEAD | 404 | RXSS and CSRF bypass to Account takeover | https://nirmaldahal.com.np/r-xss-csrf-bypass-to-account-takeover/ | devanshbatham__awesome-bugbounty-writeups, own-byok-cyber-arsenal |
| LINK_DEAD | 404 | SQLi Bypass | https://www.trustwave.com/en-us/resources/blogs/spiderlabs-blog/modsecurity-sql-injection-challenge-lessons-learned/ | 0xinfection__awesome-waf |
| LINK_DEAD | 404 | XSS Bypass | https://github.com/kmkz/Pentesting/blob/master/Pentest-Cheat-Sheet#L285 | 0xinfection__awesome-waf |
| LINK_ERROR | - | How To Exploit PHP Remotely To Bypass Filter | https://www.secjuice.com/php-rce-bypass-filters-sanitization-waf/ | 0xinfection__awesome-waf |
| LINK_ERROR | - | Public MUJ portal landing page | https://mujslcm.jaipur.manipal.edu/Home/Index | own-byok-cyber-arsenal |
| LINK_ERROR | - | RCE Payload Detection Bypass | https://www.secjuice.com/web-application-firewall-waf-evasion/ | 0xinfection__awesome-waf |

## Why this matters

The collections we reconciled never check their own links and do not carry dates. A 3 percent dead
rate on core entries means roughly one in thirty recommendations points at nothing, and the reader has
no way to tell which. That is what a list without dates and without a verification pass looks like
after a few years in service.

Nothing is deleted. A `LINK_DEAD` entry is marked, because deleting it loses the information that the
tool existed and died, which is itself useful. `LINK_BLOCKED` is not a defect: it means the site is
alive and refuses bots, which is a fact worth recording rather than a failure.

---

# Domain entry link check (2026-10-27)

Every URL in the 10 authored domain files, checked with `GET`, a browser user agent and redirects followed.

`111` unique URLs: OK 110, BLOCKED 1.

| status | url | entries |
|---|---|---|
| BLOCKED | https://www.w3.org/TR/webauthn-3/ | d04-webauthn |

## Seven were broken on first check, and two of them were my fault

1. **OWASP API Security pages returned 404 without a trailing slash.** `.../0xa1-...md` and `.../0xa1-.../` differ; only the slashed form resolves. Two entries fixed.
2. **`docs.mitmproxy.org/` returns 404, `/stable/` returns 200.** Fixed in three entries across D04, D05 and D31.
3. **Two URLs I wrote were wrong and had to be replaced rather than repaired:**
   - `portswigger.net/bappstore/jwt-editor` is not a real BApp path. Guessed slugs do not resolve. Now links the store with a note to search.
   - `github.com/Noisyfox/wxapkg-unpacker` **does not exist**. I invented it. Replaced with a GitHub search URL and marked PROBABLE, because no single canonical unpacker repo was verified.
4. **`frida.re` does not resolve from this host at all.** Not dead, but unverifiable here, so the link now points at `github.com/frida/frida` which is stable.
5. **`w3.org/TR/webauthn-3/` returns 403 to automated clients.** That is the site refusing bots, not a dead link, and is recorded as BLOCKED rather than DEAD.

## The lesson, again

A guessed URL is indistinguishable from a real one until it is fetched. Three of the seven failures looked perfectly plausible: a BApp deep link, a GitHub repo under a plausible name, and a documentation root. The repo now has a check that catches all three classes, and the two invented ones are recorded as inventions rather than quietly fixed.

---

# Final domain link sweep (2026-10-27)

213 unique URLs across all 28 authored domains: OK 209, DEAD 2, BLOCKED 1, ERR 1.

Four problems found and fixed:

1. `docs.mitmproxy.org/` still appeared in D22, D29 and D31 after the earlier fix. It is `/stable/` that resolves.
2. `frida.re/docs/` does not resolve from this host at all. Now points at `github.com/frida/frida`.
3. `github.com/dev2be/awesome-favicon-hash` **does not exist.** That is the second invented repository in this project. The entry is now `Favicon hash via httpx -favicon`, because httpx genuinely implements it and is verified.
4. `w3.org/TR/webauthn-3/` returns 403 to automated clients, which is refusal not death, recorded BLOCKED.

## Standing rule

A URL that has not been fetched is a hypothesis. Two invented repositories and one guessed BApp slug is enough evidence for that. Every URL in this repo now has a fetch date behind it.

---

# Final verification sweep (2026-10-27, round 38)

Full pipeline, all 13 stages, then every URL in every authored domain.

```
parse        31,298 rows
corpus       21,397 by url, 21,194 by tool identity
reconcile    13,575 admitted + 17,516 excluded + 204 held + 3 residue, identity holds
taxonomy     624 of 706 mapped (88.4%)
tools        64, 0 unresolved
bootstrap    11 scripts generated
domains      28 authored + 9 pointers, validator passes
links        264 of 265 live
```

The only non-live URL is `https://www.w3.org/TR/webauthn-3/` returning 403 to automated clients.
That is the W3C refusing bots, not a dead link, recorded BLOCKED.

Nothing was fixed this round because nothing was broken. That is the first verification pass in this
project where the answer was 'clean', and it took nine rounds of finding defects to get here.

Standing rule, unchanged: a URL that has not been fetched is a hypothesis.
