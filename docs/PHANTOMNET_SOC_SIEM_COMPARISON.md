# PhantomNet Compared with SIEM and SOC Platforms

**Assessment date:** 19 August 2026
**Scope:** Product-positioning and engineering comparison; not a procurement scorecard or substitute for a proof of concept.

## Executive perspective

**PhantomNet should not claim feature parity with Splunk Enterprise Security, Microsoft Sentinel, Elastic Security, Wazuh, or Security Onion today.** Those platforms have mature deployment operations, large integration or content ecosystems, and production evidence developed over many years. PhantomNet’s credible position is narrower and more distinctive: a **self-hosted, composable, governance-first SOC** for teams that want to own their deployment, data path, response controls, and audit evidence rather than accept a vendor-defined control plane.

The strongest present differentiation is not generic “AI.” It is the combination of a canonical event pipeline, graph-oriented context, tenant-scoped controls, human approval for high-impact response, HMAC-backed containment evidence, and an explicit fail-closed policy when an adapter cannot prove enforcement. The latest repository validation has **288 passing tests**, while Docker/LocalStack-dependent evidence remains explicitly gated rather than claimed as complete. [Production-Readiness Validation](PRODUCTION_READINESS_VALIDATION.md)

> **Positioning statement:** *Capable, composable, yours — an AI-native, self-hosted SOC where every high-impact response remains accountable to a human approval and verifiable evidence trail.*

## Comparison lens

This comparison separates **validated current PhantomNet capability** from roadmap intent. A checkmark in a competitor column means the vendor documents the capability; it does not imply that every edition, deployment option, or subscription includes it. “Partial” for PhantomNet means a real implementation boundary or test exists but is not yet proven as a complete production service.

| Dimension | PhantomNet v4.0 — current evidence | Splunk Enterprise Security | Wazuh | Microsoft Sentinel | Elastic Security | Security Onion |
|---|---|---|---|---|---|---|
| Primary model | Self-hosted, composable SOC platform | Commercial unified TDIR/SIEM platform | Open-source SIEM/XDR | Cloud-native SIEM/SOAR | SIEM/XDR with native automation | Open-source NSM/SOC platform |
| Control plane and data ownership | Operator-hosted; PostgreSQL, Redis, Redpanda, Neo4j, and services are intended to be deployable in the team’s environment | Enterprise or cloud deployment model | Operator-deployed server, indexer, dashboard, and agents | Microsoft Azure/Defender control plane | Cloud, self-managed, and air-gapped options documented | Operator-deployed manager, sensor, and search topology |
| Ingestion and normalization | Versioned canonical event schema and broker ingestion are validated | Mature real-time SIEM collection and data management | Agent and log collection, decoders, rules, indexer | Connectors, custom connectors, Syslog/CEF/REST, ASIM normalization | Broad integration and schema capabilities | Network sensors, Elastic Agent, Syslog, Logstash/Elasticsearch |
| Detection, hunting, and MITRE context | MITRE-aligned evidence, BAS fixtures, correlation, PNQL/hunting components; content library remains early | Detection Studio, risk-based alerting, UEBA, ATT&CK visualization, extensive content | Rules, decoders, ATT&CK mapping, threat hunting, vulnerability and configuration analysis | Analytics, ATT&CK coverage, hunting, threat intelligence, UEBA | Detection rules, ATT&CK mapping, hunting, entity analytics, AI-assisted analysis | Suricata/Zeek/NIDS, Sigma/YARA tuning, hunt, PCAP analysis |
| Investigation and case workflow | Alert workflow, case lifecycle, playbooks, graph/attack-path modules | Analyst queue, threat topology, investigations, cases, SOAR workbooks | Dashboard and API workflows; broader case workflow is less central than its endpoint/XDR strengths | Incidents, entity graph, notebooks, hunting, Defender portal workflow | Timeline, event analyzer, Session View, Osquery, Cases | Alerts, dashboards, Hunt, PCAP, Cases, CyberChef |
| Response model | **Approval-gated** high-impact actions; HMAC audit evidence required; verified rollback model | Adaptive response, SOAR playbooks and response plans | Alert-triggered active-response scripts | Automation rules and Azure Logic Apps playbooks | Workflows, response actions, and human approval/verification positioning | Primarily investigation and NSM; integrations/host tooling vary by deployment |
| Endpoint / EDR | Inventory and telemetry boundaries exist; local firewall and AWS SG adapters are tested; live EDR isolation is **not configured or validated** | Integrates with broad security stack | Multi-platform Wazuh agent with endpoint telemetry and response | Connects to Microsoft and third-party sources; paired Defender ecosystem is a major advantage | Native Elastic Defend/endpoint capability | Elastic Agent, osquery, and host telemetry; strength remains network-centric |
| Audit and governance | Tenant isolation, immutable audit records, HMAC verification, approval separation, fail-closed adapter behavior | Enterprise controls and workflow governance | RBAC, API, agent and configuration controls | Azure identity/control-plane governance and append-only data practices | Role controls, cases, workflows, and auditable AI positioning | MFA/RBAC documented; case history and observable tracking |
| AI posture | AI-native design direction; behavioral and graph modules exist, but no production model-evaluation claim | AI assistant and agentic SOC capabilities documented; availability varies by edition/deployment | AI capabilities are emerging, but core value is open XDR/SIEM | AI/ML and UEBA embedded in Microsoft security ecosystem | Strong current agentic-SOC and transparent-reasoning product position | AI is not its primary differentiator; network/forensics depth is |
| Production proof status | Unit/integration coverage is strong; live Docker topology, recovery, vendor EDR, and external assessment remain gated | Mature commercial product | Mature open-source platform | Mature managed cloud service | Mature commercial/self-managed platform | Mature open-source NSM platform |

## Where PhantomNet is already competitive

### Governance-first response

PhantomNet’s most defensible engineering choice is that high-impact containment is not treated as a generic automation problem. The request, approval, execution, verification, and rollback sequence is separately represented, and signed audit evidence is required for execution. The stress suite repeats this complete lifecycle 24 times and validates the resulting HMAC chain. This is a meaningful differentiator for regulated, cautious, or small security teams that value **proof of what the platform did** over opaque “automation succeeded” messages.

This differs from the default automation emphasis in larger platforms. Splunk documents response plans, adaptive response, SOAR playbooks, and a large action ecosystem.[1] Microsoft Sentinel documents rules and Logic Apps playbooks that can run automatically on alerts or incidents.[6] Wazuh Active Response executes scripts in response to alerts.[5] These are mature models, but PhantomNet can compete on making **approval and verifiable evidence mandatory policy primitives** for selected actions, not optional runbook conventions.

### Composability and self-hosted control

Wazuh and Security Onion demonstrate that open-source, self-hosted security operations are viable. Wazuh combines endpoint agents with central server, indexer, and dashboard components, while Security Onion combines network sensors, host telemetry, full packet capture, and analyst tooling.[3] [12] PhantomNet’s distinct architecture is an API-first microservice composition with explicit PostgreSQL, Redis, Redpanda/Kafka, Neo4j, and React/Next.js boundaries. This makes it a better fit for teams that want to adapt event, graph, case, and response components independently rather than adopt a monolithic appliance-style security stack.

### Evidence-oriented security engineering

The current project has unusually explicit testable invariants for a young SOC platform: tenant isolation, HMAC key binding, audit-chain mutation detection, session-to-user and tenant JWT binding, dead-letter recovery, broker retry/idempotency, and adapter verification. These are not substitutes for production operations, but they are a strong foundation for building a system that can be audited and evolved safely.

## Where established platforms are ahead

| Gap | Why established platforms lead | What PhantomNet must do |
|---|---|---|
| Endpoint protection and EDR | Wazuh, Elastic, and Microsoft ecosystems have production endpoint agents, operational tooling, and established response paths. [3] [11] | Implement one provider-backed EDR path in an authorized lab, including observed-state verification and rollback; do not call a message-bus acknowledgment “isolation.” |
| Content and connectors | Splunk, Sentinel, and Elastic have broad documented connectors, detection content, and field-tested ecosystems. [1] [6] [9] | Build a curated core pack: identity, endpoint, cloud, network, and SaaS sources; version and test every rule. |
| Scale and operator experience | The incumbents document clustering, high-volume ingestion, mature queues, workflow UIs, and years of field operations. [4] [13] | Complete Docker-host topology/recovery evidence, benchmark with real services, document capacity envelopes, and add operational SLOs. |
| AI maturity | Elastic, Splunk, and Microsoft package AI/ML with established data ecosystems, product workflows, and support models. [2] [8] [9] | Treat AI as an assistive, evaluated capability: publish model boundaries, prompt/data handling, test sets, false-positive analysis, and human override behavior. |
| Procurement readiness | Commercial platforms offer support, SLAs, compliance artifacts, and established buyer processes. | Publish hardening guidance, upgrade/backup/restore policy, SBOM, support model, deployment reference architecture, and a clear threat model. |

## Platform-by-platform assessment

### Versus Splunk Enterprise Security

Splunk Enterprise Security is the broadest benchmark for a mature TDIR suite. Splunk documents SIEM, SOAR, UEBA, risk-based alerting, Detection Studio, threat topology, cases, response plans, and a substantial SOAR integration catalog.[1] Its advantage is feature depth, content maturity, and enterprise operating experience. PhantomNet should not compete on “more features than Splunk.”

PhantomNet’s opportunity is the customer segment that wants a simpler, ownable security control plane and values auditable response governance more than a global app marketplace. Its path to credibility is a tightly scoped self-hosted package, not an attempt to clone every Splunk product surface.

### Versus Wazuh

Wazuh is the closest open-source comparator for endpoint-centric SIEM/XDR. It documents agents, inventory, vulnerability detection, configuration assessment, file-integrity monitoring, threat hunting, cloud monitoring, compliance use cases, and active response.[3] Wazuh is decisively ahead in deployed endpoint coverage and practical out-of-the-box security operations.

PhantomNet can complement Wazuh before it tries to replace it: ingest Wazuh telemetry, add governed cross-domain correlation, graph context, case work, and high-assurance response evidence. The immediate strategic move is **Wazuh-compatible ingestion plus a verified governed-action bridge**, not an unproven replacement agent.

### Versus Microsoft Sentinel

Microsoft Sentinel is best suited to organizations already committed to Azure and Microsoft Defender. It documents scalable data collection, normalization, analytic rules, threat intelligence, entity graphs, hunting, UEBA, automation rules, and Logic Apps playbooks.[6] [7] [8] Sentinel is far ahead in cloud-scale operations and Microsoft ecosystem integration, but its control plane is Microsoft-managed and its automation behavior is shaped by the Defender/Azure environment.

PhantomNet is a fit where data sovereignty, air-gapped or independent deployment, custom architecture, and human-governed response matter more than native Microsoft platform integration. It is not yet a replacement for Sentinel in a Defender-centric enterprise.

### Versus Elastic Security

Elastic is the closest commercial benchmark for an AI-forward, flexible-deployment security platform. It documents SIEM/XDR, cases, Osquery, endpoint protection, detection engineering, entity analytics, AI-assisted investigation, response workflows, and on-premises or air-gapped operation.[9] [10] [11] Elastic is ahead in search/data platform maturity, endpoint capability, integrations, and operational scale.

PhantomNet’s differentiation lies in a smaller, purpose-built stack where governance and proof of containment are first-class domain objects. To win against Elastic in a narrow segment, PhantomNet must remain visibly simpler to operate and more explicit about response evidence—not merely claim equivalent AI.

### Versus Security Onion

Security Onion is the closest self-hosted SOC comparator for network-centric teams. Its distinctive advantages are Suricata, Zeek, packet capture, file analysis, honeypots, CyberChef, analyst hunting, and tightly integrated case work.[12] [14] Security Onion is stronger when raw network evidence and PCAP-driven investigation are central.

PhantomNet should position alongside Security Onion for organizations that want a broader event/case/governed-response platform, while integrating Security Onion network telemetry. A production-grade honeypot and network sensor implementation would materially improve this comparison.

## Recommended market position

PhantomNet should own this message:

> **For security teams that need a self-hosted SOC they can adapt and trust, PhantomNet unifies canonical telemetry, contextual correlation, case workflows, and human-governed response—with cryptographic evidence for high-impact action.**

Avoid these messages until live evidence exists: “Splunk replacement,” “production EDR,” “autonomous attack stopping,” “full Wazuh parity,” or “enterprise scale proven.” The stronger strategy is to state a disciplined target market:

| Best early customer | Why PhantomNet fits |
|---|---|
| Regulated startup, university, research lab, or regional SaaS team | Wants data/control-plane ownership, adaptable integrations, and auditability without a large commercial SIEM program. |
| Existing Wazuh or Security Onion operator | Wants governed correlation, cases, graph context, and response evidence without discarding existing endpoint/network investment. |
| Security engineering team building bespoke controls | Values microservice boundaries and testable contracts over vendor lock-in. |

## The next three competitive milestones

1. **Ship one production-backed endpoint response integration.** Start with Wazuh or an authorized EDR provider in a lab; demonstrate request, approval, independently observed isolation, release, rollback, and signed evidence.
2. **Prove the deployment.** Run the Docker topology and recovery evidence on a Docker-capable host, then publish a reproducible 30-minute single-node install and a supported scaling reference.
3. **Make the detection pack useful on day one.** Publish versioned, tested content across identity, Linux/Windows endpoint, AWS, cloud audit, network, and Wazuh/Security Onion sources, with MITRE coverage and false-positive guidance.

## References

[1]: https://www.splunk.com/en_us/products/splunk-enterprise-security-features.html "Splunk Enterprise Security features"
[2]: https://www.splunk.com/en_us/products/enterprise-security.html "Splunk Enterprise Security overview"
[3]: https://wazuh.com/platform/overview/ "Wazuh platform overview"
[4]: https://documentation.wazuh.com/current/getting-started/architecture.html "Wazuh architecture"
[5]: https://documentation.wazuh.com/current/user-manual/capabilities/active-response/index.html "Wazuh Active Response"
[6]: https://learn.microsoft.com/en-us/azure/sentinel/overview "Microsoft Sentinel SIEM overview"
[7]: https://learn.microsoft.com/en-us/azure/sentinel/automation/automation "Microsoft Sentinel automation"
[8]: https://learn.microsoft.com/en-us/azure/sentinel/identify-threats-with-entity-behavior-analytics "Microsoft Sentinel UEBA"
[9]: https://www.elastic.co/security/siem "Elastic Security SIEM"
[10]: https://www.elastic.co/docs/solutions/security/investigate "Elastic Security investigations"
[11]: https://www.elastic.co/endpoint-detection-response "Elastic endpoint detection and response"
[12]: https://docs.securityonion.net/en/2.4/introduction.html "Security Onion introduction"
[13]: https://securityonion.net/docs/architecture "Security Onion architecture"
[14]: https://docs.securityonion.net/en/2.4/cases.html "Security Onion Cases"
