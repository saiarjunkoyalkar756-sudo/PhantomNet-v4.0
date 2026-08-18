# SOC and SIEM Comparison Research Notes

## PhantomNet baseline from repository validation

PhantomNet is a self-hosted, distributed architecture with FastAPI backend components, PostgreSQL, Redis, Redpanda, Neo4j, React/Vite dashboard, Next.js portal, endpoint-agent code, and a blockchain audit layer. The source implements prototype SIEM/SOAR concepts including telemetry ingestion, correlation, threat intelligence, playbooks, case management, graph analysis, BAS, and an endpoint agent.

Its maturity is not equivalent to a production SOC platform. The original full test run produced 68 passing, 19 failing, and 11 erroring tests. Later repairs brought collection to 98 tests and created a working local-only SOAR firewall action. The adapter verified and rolled back a sandbox iptables rule only for RFC 5737 documentation addresses. It does not provide production firewall, EDR host isolation, or process termination integration. The latter controls truthfully report failure without a configured provider.

## Microsoft Sentinel

Official source: https://learn.microsoft.com/en-us/azure/sentinel/

Microsoft Sentinel documents a cloud-native SOC platform covering telemetry connectors and collection, normalization/parsing, threat intelligence, MITRE ATT&CK mapping, UEBA, anomaly detection, built-in/custom analytics rules, incident investigation/case management, KQL hunting, automation rules, playbooks, and automated response. It is a mature cloud service benchmark for lifecycle breadth and managed operations.

## Splunk Enterprise Security

Official source: https://help.splunk.com/en/splunk-enterprise-security-8/user-guide/8.1/introduction/get-started-with-splunk-enterprise-security

Splunk Enterprise Security documents triage, investigations, response plans, automated investigation response with actions/playbooks, risk-based alerting, and threat-intelligence investigation. It is an enterprise SIEM benchmark for analytics, investigation workflow, ecosystem maturity, and risk-based detection.

## CrowdStrike Falcon Next-Gen SIEM

Official source: https://www.crowdstrike.com/en-us/platform/next-gen-siem/

The official CrowdStrike page positions Falcon Next-Gen SIEM as an AI-native, XDR-centric SOC platform. It describes cross-domain data, real-time/federated search, unified detection and response, centralized case management, third-party indicator management, and integrated Falcon Fusion/Charlotte Agentic SOAR workflows. Vendor performance and cost claims are vendor-reported and are not used as independent benchmarks in the comparison.

## Wazuh

Official source: https://documentation.wazuh.com/current/user-manual/capabilities/active-response/index.html

Wazuh documents an open-source SIEM/XDR design that executes active-response scripts on monitored endpoints when an alert trigger matches a configured rule ID, level, or group. It distinguishes stateless actions from stateful actions that revert after a configured period, and documents configuration for the server and monitored endpoint, default and custom scripts, whitelist controls, and a specific SSH brute-force blocking use case. It therefore provides a useful open-source benchmark for endpoint-mediated, configurable, reversible response.

## Google Security Operations

Official source: https://docs.cloud.google.com/chronicle/docs/siem

Google Security Operations documents a cloud service for privately retaining, analyzing, and searching large security and network telemetry volumes. Its SIEM documentation states that it normalizes, indexes, correlates, and analyzes data for context on risky activity, and exposes documented search, detection-engine, ingestion, and unified-data-model APIs. It is a useful benchmark for mature normalized-data lifecycle and API-oriented operations.
