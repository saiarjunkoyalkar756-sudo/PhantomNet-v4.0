# Performance Stress and Chaos Validation

## Scope and safety boundary

This validation is intentionally **controlled and non-destructive**. It uses a single in-memory SQLite database, synthetic BAS-marked telemetry, simulated software failures, and no network destination. It does not start Docker, contact Kafka or Redpanda, invoke AWS, access endpoints, alter firewall state, or execute a response adapter.

> The measured figures are a repeatable **local regression signal**, not a production-capacity claim. Production latency, throughput, availability, recovery, and data-loss behavior require a Docker-capable environment with PostgreSQL, Redpanda or Kafka, Redis, Neo4j, TLS, and realistic disk and network conditions.

## Stress profile

The reproducible benchmark runs 500 unique canonical BAS authentication events through normalization, baseline detection, durable detection storage, and analyst alert creation. It then replays every tenth message, for 50 duplicate deliveries. It fails if a duplicate produces a new detection, creates a new alert, increments an alert occurrence count, or invokes a response adapter.

| Measured item | Result | Interpretation |
|---|---:|---|
| Unique canonical events | 500 | Controlled isolated workload |
| Duplicate deliveries | 50 | At-least-once delivery resilience check |
| Unique detections | 500 | One durable detection per unique event |
| Unique analyst alerts | 500 | One durable alert per unique event |
| p50 latency | 2.126 ms | Local in-memory per-event processing only |
| p95 latency | 2.257 ms | Local tail-latency regression signal |
| p99 latency | 2.461 ms | Local tail-latency regression signal |
| Throughput | 467.771 events/s | Sequential SQLite fixture throughput only |
| External response actions | 0 | Explicitly verified |

## Controlled fault-injection matrix

| Fault injected | Expected invariant | Verified recovery behavior |
|---|---|---|
| First detection persistence attempt fails | A durable dead-letter receipt is created and no silent loss occurs | Explicit replay succeeds once; one detection and one alert exist afterward |
| First alert-workflow attempt fails after detection persistence | Replay repairs alert workflow without increasing alert cardinality | The detection is treated as a duplicate; one alert remains with occurrence count one |
| First regional telemetry transport attempt fails | Failure receipt retains event hash and retry evidence | Identical event retry reuses receipt, increments attempts, and delivers once |
| Signed audit payload is modified in memory | No repair or suppression occurs | Hash-chain/HMAC verification returns invalid evidence |

## Reproduction

Run the stress benchmark from the project root. It writes a non-sensitive JSON result suitable for comparison across local regression runs.

```bash
PYTHONPATH="$(pwd):$(pwd)/phantomnet_agent" \
  python3 scripts/run_resilience_stress.py \
  --events 500 \
  --output artifacts/resilience_stress_benchmark.json
```

Run the isolated stress and chaos assertions:

```bash
python3 -m pytest tests/test_resilience_stress_chaos.py -q -p no:cacheprovider
```

## Required next validation

A Docker-capable non-production host should validate the same invariants under broker restart, consumer restart, PostgreSQL connection failure, Redis outage, broker partition, regional transport timeout, message reordering, realistic retry backoff, dead-letter retention, and regional failover. Those experiments must remain tenant-scoped, use non-production credentials, disable containment adapters unless specifically approved, and preserve signed-audit verification before and after each fault scenario.
