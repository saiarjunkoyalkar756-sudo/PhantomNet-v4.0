# Phase 5: Analyst Operations Layer

## Objective

Phase 5 turns tenant-owned SOC records into a bounded analyst workspace. It connects alerts, durable detections, cases, integrated evidence, read-only graph context, saved hunts, and dashboard health into an **explainable evidence-to-decision trace**. The output helps an analyst decide what to review next; it does not decide, approve, or execute a response.

> **Phase 5 is advisory-only.** A decision trace has no containment authority, does not create a containment request, does not transition an alert or case, does not invoke a playbook, and always returns `automatic_enforcement=false` with `recommended_next_step=human_review_required`.

## Core objectives

| Objective | Implementation | Safety boundary |
|---|---|---|
| Evidence-aware hunting | The structured hunt service now supports the `evidence` dataset with allowlisted source metadata filters. | Hunts remain tenant-scoped, read-only, bounded to 200 results, and return an empty `automated_actions` list. |
| Alert decision trace | An alert context joins the tenant-owned alert, linked durable detections, matching integrated evidence, and graph-context records. | Joins are constrained by tenant ID and declared alert detection IDs, event IDs, or correlation IDs. |
| Case decision trace | A case context aggregates the bounded alert traces for its linked alerts and de-duplicates their evidence receipts. | It does not change case state, assignment, playbook state, or alert state. |
| Explainable prioritization | A deterministic score shows severity, occurrence count, linked detections, endpoint/Wazuh evidence, and graph-context factors. | The score is a review cue only; it cannot change severity, suppress evidence, or trigger automation. |
| Dashboard evidence health | Dashboard summary now reports integrated-evidence count and source-kind distribution. | The dashboard reports available context; it does not infer a response recommendation. |
| Traceability | Each trace lists exact alert, case, detection, event, and integrated-evidence IDs. | Records remain owned by the tenant and preserve the Phase 4 read-only provenance contract. |

## Evidence-to-decision flow

```text
Canonical detections ─────┐
Analyst alert workflow ───┼──► Tenant-bound alert context
Integrated evidence ──────┤          │
Read-only graph context ──┘          ▼
                              Explainable priority factors
                                      │
                                      ▼
                         human_review_required only
                                      │
                                      ▼
                     Existing governed case/playbook paths
                (approval and response remain separate)
```

The trace is generated from durable tenant-owned records at read time. It is not a new mutable workflow object. This prevents a dashboard or hunting request from silently changing an investigation lifecycle or creating a high-impact action.

## Explainable priority

Priority is intentionally deterministic and inspectable. The implementation uses the alert’s governed severity, bounded occurrence count, number of linked detections, number of endpoint or Wazuh evidence records, and number of graph-context records. Each returned factor includes its input value and numeric contribution.

| Factor | Purpose | Bound |
|---|---|---|
| Alert severity | Preserves the existing governed severity as the primary review signal. | Informational through critical map to fixed weights. |
| Occurrence count | Shows repeated alert evidence without changing its workflow status. | Capped at 10. |
| Linked detections | Shows how much durable detection evidence backs the alert. | Count-only contribution. |
| Endpoint/Wazuh evidence | Highlights host or read-only Wazuh observations linked to the same tenant trace. | Count-only contribution. |
| Graph context | Indicates that a read-only graph projection exists for the correlation path. | Count-only contribution. |

The score maps to `low`, `medium`, `high`, or `urgent` review levels. It does not modify alert severity, set a case priority, suppress an alert, or create a response proposal.

## Analyst APIs

| Route | Capability | Behavior |
|---|---|---|
| `POST /hunts/execute` | `alerts:read` | Runs a bounded structured hunt, including the new `evidence` dataset. |
| `GET /analyst-context/alerts/{alert_id}` | `alerts:read` | Returns an explainable read-only alert trace, priority factors, linked records, and human-review guidance. |
| `GET /analyst-context/cases/{case_id}` | `alerts:read` | Returns the case, its alert traces, de-duplicated evidence, and exact traceability identifiers. |
| `GET /dashboard/summary` | `alerts:read` | Returns existing SOC health plus integrated evidence count and source-kind distribution. |
| Existing case and playbook routes | Existing capabilities | Continue to own lifecycle transitions. This Phase 5 layer never calls them. |

A missing cross-tenant alert or case is treated as not found. The route does not report whether the identifier exists in another tenant.

## Read-only evidence hunts

The `evidence` hunt dataset exposes only the metadata necessary to decide whether more review is warranted: evidence ID, source kind, source name, source-record ID, timestamp, tags, read-only provenance, and enforcement state. It does not provide an unbounded raw-content search. The supported metadata filters are `source_kind`, `source_name`, and `source_record_id`.

## Operational validation

The Phase 5 focused regression suite verifies the following.

| Validation | Expected result |
|---|---|
| Evidence hunt | Returns only tenant-owned evidence and preserves `read_only=true` and `automatic_enforcement=false`. |
| Dashboard health | Counts integrated evidence and provides deterministic source distribution. |
| Alert context | Joins the correct linked detection, Wazuh/endpoint evidence, and graph context; returns all priority factors. |
| Case context | Aggregates and de-duplicates linked alert traces and integrated evidence. |
| Tenant isolation | Cross-tenant alert and case context requests fail without revealing the other tenant’s record. |
| No-response boundary | Context routes contain no containment or response operation and report no authority. |

Run the focused suite with:

```bash
python3 -m pytest -q -p no:cacheprovider \
  tests/test_analyst_operations_context.py \
  tests/test_threat_hunting_service.py \
  tests/test_case_playbook_workflow.py
```

Run all project quality gates before release:

```bash
python3 -m pytest -q -p no:cacheprovider
cd dashboard_frontend && npm run lint && npm run build
cd ../phantomnet-website && npm run lint && npm run build
```

## Explicit limits

Phase 5 does not replace analyst judgment, SOAR approval, graph-engine production hardening, or dashboard visual design work. It provides a safe, inspectable integration point: **evidence before action, explanation before recommendation, and human approval before high-impact response**.
