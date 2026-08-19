# SOC and SIEM comparison research notes

## Splunk Enterprise Security

- Splunk positions Enterprise Security as a unified TDIR platform spanning SIEM, SOAR, UEBA, and AI-assisted workflows.
- Its published feature set includes real-time collection and analysis, Detection Studio, MITRE ATT&CK visualizations, risk-based alerting, threat intelligence, analyst queue, threat topology, case management, response plans, adaptive response actions, visual playbooks, and a large SOAR app/action ecosystem.
- Splunk states that selected AI functionality and certain automated threat-analysis capabilities have Cloud-only or controlled-availability boundaries; the comparison must not treat every named capability as available in every deployment model.

Sources:
1. https://www.splunk.com/en_us/products/splunk-enterprise-security-features.html
2. https://www.splunk.com/en_us/products/enterprise-security.html

## Wazuh

- Wazuh positions its platform as open-source SIEM and XDR, with central indexer/server/dashboard components plus a multi-platform endpoint agent.
- Its published capabilities include endpoint and cloud log analysis, file integrity monitoring, configuration assessment, vulnerability detection, system inventory, threat hunting, compliance reporting, containers security, and active response.
- Wazuh documentation describes Active Response as execution of scripts in response to specific alerts. This is different from PhantomNet's intended approval-gated containment model and should be compared as a control-model distinction, not a categorical superiority claim.

Sources:
3. https://wazuh.com/platform/overview/
4. https://documentation.wazuh.com/current/getting-started/architecture.html
5. https://documentation.wazuh.com/current/user-manual/capabilities/active-response/index.html

## Microsoft Sentinel

- Microsoft Sentinel is a cloud-native SIEM that combines cross-cloud/multiplatform collection, normalization, detections, MITRE coverage, threat intelligence, investigation graph, hunting, automation rules, and Azure Logic Apps playbooks.
- Sentinel UEBA uses machine learning to model users, hosts, IPs, applications, and other entities; it evaluates peer groups, blast radius, and behavioral context.
- Microsoft documents operational constraints during the Defender portal transition, including asynchronous playbook trigger windows and batching behavior. The comparison therefore treats cloud automation maturity and deployment/control-plane dependence as separate dimensions.

Sources:
6. https://learn.microsoft.com/en-us/azure/sentinel/overview
7. https://learn.microsoft.com/en-us/azure/sentinel/automation/automation
8. https://learn.microsoft.com/en-us/azure/sentinel/identify-threats-with-entity-behavior-analytics

## Elastic Security

- Elastic positions its platform as unified SIEM, XDR, native automation, and AI-assisted operations, with on-premises, cloud, and air-gapped deployment options.
- Its documentation describes investigation through timelines, visual event analysis, Session View, Osquery, threat intelligence, cases, and AI chat; endpoint material describes Windows, macOS, and Linux telemetry and prevention capabilities.
- Elastic’s current product material claims human approval and verification in incident-response workflows. In a comparison, this is a mature integrated response position, while PhantomNet should claim its approval/audit strengths only within its tested adapters and control surfaces.

Sources:
9. https://www.elastic.co/security/siem
10. https://www.elastic.co/docs/solutions/security/investigate
11. https://www.elastic.co/endpoint-detection-response

## Security Onion

- Security Onion is a free and open platform with network visibility, host visibility, intrusion-detection honeypots, log management, and case management.
- Its core network strengths are Suricata, Zeek, full packet capture, file analysis, and PCAP-oriented investigation. It can also use Elastic Agent and osquery for host visibility.
- Its documented architecture supports standalone and distributed sensor/manager/search configurations, while the SOC interface supports alerts, dashboards, hunt, PCAP, detections, cases, observables, and analyzers.

Sources:
12. https://docs.securityonion.net/en/2.4/introduction.html
13. https://securityonion.net/docs/architecture
14. https://docs.securityonion.net/en/2.4/cases.html
