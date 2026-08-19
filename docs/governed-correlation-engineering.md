# Governed Correlation Engineering

## Purpose

The governed correlation engine adds tenant-owned, deterministic detection rules to PhantomNet’s canonical ingestion path. It replaces unsafe free-form matching with structured predicates over canonical event fields and retains bounded match evidence before a threshold becomes a detection.

> **Detection and correlation are advisory.** A governed rule can create durable detection and alert evidence, but it cannot contain an endpoint, modify a cloud firewall, execute a playbook, or invoke any response adapter.

## Rule boundary

A governed rule has a tenant UUID, numeric dotted version, bounded event types, structured predicates, one tactic for every MITRE technique, an optional correlation key, a threshold, a time window, and a reviewed alert-suppression window. The contract rejects undeclared fields, raw query text, response-action properties, unsafe field paths, nested arbitrary values, invalid MITRE IDs, and incomplete technique-to-tactic mappings.

| Rule element | Allowed form | Safety property |
|---|---|---|
| Field path | Bounded canonical dot path such as `payload.hostname` | No raw database, graph, or query expression |
| Operators | `equals`, `contains`, `gte`, `lte`, `in` | Deterministic and testable evaluation |
| Values | Scalar or bounded scalar list | No arbitrary executable or nested object payload |
| Threshold | 1–100 matches | Bounded correlation state |
| Window | 1 second–24 hours | Bounded temporal lookback |
| MITRE evidence | Equal-length valid technique and tactic arrays | Complete analyst-readable technique-to-tactic coverage |
| Alert suppression window | 0 seconds–24 hours | Rule-reviewed control for repeated analyst alerts; never changes detection evidence or execution authority |

## Rule version governance

The active rule table is only the current projection. Each accepted rule version is also stored as an **immutable tenant-scoped snapshot** containing the complete bounded definition and a SHA-256 definition fingerprint. A changed definition must supply a strictly higher dotted numeric version; versions cannot be reduced, and an already recorded version cannot be redefined. This makes a historical detection’s `rule_id`, `rule_version`, and definition fingerprint reproducible for analyst review.

A repeated submission of an unchanged current definition is idempotent. Existing pre-revision rules receive their first immutable snapshot when they are next submitted without altering their active definition.

## Correlation evidence

Every matching event receives an idempotent durable match receipt keyed by tenant, rule, and event. The engine computes a hash-based correlation key from the declared key fields; when none are declared, it falls back to the canonical event correlation ID or source/event-type grouping. It counts matching receipts within the governed window and emits a detection only when the configured threshold is met.

Duplicate broker delivery reads the existing receipt. It neither creates a second match nor changes the threshold count. When the same detection reaches the alert workflow again, the workflow recognizes it as an already-linked transport duplicate and leaves the analyst alert occurrence count unchanged.

The rule’s bounded alert-suppression window is carried as governed detection evidence. The analyst workflow uses it only to group repeated alerts with the same stable suppression key. A malformed value falls back to the conservative workflow default, and neither a rule nor suppression metadata can suppress durable match or detection evidence.

## Analyst APIs

| Route | Required capability | Behavior |
|---|---|---|
| `GET /governed-rules` | `alerts:read` | Lists only rules owned by the authenticated tenant |
| `POST /governed-rules` | `rules:write` | Creates or updates a structured tenant-owned rule after tenant-scope validation |
| `GET /governed-rules/quality` | `alerts:read` | Returns tenant-owned match counts, detection counts, and last-match time without automatic tuning |
| `GET /governed-rules/mitre-coverage` | `alerts:read` | Returns deterministic tenant-owned technique and tactic counts with no tuning or response capability |
| `GET /governed-rules/{rule_id}/revisions` | `alerts:read` | Returns immutable definition snapshots and fingerprints for one tenant-owned rule |
| `POST /governed-rules/{rule_id}/fixtures/evaluate` | `rules:write` | Evaluates a bounded tenant-owned fixture in timestamp/event-ID order without persisting events or invoking response |

## Deterministic fixture evaluation

A fixture is a bounded offline set of unique tenant-owned canonical events plus the expected event IDs that should cross the configured threshold. Fixture events are ordered by timestamp and then event ID, grouped with the same declared correlation key and window as live evaluation, and evaluated without database writes. The evaluation returns the ordered event IDs, matching event IDs, detection event IDs, expected IDs, and a boolean expectation result. It has no broker, endpoint, cloud, containment, or response-adapter dependency.

## Quality telemetry

Rule quality output contains only non-sensitive operational evidence: rule identity, enabled state, severity, matching-event count, threshold-detection count, and normalized UTC last-match time. It does not claim precision, recall, or false-positive rates without analyst-labeled ground truth.

## Deployment and validation

The migration `b4e8c1d6f2a9_add_governed_correlation.py` creates tenant-scoped governed-rule and match-evidence tables. The follow-on migration `f1a2b3c4d5e6_add_governed_correlation_revisions.py` adds the bounded suppression field and immutable revision snapshots. Isolated tests cover contract rejection, tenant isolation, persistence before threshold, MITRE detection after threshold, idempotent upsert, monotonic immutable versions, deterministic fixture evaluation, rule-provided alert suppression, canonical broker integration, replay-safe alert handling, and API route wiring. Full broker deployment validation remains a Docker-capable-host task because this sandbox has no Redpanda deployment.
