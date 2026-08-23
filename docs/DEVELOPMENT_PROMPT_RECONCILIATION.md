# Development Prompt Reconciliation

## Purpose

`PHANTOMNET_DEV_PROMPT.txt` is retained at the repository root as the user-provided development governance reference. This document reconciles its post-remediation, pre-external-lab snapshot with the source-controlled state on `main`. Where the prompt’s historical service inventory conflicts with current code, migrations, tests, or the credibility ledger, the current evidence in the repository is authoritative.

> **Governing rule:** deterministic evidence, tenant isolation, HMAC-audited human approval, adapter verification, rollback, and credibility classification take precedence over feature velocity or roadmap wording.

## Reconciliation

| Prompt area | Current evidence | Reconciled state |
|---|---|---|
| Evidence taxonomy and fail-closed response | `docs/CREDIBILITY_AND_EXTERNAL_PROOF_BASELINE.md`, governed containment contracts, audit and response regressions | **Adopted.** These are already repository rules and remain mandatory for every increment. |
| Prompt architecture snapshot at `f8a58ac` | Main now includes `c184c53` and `9fceeae` after the snapshot | **Historical.** It does not include evidence-grounded autonomous decisions or the governed defensive-data evaluation pipeline. |
| Deterministic detection before probabilistic AI | Versioned governed correlation, BAS fixtures, MITRE evidence, suppression, and decision traces | **Implemented foundation.** Detection coverage and live false-positive evidence remain continuing work. |
| Response governance | Approval-bound containment, HMAC audit gate, verification, rollback, endpoint/AWS/Wazuh boundaries | **Implemented with controlled evidence.** Real Wazuh and AWS execution remain non-production lab gates. |
| AI layer | Deterministic evidence-grounded decision service; sanitized corpus registry; immutable model evaluation; disabled-by-default advisory provider | **Partially implemented, advisory-only.** No model is trained on customer data, no external model is enabled by default, and no AI output has direct response authority. |
| Service consolidation target | Root development Compose still lists a broad legacy service topology; the Phase 7 self-hosted reference intentionally exposes a reduced control-plane topology | **Open architecture work.** Consolidation requires dependency mapping and Docker-host proof; it must not be performed as an untested rename-only exercise. |
| Universal health, readiness, and metrics | Shared factory provides standardized endpoints, but legacy service coverage is uneven | **Highest-priority remaining foundation gap.** Each service must be inventoried and made observable before any production claim. |
| External-lab gates | Controlled protocols and harnesses exist | **Class C pending.** The repository must not claim Docker-host, Wazuh, AWS, agent-device, scale, or production proof until lab evidence is retained. |

## Next implementation increment

The prompt’s Phase 1 focus remains appropriate after reconciliation. The next source-controlled increment is an **observable service contract inventory**: enumerate the self-hosted control-plane services, assert required `/health`, `/ready`, and `/metrics` contracts where applicable, classify dependencies, and make missing coverage visible in regression tests. This is safer and more actionable than prematurely consolidating services or adding probabilistic capabilities.

| Constraint | Required behavior |
|---|---|
| Security | New health/readiness output must be secret-safe and must not downgrade readiness checks. |
| Evidence | New service claims remain Class A only after deterministic regression coverage; Docker-host validation remains Class C. |
| Deployment | The root broad Compose file remains a development topology; the Phase 7 reference remains the self-hosted baseline until a consolidated topology is built and tested. |
| AI | Advisory model work may only consume accepted, tenant-owned evaluation evidence and must remain observation/investigation-only. |
| Response | No health, evaluation, or AI route may create a path around approval, HMAC audit, verification, or rollback. |

## Adoption rule

Future implementation sessions should load the root prompt, then consult this reconciliation, the credibility ledger, controlled external-lab validation protocol, and the current Git revision. The prompt is a governance and planning input, not proof that a roadmap item is complete.
