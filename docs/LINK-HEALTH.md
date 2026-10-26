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
