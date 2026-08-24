# Governed Attack-Path Analysis

## Purpose

PhantomNet’s governed attack-path analysis projects **tenant-owned, canonical SOC evidence** into a read-only graph and returns bounded evidence paths for analysts. It provides context for investigations; it does not enrich data with untrusted graph input, execute playbooks, issue endpoint commands, alter firewall rules, or trigger containment.

> **Security boundary:** graph analysis is read-only. A path result is evidence context for an analyst, never an authorization to take a response action.

## Evidence model

The projection accepts only the platform’s canonical contracts. Every graph node and relationship retains identifiers of the durable evidence that justified it.

| Evidence record | Graph node or relationship |
|---|---|
| `HostAssetRecord` | `asset:<asset_id>` |
| `IntegrityObservation` | `integrity:<observation_id>` and `INTEGRITY_OBSERVED_ON_ASSET` |
| `DetectionRecord` | `detection:<detection_id>`, evidence-to-asset or evidence-to-integrity relationships, and MITRE technique mapping |
| `AlertRecord` | `alert:<alert_id>` and `ALERT_DERIVED_FROM_DETECTION` |
| `CaseRecord` | `case:<case_id>` and `CASE_INVESTIGATES_ALERT` |

The service does not infer asset ownership from hostnames, descriptions, or AI output. A detection may be linked to an asset only through an explicit `evidence.asset_id`, or to an integrity observation through an exact `event_id` and `source_event_id` match.

## Tenant and query controls

Each graph snapshot is isolated by canonical tenant UUID. Projection fails if any input record belongs to another tenant. Path queries derive the tenant from the authenticated user and never accept a tenant identifier from the request body.

The only supported query input is a validated pair of canonical graph node identifiers with strict bounds: a maximum of six hops, 25 paths, and 5,000 traversal expansions. Raw Cypher, labels, relationship expressions, and arbitrary query fields are rejected.

| API route | Capability | Purpose |
|---|---|---|
| `POST /api/governed-attack-paths/refresh` | `config:write` | Projects a bounded snapshot of the authenticated tenant’s assets, integrity evidence, detections, alerts, and cases. |
| `POST /api/governed-attack-paths/analyze` | `alerts:read` | Returns bounded evidence-backed paths for the authenticated tenant. |

The prior unscoped legacy graph route remains only as an explicit compatibility boundary and returns HTTP `410 Gone`. Its direct event consumer, unscoped graph builder, and direct path analyzer are retired and have no enablement setting.

## Self-hosted backend configuration

The default `memory` backend supports isolated development and tests but is ephemeral. A self-hosted Neo4j deployment is enabled only through explicit environment configuration:

```dotenv
PHANTOMNET_GRAPH_BACKEND=neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<environment-managed-secret>
```

The Neo4j backend uses static, parameterized Cypher. Tenant identifiers, node identifiers, hop counts, and result limits are bound parameters; the API never passes caller-controlled Cypher or relationship syntax to Neo4j.

## Analyst workflow

An administrator refreshes the current tenant graph from canonical evidence. An analyst then enters a source and target identifier, such as `case:<case-id>` and `asset:<asset-id>`, in the **Evidence-backed attack paths** panel of the Threat Hunting workspace. The returned path displays hop count, calculated evidence risk, and source evidence references.

A graph result must be reviewed alongside the linked alert, case, integrity observation, and audit history. If containment is needed, it still follows the separate human-request, approval, signed-audit, execution, verification, and rollback lifecycle.

## Validation status

The isolated test coverage verifies evidence-bound paths, tenant isolation, cross-tenant projection refusal, bounded query validation, rejection of undeclared raw-query fields, governed router wiring, permanent legacy-route retirement, and the absence of execution or rollback methods from the graph service. Neo4j connectivity and multi-container behavior remain pending validation on a Docker-capable host with a real self-hosted Neo4j instance.
