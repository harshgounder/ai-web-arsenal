# Security policy

## What this repository is

Methodology and tooling for testing web platforms **you own or have written authorisation to test**.
Every pattern in the companion atlas carries an `authorization` field stating that requirement.

## What it is not

It is not a service, it has no runtime, and it collects nothing. It ships no credentials, no API keys and
no targeting data.

## Reporting a problem in this repository

Open an issue for a broken install command, a dead link or an incorrect claim. Those are defects and
they get fixed.

If you believe a technique here is described at a level that crosses from methodology into operational
harm, open an issue titled `scope concern` and quote the entry id. That is a legitimate defect report.

## Before you run anything

1. Confirm you own the target or hold written permission, and record it.
2. Read the domain's decision tree. Several branches say **stop**, and they mean it. D09 smuggling on
   shared infrastructure is an incident, not a test.
3. Respect rate limits. An agent that ignores rate is a denial of service with a README.
4. Never run credential collection tooling (`ssh-mitm`) against users who have not consented.

## Known limits

- `w3.org` refuses automated clients with 403. That is recorded as `BLOCKED`, not as a dead link.
- `masscan` defaults are unsafe for a production network. Set `--rate` explicitly, always.
- `cloudscraper` only handles the legacy challenge. Failure is data about the defence, not a tool bug.
