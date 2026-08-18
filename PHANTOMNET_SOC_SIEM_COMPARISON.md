# PhantomNet Compared with SOC, SIEM, XDR, and SOAR Platforms

## Executive assessment

**PhantomNet is currently a promising pre-production security-platform codebase, not yet a substitute for a mature SOC platform.** Its repository has an ambitious self-hosted architecture: a FastAPI microservice grid, PostgreSQL, Redis, Redpanda, Neo4j, two web frontends, an endpoint-agent codebase, a blockchain audit layer, and modules for ingestion, correlation, playbooks, BAS, case management, threat intelligence, and graph analysis. The architecture is broader than a typical early-stage SIEM prototype.

However, architectural breadth is not the same as operational maturity. Current validation demonstrates only a constrained local firewall rule that accepts RFC 5737 documentation addresses, verifies the exact rule, writes an audit record, and rolls it back. Host isolation and process termination correctly return failure until a real EDR or endpoint-management provider is implemented. Full test collection now succeeds, but the full suite remains at **68 passed, 19 failed, and 11 errors**. [1] [2]

> The appropriate near-term position is **self-hosted security-operations platform and research framework**, rather than “production autonomous XDR/SIEM.”

## Comparison scope and terminology

A **SIEM** centralizes telemetry, normalizes it, correlates detections, and supports investigation. **XDR** adds coordinated detection and response across endpoint, identity, cloud, network, and other domains. **SOAR** supplies playbooks, orchestration, approvals, case workflows, and integrations that execute response actions. A SOC platform combines these capabilities with scalable operations, content lifecycle, governance, resilience, and analyst workflow.

The comparison uses four mature reference points: Microsoft Sentinel as a cloud-native SIEM/SOAR platform, Splunk Enterprise Security as an enterprise SIEM benchmark, Google Security Operations as a high-scale normalized-data and API benchmark, CrowdStrike Falcon Next-Gen SIEM as an XDR-native SOC benchmark, and Wazuh as an open-source SIEM/XDR and endpoint-response benchmark. The vendors’ own performance and cost claims are not treated as independent validation.

## Platform snapshot

| Platform | Deployment model | Core position | Documented mature differentiator | Relative implication for PhantomNet |
|---|---|---|---|---|
| **PhantomNet** | Self-hosted microservices and local agents | Ambitious SIEM/XDR/SOAR research platform | Customizable architecture, local-only verified firewall-rule adapter, graph and blockchain concepts | Strong experimental breadth; insufficient production proof today. |
| **Microsoft Sentinel** | Managed cloud service | Cloud-native SIEM with automation and unified operations | Connectors, normalization, analytics, UEBA, KQL hunting, incident workflow, playbooks, and automated response [3] | Far ahead in managed operations, data lifecycle, integrations, detection content, and operational governance. |
| **Splunk Enterprise Security** | Enterprise self-managed or cloud ecosystem | Enterprise SIEM and analyst workbench | Triage, investigations, response plans, automation, risk-based alerting, and threat-intelligence investigation [4] | Far ahead in analytics maturity, risk aggregation, workflow, content, and ecosystem depth. |
| **Google Security Operations** | Managed cloud service | High-scale SIEM/SOAR and threat intelligence platform | Normalizes, indexes, correlates, and analyzes security/network telemetry; exposes search, detection, ingestion, and unified-data-model APIs [5] | Far ahead in scalable data model discipline, search, API maturity, and operating model. |
| **CrowdStrike Falcon Next-Gen SIEM** | Managed, XDR-native platform | AI-native SOC and XDR-centric SIEM | Unified detection/response, centralized case management, third-party data, and integrated SOAR workflows [6] | Far ahead in integrated endpoint telemetry, response provider maturity, and managed XDR operations. |
| **Wazuh** | Open source, self-hosted or SaaS | Open-source SIEM/XDR | Agent-mediated active response, configurable trigger rules, stateful reversal, whitelist controls, and documented endpoint use cases [7] | The closest architectural comparator, yet ahead in real endpoint response, deployment maturity, and operator documentation. |

## Capability matrix

The labels below distinguish **implemented and validated**, **implemented but not yet production-proven**, and **mature reference capability**. They do not indicate a feature-for-feature procurement score.

| Capability | PhantomNet current evidence | Mature-platform benchmark | Assessment |
|---|---|---|---|
| Telemetry collection and ingestion | Backend services and endpoint-agent collectors exist; full infrastructure stack is defined. End-to-end availability is not yet demonstrated in this sandbox. [1] | Sentinel connectors and collection; Google SecOps ingestion/API; Splunk data ecosystem; Falcon third-party data. [3] [4] [5] [6] | **Prototype / integration gap.** Define stable schemas, connector contracts, health checks, replay, and data-quality SLOs. |
| Normalization and correlation | Event normalization and correlation components are present in the repository; cross-service validation is incomplete. | Sentinel normalization, Google SecOps UDM, Splunk CIM/RBA, vendor detection content. [3] [4] [5] | **Concept present; production data model unproven.** Prioritize an explicit common schema and deterministic correlation test corpus. |
| Detection engineering and hunting | MITRE mapper, query-engine components, BAS, and threat-intelligence modules are present. Repository defects and test failures constrain confidence. | Built-in/custom analytics, UEBA, KQL hunting, risk-based alerting, detection engine APIs. [3] [4] [5] | **Early-stage.** Build versioned detection-as-code, simulation-backed regression tests, tuning and false-positive measurement. |
| Investigation and case management | Case-management and dashboard components exist. | Formal triage, investigations, response plans, tasks, cases, collaboration. [3] [4] [6] | **Partial.** Implement a unified incident state machine, evidence retention, timelines, ownership, SLAs, and escalation workflows. |
| SOAR and response | Playbook engine exists. A safe local `iptables` adapter now applies/verifies/rolls back rules only for documentation addresses. Host isolation and process termination are not implemented with real providers. [2] | Sentinel playbooks, Splunk actions/playbooks, Falcon Fusion SOAR, Wazuh agent active response. [3] [4] [6] [7] | **Validated local mechanism; not production containment.** Add authenticated firewall, EDR, IAM, and ticketing provider adapters with approvals and outcome checks. |
| Endpoint / XDR coverage | Cross-platform agent code and collectors exist, but deployment/runtime verification is incomplete. | Falcon’s native XDR telemetry; Wazuh’s managed agents and configured endpoint response. [6] [7] | **Not yet XDR-equivalent.** Secure agent lifecycle, device identity, health telemetry, signed commands, and provider-backed actions are required. |
| Threat intelligence | Modules for threat intelligence and MITRE mapping are present; World Intel MCP is a viable future read-only enrichment source. | Mature vendor content, indicator lifecycle, investigation context, and enrichment. [3] [4] [6] | **Promising.** Preserve source provenance, confidence, expiry, deduplication, and analyst review. Do not trigger containment directly from enrichment. |
| Search, scale, resilience | Redpanda, PostgreSQL, Redis, and Neo4j are architected; production load, retention, recovery, and multi-tenancy are not validated. | Managed large-scale telemetry search/correlation and mature operations. [3] [5] [6] | **Major maturity gap.** Establish sizing, retention, replay, backup/recovery, observability, and chaos/load tests. |
| Security governance | Security concepts and audit logging exist; tests flag dependency/configuration and reliability gaps. | Mature SaaS/enterprise controls, role models, support, release operations, and content governance. | **Major maturity gap.** Add RBAC, tenant boundaries, secret rotation, audit immutability verification, upgrade policy, threat modeling, and security release gates. |

## Where PhantomNet is differentiated

PhantomNet’s principal advantage is **composability**. The platform is not restricted to a single vendor’s telemetry, query language, endpoint sensor, or control plane. Its proposed combination of event streaming, graph analysis, blockchain-style audit evidence, BAS, autonomous response concepts, and pluggable enrichment could be differentiated for a research lab, a controlled private deployment, or an organization needing deep customization.

The platform also has a useful reliability improvement: response code now distinguishes planned action from enforced action. The local adapter returns whether an action was actually enforced and verified, rejects unsafe targets, and supports rollback. This is the right pattern to carry into production provider adapters. [2]

## Where PhantomNet trails mature tools

The largest gap is not user interface breadth or the count of microservices; it is **operational evidence**. Mature platforms package validated data connectors, durable schemas, detection content, permissions, cases, integrations, deployment tooling, documentation, support, monitoring, and response mechanisms. Wazuh, for example, documents endpoint-triggered active response, stateful reversal, whitelisting, and real use cases; PhantomNet currently has only a sandbox-scoped firewall action and no provider-backed EDR isolation. [7]

A second gap is **test and release quality**. PhantomNet now collects 98 tests, but the current full test result contains unresolved failures/errors. No production claim should be made until the suite is reliable, containerized integration tests are reproducible, and each claimed detection/response path has success, failure, rollback, and audit verification cases. [1]

A third gap is **data and ecosystem maturity**. Sentinel, Splunk, Google SecOps, and Falcon are designed around large connector ecosystems, normalized data models, investigation workbenches, and managed operations. PhantomNet needs to make its own shared schema, integration contracts, and operational SLOs first-class product assets before its microservice architecture becomes an advantage.

## Practical positioning

| Use case | Fit today | Rationale |
|---|---|---|
| Security R&D, university lab, or controlled BAS environment | **Good fit with guardrails** | The codebase is flexible and supports experimentation. Keep all response actions scoped and reversible. |
| Internal prototype for a custom SOC workflow | **Conditional fit** | Appropriate after test stabilization, schema definition, and specific provider integrations. |
| Replacement for a production SIEM/XDR platform | **Not ready** | Core production capabilities and evidence are incomplete. |
| Complementary enrichment, simulation, or custom orchestration layer beside an existing SIEM | **Potentially strong** | This is the best near-term product position: integrate read-only enrichment and human-approved SOAR with existing controls. |

## Recommended roadmap

### 1. Establish a production-grade core

First, make the existing platform reliable. Reduce the full-suite failures to zero, remove hard-coded test paths, standardize asynchronous transport interfaces, repair honeypot/plugin/collector tests, and run the suite in a clean CI environment. Turn the Docker stack into a repeatable integration test that validates ingestion, normalization, correlation, case creation, playbook execution, outcome verification, and rollback.

### 2. Treat the data model as a product

Publish a versioned common event schema, an entity model, enrichment provenance fields, confidence and expiration semantics, and a rule/detection contract. Build parsers and connectors around that schema. This closes the largest structural gap against Sentinel-style normalization, Google SecOps UDM-style discipline, and Splunk-style common information models. [3] [4] [5]

### 3. Build provider-backed response adapters

Promote the local adapter’s safety pattern into real integrations: a firewall provider, an EDR endpoint provider, an IAM provider, a ticketing provider, and notification provider. Every action should require target validation and role/policy authorization; return a provider-issued action ID; verify actual state; support idempotency and rollback where feasible; preserve a tamper-evident audit trail; and gate high-impact actions behind human approval.

### 4. Position World Intel MCP correctly

Use World Intel MCP only as **read-only threat/context enrichment**. Retain source citations, timestamp and cache intelligence, score confidence, and require correlation with local evidence before creating a case or recommending a playbook. Do not allow intelligence output alone to block an IP, isolate a host, or terminate a process.

### 5. Compete by augmentation, not replacement

The most credible market path is to position PhantomNet as a customizable **security enrichment, BAS, and controlled orchestration layer** alongside a mature SIEM/XDR. It can differentiate through custom analytics, graph context, local/private deployment patterns, and transparent action verification while the foundational SOC platform remains the authoritative telemetry and incident system.

## References

[1]: PHANTOMNET_VALIDATION_REPORT.md "PhantomNet validation report"
[2]: PHANTOMNET_ENFORCEMENT_IMPLEMENTATION_REPORT.md "PhantomNet local enforcement implementation report"
[3]: https://learn.microsoft.com/en-us/azure/sentinel/ "Microsoft Sentinel documentation"
[4]: https://help.splunk.com/en/splunk-enterprise-security-8/user-guide/8.1/introduction/get-started-with-splunk-enterprise-security "Splunk Enterprise Security documentation"
[5]: https://docs.cloud.google.com/chronicle/docs/siem "Google Security Operations SIEM documentation"
[6]: https://www.crowdstrike.com/en-us/platform/next-gen-siem/ "CrowdStrike Falcon Next-Gen SIEM"
[7]: https://documentation.wazuh.com/current/user-manual/capabilities/active-response/index.html "Wazuh Active Response documentation"
