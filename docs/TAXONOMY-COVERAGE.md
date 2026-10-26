# Taxonomy coverage

Every test ID from six taxonomies, mapped onto the 16 atoms in `web-attack-atlas`. If a taxonomy item
maps to an atom, the atlas can address it by construction. Unmapped items are the gap list, printed
in full at the bottom, not swept up.

Generated 2026-10-26 by `scripts/taxonomy-reconcile.py`.

**`624` of `706` items mapped, `88.4%`.**

| taxonomy | items | mapped | unmapped | coverage |
|---|---|---|---|---|
| OWASP Web Security Testing Guide | 131 | 112 | 19 | 85% |
| OWASP ASVS | 17 | 11 | 6 | 65% |
| Bugcrowd VRT | 437 | 416 | 21 | 95% |
| OWASP API Security Top 10 (2023) | 10 | 8 | 2 | 80% |
| MITRE ATLAS | 101 | 69 | 32 | 68% |
| OWASP LLM Top 10 | 10 | 8 | 2 | 80% |

## Atom distribution across all taxonomies

| atom | name | items |
|---|---|---|
| A15 | configuration divergence | 233 |
| A01 | interpreter confusion | 137 |
| A03 | identity confusion | 128 |
| A08 | information exposure | 110 |
| A16 | model and agent manipulation | 94 |
| A02 | trust boundary crossing | 55 |
| A09 | cryptographic weakness | 55 |
| A07 | resource exhaustion | 32 |
| A10 | logic assumption violation | 29 |
| A06 | path and namespace confusion | 23 |
| A05 | type and shape confusion | 16 |
| A04 | state confusion | 14 |
| A11 | dependency compromise | 12 |
| A13 | side channel | 7 |
| A12 | timing and ordering | 6 |
| A14 | human manipulation | 3 |

No atom is unused, which means the 16 primitive set is not over-fitted to one series.

## Corrections made while building this

Three numbers that were circulating in this project turned out to be wrong, and are corrected here

rather than quietly replaced:

1. **ASVS is not 240 requirements.** 240 is the count of markdown files in the ASVS repo, and only 49
   are under `en/`, and those are prefaces and headers. Requirement level reconciliation needs the 5.0
   chapter content, which failed to clone twice. Current state is chapter level, 17 chapters, 11 mapped.
   Stated as 17, not 240.
2. **VRT is not 581 tests.** 581 is total nodes including containers. 437 are leaves, and the leaves are
   qualifiers (`Long Timeout`, `Over HTTP`, `Relay`) whose meaning only exists with the parent path.
   Matching on the leaf alone was the bug, fixing it took VRT from 53% to 95%.
3. **API Top 10 has 10 items, not 9.** The tenth file is `0xaa`, hexadecimal, and a decimal-only regex
   silently dropped it.

## The unmapped list

These are the real gaps. Each is either a taxonomy item the atom set does not describe, or a name that
needs a rule. They are kept visible.

### OWASP Web Security Testing Guide (19 unmapped)

| id | title |
|---|---|
| `WSTG-IDEN-02` | User Registration Process |
| `WSTG-IDEN-03` | Account Provisioning Process |
| `WSTG-SESS-05` | Cross Site Request Forgery |
| `WSTG-INJE-XX` | 05.5-MS Access |
| `WSTG-INJE-XX` | 05.8-Client-side |
| `WSTG-INJE-19` | Server-Side Request Forgery |
| `WSTG-BUSI-05` | Number of Times a Function Can Be Used Limits |
| `WSTG-BUSI-07` | Defenses Against Application Misuse |
| `WSTG-BUSI-09` | Upload of Malicious Files |
| `WSTG-BUSI-10` | Payment Functionality |
| `WSTG-CLIE-08` | Cross Site Flashing |
| `WSTG-CLIE-09` | Clickjacking |
| `WSTG-CLIE-10` | WebSockets |
| `WSTG-CLIE-11` | Web Messaging |
| `WSTG-CLIE-12` | Browser Storage |
| `WSTG-CLIE-14` | Reverse Tabnabbing |
| `WSTG-APIT-XX` | 00-API Testing Overview |
| `WSTG-APIT-01` | API Reconnaissance |
| `WSTG-APIT-99` | GraphQL |

### OWASP ASVS (6 unmapped)

| id | title |
|---|---|
| `ASVS-V3` | Web Frontend Security |
| `ASVS-V4` | API and Web Service |
| `ASVS-V5` | File Handling |
| `ASVS-V12` | Secure Communication |
| `ASVS-V14` | Data Protection |
| `ASVS-V17` | WebRTC |

### Bugcrowd VRT (21 unmapped)

| id | title |
|---|---|
| `algorithmic_biases-aggregation_bias` | Algorithmic Biases > Aggregation Bias |
| `algorithmic_biases-processing_bias` | Algorithmic Biases > Processing Bias |
| `cloud_security-logging_and_monitoring_issues-disabled_or_ins` | Cloud Security > Logging and Monitoring Issues > Disabled or Insufficient Logging |
| `cross_site_request_forgery_csrf-application_wide` | Cross-Site Request Forgery (CSRF) > Application-Wide |
| `cross_site_request_forgery_csrf-flash_based` | Cross-Site Request Forgery (CSRF) > Flash-Based |
| `data_biases-pre_existing_bias` | Data Biases > Pre-existing Bias |
| `data_biases-representation_bias` | Data Biases > Representation Bias |
| `developer_biases-implicit_bias` | Developer Biases > Implicit Bias |
| `external_behavior-browser_feature-autocomplete_enabled` | External Behavior > Browser Feature > Autocomplete Enabled |
| `external_behavior-browser_feature-autocorrect_enabled` | External Behavior > Browser Feature > Autocorrect Enabled |
| `external_behavior-captcha_bypass-crowdsourcing` | External Behavior > Captcha Bypass > Crowdsourcing |
| `indicators_of_compromise` | Indicators of Compromise |
| `insecure_data_transport-cleartext_transmission_of_sensitive_` | Insecure Data Transport > Cleartext Transmission of Sensitive Data |
| `insecure_os_firmware-failure_to_remove_sensitive_artifacts_f` | Insecure OS/Firmware > Failure to Remove Sensitive Artifacts from Disk |
| `insecure_os_firmware-kiosk_escape_or_breakout` | Insecure OS/Firmware > Kiosk Escape or Breakout |
| `insecure_os_firmware-recovery_of_disk_contains_sensitive_mat` | Insecure OS/Firmware > Recovery of Disk Contains Sensitive Material |
| `insecure_os_firmware-weakness_in_firmware_updates-firmware_c` | Insecure OS/Firmware > Weakness in Firmware Updates > Firmware cannot be updated |
| `insecure_os_firmware-weakness_in_firmware_updates-firmware_d` | Insecure OS/Firmware > Weakness in Firmware Updates > Firmware does not validate update in |
| `misinterpretation_biases-context_ignorance` | Misinterpretation Biases > Context Ignorance |
| `societal_biases-confirmation_bias` | Societal Biases > Confirmation Bias |
| `societal_biases-systemic_bias` | Societal Biases > Systemic Bias |

### OWASP API Security Top 10 (2023) (2 unmapped)

| id | title |
|---|---|
| `API7:2023` | Server Side Request Forgery |
| `API9:2023` | Improper Inventory Management |

### MITRE ATLAS (32 unmapped)

| id | title |
|---|---|
| `AML.T0000` | Search Open Technical Databases |
| `AML.T0003` | Search Victim-Owned Websites |
| `AML.T0004` | Search Application Repositories |
| `AML.T0006` | Active Scanning |
| `AML.T0016` | Obtain Capabilities |
| `AML.T0017` | Develop Capabilities |
| `AML.T0008` | Acquire Infrastructure |
| `AML.T0019` | Publish Poisoned Datasets |
| `AML.T0021` | Establish Accounts |
| `AML.T0011` | User Execution |
| `AML.T0012` | Valid Accounts |
| `AML.T0025` | Exfiltration via Cyber Means |
| `AML.T0034` | Cost Harvesting |
| `AML.T0037` | Data from Local System |
| `AML.T0042` | Verify Attack |
| `AML.T0043` | Craft Adversarial Data |
| `AML.T0048` | External Harms |
| `AML.T0049` | Exploit Public-Facing Application |
| `AML.T0059` | Erode Dataset Integrity |
| `AML.T0060` | Publish Hallucinated Entities |
| `AML.T0072` | Reverse Shell |
| `AML.T0074` | Masquerading |
| `AML.T0075` | Cloud Service Discovery |
| `AML.T0078` | Drive-by Compromise |
| `AML.T0079` | Stage Capabilities |
| `AML.T0088` | Generate Deepfakes |
| `AML.T0089` | Process Discovery |
| `AML.T0095` | Search Open Websites/Domains |
| `AML.T0097` | Virtualization/Sandbox Evasion |
| `AML.T0105` | Escape to Host |
| `AML.T0107` | Exploitation for Defense Evasion |
| `AML.T0112` | Machine Compromise |

### OWASP LLM Top 10 (2 unmapped)

| id | title |
|---|---|
| `LLM05` | Improper Output Handling |
| `LLM06` | Excessive Agency |

