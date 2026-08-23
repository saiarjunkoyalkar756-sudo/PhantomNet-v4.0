# Gate 3 — Safe BAS Incident-Workflow Evidence Template

## Scope and safety declaration

| Field | Operator-recorded value |
|---|---|
| Run identifier | `<lab-run-id>` |
| Operator and approval reference | `<owner-and-reference>` |
| Code identity | `<commit-sha>`, `<branch>`, `<migration-head>` |
| Environment | `<isolated-lab-only>` |
| Production target, credential, customer data, malware, exploit, or command execution used | **No** — record an immediate stop result if this cannot be truthfully stated. |
| Response configuration | `<all-disabled>` or `<one-reviewed-mock-or-lab-adapter>` |
| Fixture content digest | `<sha256-of-sanitized-fixture-set>` |

> This template records evidence. It does not authorize a response action, endpoint modification, network connection, credential use, exploit, persistence technique, or lateral movement.

## Selected fixtures and expected deterministic evidence

| Scenario ID | Expected technique | Expected rule ID | Fixture safety boundary | Run result |
|---|---|---|---|---|
| `BAS-AUTH-001` | `T1110` | `bas.auth.repeated-failures` | Five synthetic authentication-failure fields only | `<pass/fail/not-run>` |
| `BAS-PROC-001` | `T1059` | `bas.process.unexpected-lineage` | Named lab process-lineage metadata only | `<pass/fail/not-run>` |
| `BAS-DNS-001` | `T1071.004` | `bas.dns.high-entropy-query` | `.example.test` DNS telemetry only | `<pass/fail/not-run>` |
| `BAS-NET-001` | `T1071.001` | `bas.network.unexpected-outbound` | Documentation-range network metadata only | `<pass/fail/not-run>` |
| `BAS-FILE-001` | `T1565.001` | `bas.file.sensitive-modification` | `/tmp/phantomnet-lab-sensitive.txt` metadata only | `<pass/fail/not-run>` |
| `BAS-SCHED-001` | `T1053.005` | `bas.execution.controlled-scheduled-task` | Documentation-only task metadata; no task creation | `<pass/fail/not-run>` |
| `BAS-RDP-001` | `T1021.001` | `bas.lateral-movement.controlled-rdp-failures` | Synthetic RDP failure telemetry only; no remote login attempt | `<pass/fail/not-run>` |
| `BAS-DISC-001` | `T1083` | `bas.discovery.controlled-lab-tree` | Bounded `/tmp/phantomnet-lab-tree` inventory metadata only | `<pass/fail/not-run>` |

## Canonical workflow observations

| Evidence field | Sanitized value |
|---|---|
| Fixture scenario identifier | `<scenario-id>` |
| Canonical event identifier | `<event-id>` |
| Normalized event identifier / hash | `<normalized-evidence>` |
| Detection identifier and rule version | `<detection-id-and-rule-version>` |
| MITRE evidence technique and rationale | `<technique-and-rationale>` |
| Alert and case identifiers, if created | `<tenant-scoped-identifiers-only>` |
| Analyst trace and priority factors | `<sanitized-summary>` |
| Decision identifier, if advisory evaluation occurred | `<decision-id-or-not-applicable>` |
| Detection latency boundary and elapsed time | `<defined-boundary-and-duration>` |
| False positive, miss, or unexpected result | `<explicit-result-or-none>` |

## Optional governed response observation

Leave this section **not applicable** unless a single reviewed mock or isolated lab adapter is explicitly enabled after the detection workflow completes.

| Field | Sanitized value |
|---|---|
| Containment request identifier | `<request-id>` |
| Human approval identifier and timestamp | `<approval-id-and-time>` |
| Audit key identifier and chain verification result | `<key-id-and-result>` |
| Adapter preflight, verification, and rollback receipt identifiers | `<identifiers-only>` |
| Scope confirmation | `<single-approved-lab-target>` |
| Cleanup confirmation | `<rollback-and-resource-cleanup-result>` |

## Conclusion and limits

State exactly what the run proved and what it did not prove. A successful BAS fixture run proves only the exercised isolated workflow. It does not prove production detection efficacy, model efficacy, live Wazuh or AWS behavior, endpoint effectiveness, absence of false positives, or autonomous containment.
