# Canonical Ingestion Reliability

## Purpose

The canonical ingestion reliability layer preserves forensic evidence for failed broker deliveries while keeping successful delivery, detection persistence, and analyst alert workflows idempotent. It separates three states that must not be conflated: a delivery that succeeds, a delivery that has been durably dead-lettered, and a delivery that fails before durable failure evidence exists.

> **Safety boundary:** a dead-letter replay reprocesses canonical telemetry only. It cannot invoke containment, a response adapter, a playbook execution, or any automatic enforcement action.

## Broker commit model

The correlation consumer disables automatic offset commits. It commits a broker offset only after one of two terminal outcomes:

| Outcome | Consumer action | Durable evidence |
|---|---|---|
| Canonical processing succeeds | Commit offset | Detection and idempotent alert evidence |
| Processing fails but a dead-letter receipt is stored | Commit offset | Immutable failure receipt with delivery coordinates and failure metadata |
| Processing or dead-letter persistence fails | Do **not** commit offset | Broker retains the delivery for retry after the underlying persistence issue is fixed |

Invalid JSON is retained as a hash-only failure payload rather than storing raw unparseable broker content. This allows operators to correlate a broker delivery without unnecessarily persisting raw malformed content. Valid JSON telemetry retains its canonical payload as evidence, subject to the normal tenant and database access controls.

## Durable failure receipt

Each dead-letter receipt is unique on its broker coordinates: topic, partition, and offset. Repeated processing attempts update the same open receipt’s attempt count and last-failure timestamp. A coordinate reappearing with a different canonical message hash is rejected because it indicates an unsafe broker-delivery inconsistency.

A tenant is recorded only after its identifier parses as a canonical UUID. Malformed or absent tenant values are stored as unscoped forensic receipts and cannot appear in any tenant’s analyst listing. Tenant-scoped lists and replays use the authenticated tenant identity rather than a caller-supplied tenant identifier.

## Replay model

An analyst with the existing governed workflow write capability can explicitly replay one open tenant-owned receipt through `POST /ingestion/dead-letters/{dead_letter_id}/replay`. Successful replay changes the receipt to `replayed` and records the actor and timestamp. Retrying an already replayed receipt is idempotent and never reprocesses the event a second time.

If a replay fails, the receipt remains open, increments its attempt count, and retains the current failure code and type. The replay path cannot change a receipt’s tenant ownership or payload hash.

## Alert repair and duplicate delivery

Canonical broker delivery is at-least-once. The alert workflow now recognizes a detection already linked to its active alert as a transport duplicate: it returns an idempotent suppressed workflow result without adding a second detection ID or increasing the alert occurrence count. This permits a duplicate broker delivery to repair a previously interrupted post-detection alert workflow without manufacturing a new analyst incident.

## Operator API

| Route | Required capability | Scope |
|---|---|---|
| `GET /ingestion/dead-letters` | `alerts:read` | Lists only dead-letter receipts owned by the authenticated tenant |
| `POST /ingestion/dead-letters/{dead_letter_id}/replay` | `cases:write` | Explicitly replays one open tenant-owned receipt through canonical detection and alert processing |

## Validation

The isolated test suite covers coordinate idempotency, tenant separation, malformed tenant handling, hash conflict refusal, explicit replay, idempotent replay, replay failure attempt accounting, broker-wrapper durable receipt signaling, and alert duplicate-delivery behavior. Production broker and database validation remains a Docker-capable-host gate because this sandbox has no Docker or Redpanda deployment.
