# Phase 4: Evidence Integration Layer

## Objective

Phase 4 makes external security context usable without making it authoritative. It introduces one durable, tenant-owned evidence record for asset, endpoint, Wazuh, identity, intelligence, and graph context. Every record must identify its source, source-record identity, timestamps, tags, and explicit read-only provenance before it can be stored or projected into the canonical event pipeline.

> **Phase 4 is an evidence layer, not a response layer.** Integrated evidence can support analyst review and deterministic correlation. It cannot execute containment, change a cloud control, invoke an endpoint command, bypass approval, or set `automatic_enforcement` to `true`.

## Core objectives

| Objective | Implementation | Security boundary |
|---|---|---|
| Unified evidence contract | `IntegratedEvidenceRecord` defines source kind, source identity, observed/collected times, bounded payload, tags, provenance, and read-only state. | Only six declared source kinds are accepted: asset, endpoint, Wazuh, identity, intelligence, and graph. Extra fields are rejected. |
| Tenant ownership | Every record is tenant-scoped from validation through persistence, list, and get operations. | A record can only be retrieved through its owner tenant; cross-tenant lookups return no evidence. |
| Provenance and idempotency | Source name, source-record ID, explicit `provenance.read_only=true`, and a SHA-256 payload/provenance fingerprint are stored. | The database accepts one record per tenant, source identity, and fingerprint, preventing duplicate transport from creating duplicate evidence. |
| Read-only source adapters | Endpoint asset and integrity ingestion writes integrated evidence as a sidecar. Wazuh integrity evidence is labeled `wazuh`; World Intel context is admitted only after its read-only evidence envelope succeeds. | Integrations do not receive response interfaces or credentials through this layer. Unavailable intelligence is not fabricated or stored. |
| Canonical correlation compatibility | Every stored record projects to one canonical `EVIDENCE.<SOURCE>.OBSERVED` event. | The projection is informational, includes `automatic_enforcement=false`, and remains subject to existing tenant-scoped governed correlation rules. |
| Analyst retrieval | Authenticated evidence list/get routes expose only tenant-owned records. | Read access requires `alerts:read`; direct evidence intake requires `config:write` and exact tenant matching. |

## Evidence lifecycle

```text
Read-only adapter or authenticated source
                │
                ▼
     IntegratedEvidenceRecord validation
     tenant + provenance + read-only controls
                │
                ▼
   Durable idempotent evidence persistence
  source identity + SHA-256 payload fingerprint
                │
                ├──► Authenticated analyst retrieval
                │
                ▼
 Canonical EVIDENCE.<SOURCE>.OBSERVED event
                │
                ▼
 Governed correlation and analyst evidence only
        (never automatic response)
```

The evidence store is append-oriented for distinct source-fingerprint observations. A retry with the same tenant, source kind, source name, source-record ID, and fingerprint returns the original evidence record rather than duplicating it. A changed source payload has a new fingerprint and is retained as a distinct observation.

## Source boundaries

| Source | Phase 4 adapter path | Result | Prohibited behavior |
|---|---|---|---|
| Asset | `EndpointTelemetryIngestion.ingest_asset` | Stores an `asset` evidence record alongside existing asset inventory persistence. | Host discovery, scanning, configuration changes, or containment. |
| Endpoint integrity | `EndpointTelemetryIngestion.ingest_integrity` | Stores an `endpoint` evidence record for PhantomNet-agent observations. | Endpoint remediation or automatic response. |
| Wazuh | Existing read-only Wazuh normalizer feeds asset and integrity adapters; Wazuh integrity is stored as `wazuh` evidence. | Preserves upstream adapter identity and reads only normalized telemetry. | Wazuh Active Response, containment requests, or bridge activation. Those remain governed separately. |
| Intelligence | `EvidenceIntegrationService.ingest_intelligence` accepts only successful World Intel envelopes with `read_only=true` provenance. | Stores contextual provider/indicator evidence. | Fetching an unallowlisted tool, treating unavailable context as evidence, or generating response authority. |
| Identity and graph | Authenticated integration intake uses `identity` or `graph` source kinds with the same provenance contract. | Provides tenant-bound context for correlation and analyst investigation. | Cross-tenant graph projection, identity mutation, privilege changes, or execution. |

## Data and integrity controls

The integrated-evidence payload is capped at **64 KiB** after canonical JSON serialization. The record contract rejects false `read_only` flags, missing read-only provenance, and any automatic-enforcement marker. The stored fingerprint covers the payload, provenance, source kind, source name, and source-record identity; it is therefore meaningful only in the declared source context, not as a global content hash.

The migration `e4f5a6b7c8d9_add_integrated_evidence.py` creates `integrated_evidence`. Its unique constraint spans tenant ID, source kind, source name, source-record ID, and payload fingerprint. Source IDs alone are intentionally not globally unique because different integrations may use the same upstream identifier.

## API surface

| Route | Capability | Behavior |
|---|---|---|
| `POST /evidence` | `config:write` | Stores a validated, tenant-matching, read-only integrated record and returns its canonical projection. |
| `GET /evidence` | `alerts:read` | Lists only the caller tenant’s records, optionally filtered by declared source kind. |
| `GET /evidence/{evidence_id}` | `alerts:read` | Retrieves one caller-tenant record or returns not found. |
| `POST /assets` | `config:write` | Existing asset intake now additionally emits an integrated-evidence receipt when Phase 4 is enabled. |
| `POST /integrity` | `config:write` | Existing integrity intake now additionally emits an integrated-evidence receipt when Phase 4 is enabled. |
| `POST /wazuh/alerts` | `config:write` | Existing read-only Wazuh intake returns asset and integrity evidence receipts where applicable. |

The compatibility `EvidenceVault` facade now also requires an explicit `tenant_id`, `source_kind`, and read-only provenance. It no longer permits unaudited process-local evidence storage or cross-tenant retrieval. Its metadata search intentionally does not inspect raw evidence content.

## Operational validation

The focused Phase 4 regression tests prove the following outcomes.

| Validation | Expected outcome |
|---|---|
| Tenant isolation | Cross-tenant list and get operations cannot reveal another tenant’s evidence. |
| Idempotent receipt | A repeated source record with unchanged fingerprint returns the original durable evidence ID. |
| Read-only enforcement | Writable evidence, automatic enforcement, and missing read-only provenance are rejected at contract validation. |
| Endpoint/Wazuh continuity | Existing endpoint events remain unchanged while durable asset and Wazuh evidence receipts are created. |
| Intelligence boundary | Only successful read-only World Intel context is integrated; unavailable context is rejected. |
| Correlation compatibility | An integrated intelligence event can traverse the canonical processor and produce only an advisory governed detection. |
| No response surface | Evidence routes do not expose containment or response operations. |

Run the focused suite with:

```bash
python3 -m pytest -q -p no:cacheprovider tests/test_evidence_integration.py
```

Then run the complete project quality gate before release:

```bash
python3 -m pytest -q -p no:cacheprovider
cd dashboard_frontend && npm run lint && npm run build
cd ../phantomnet-website && npm run lint && npm run build
```

## Explicit limits

Phase 4 does not claim that every legacy graph, identity, or intelligence module is production-ready. It establishes the **required integration boundary** for any such module: tenant scope, immutable source identity, explicit provenance, read-only semantics, bounded payloads, deterministic canonical projection, and zero direct response authority. Live provider connectivity, source credential management, data-retention policies, and graph projection evolution remain separate deployment and governance work.
