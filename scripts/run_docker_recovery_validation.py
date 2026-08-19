"""Internal Docker recovery probe for non-production broker and PostgreSQL validation.

The probe uses only the Compose-internal network. It emits non-secret status evidence, persists
canonical HMAC-signed audit-chain records, and does not invoke response adapters or cloud APIs.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from uuid import uuid4

import psycopg2
from kafka import KafkaConsumer, KafkaProducer
from phantomnet_audit_integrity import append_record, verify_chain


RUN_ID = os.getenv("RECOVERY_RUN_ID", str(uuid4()))
KAFKA_BOOTSTRAP_SERVERS = os.environ["RECOVERY_KAFKA_BOOTSTRAP_SERVERS"]
POSTGRES_DSN = os.environ["RECOVERY_POSTGRES_DSN"]
AUDIT_HMAC_KEY = os.environ["RECOVERY_AUDIT_HMAC_KEY"]
AUDIT_HMAC_KEY_ID = os.environ["RECOVERY_AUDIT_HMAC_KEY_ID"]
TOPIC = os.getenv("RECOVERY_TOPIC", "phantomnet.recovery.validation")


def _result(check: str, **fields: object) -> None:
    print(
        json.dumps(
            {"check": check, "run_id": RUN_ID, "timestamp": datetime.now(timezone.utc).isoformat(), **fields},
            sort_keys=True,
        ),
        flush=True,
    )


def _database_connection():
    return psycopg2.connect(POSTGRES_DSN, connect_timeout=10)


def broker_round_trip() -> None:
    marker = f"broker-recovery:{RUN_ID}"
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value, sort_keys=True).encode("utf-8"),
        request_timeout_ms=10_000,
        api_version_auto_timeout_ms=10_000,
    )
    try:
        metadata = producer.send(TOPIC, {"marker": marker, "kind": "recovery_validation_telemetry"}).get(timeout=10)
        producer.flush(timeout=10)
    finally:
        producer.close(timeout=10)

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=f"recovery-validation-{RUN_ID}",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        consumer_timeout_ms=10_000,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        request_timeout_ms=10_000,
        api_version_auto_timeout_ms=10_000,
    )
    try:
        for message in consumer:
            if message.value.get("marker") == marker:
                consumer.commit()
                _result(
                    "broker_round_trip",
                    status="passed",
                    topic=TOPIC,
                    partition=message.partition,
                    produced_offset=metadata.offset,
                    consumed_offset=message.offset,
                )
                return
    finally:
        consumer.close()
    raise RuntimeError("Broker probe did not consume its own validation marker before timeout.")


def postgres_write_read() -> None:
    marker = f"postgres-recovery:{RUN_ID}"
    connection = _database_connection()
    try:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS recovery_validation_receipts (marker TEXT PRIMARY KEY, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
            )
            cursor.execute("INSERT INTO recovery_validation_receipts (marker) VALUES (%s) ON CONFLICT (marker) DO NOTHING", (marker,))
            cursor.execute("SELECT marker FROM recovery_validation_receipts WHERE marker = %s", (marker,))
            row = cursor.fetchone()
        if row is None or row[0] != marker:
            raise RuntimeError("PostgreSQL probe did not read back its validation receipt.")
        _result("postgres_write_read", status="passed")
    finally:
        connection.close()


def audit_chain_integrity() -> None:
    """Append an HMAC-signed validation record and verify the persisted chain read-only."""
    connection = _database_connection()
    try:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS recovery_validation_audit_records (
                    sequence BIGSERIAL PRIMARY KEY,
                    record_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    actor_id TEXT,
                    action TEXT NOT NULL,
                    payload JSONB NOT NULL,
                    previous_hash TEXT NOT NULL,
                    record_hash TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    signature_key_id TEXT NOT NULL
                )
                """
            )
            cursor.execute("SELECT record_hash FROM recovery_validation_audit_records ORDER BY sequence DESC LIMIT 1")
            previous = cursor.fetchone()
            record = append_record(
                record_id=str(uuid4()),
                actor_id="recovery-validation",
                action="recovery_validation_probe",
                payload={"run_id": RUN_ID},
                previous_hash=previous[0] if previous else "0" * 64,
                signing_key=AUDIT_HMAC_KEY,
                signature_key_id=AUDIT_HMAC_KEY_ID,
            )
            cursor.execute(
                """
                INSERT INTO recovery_validation_audit_records
                    (record_id, timestamp, actor_id, action, payload, previous_hash, record_hash, signature, signature_key_id)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
                """,
                (
                    record.record_id,
                    record.timestamp,
                    record.actor_id,
                    record.action,
                    json.dumps(record.payload, sort_keys=True),
                    record.previous_hash,
                    record.record_hash,
                    record.signature,
                    record.signature_key_id,
                ),
            )
            cursor.execute(
                """
                SELECT record_id, timestamp, actor_id, action, payload, previous_hash, record_hash, signature, signature_key_id
                FROM recovery_validation_audit_records
                ORDER BY sequence
                """
            )
            rows = cursor.fetchall()
        records = [
            {
                "record_id": row[0],
                "timestamp": row[1],
                "actor_id": row[2],
                "action": row[3],
                "payload": row[4],
                "previous_hash": row[5],
                "record_hash": row[6],
                "signature": row[7],
                "signature_key_id": row[8],
            }
            for row in rows
        ]
        if not verify_chain(
            records,
            signing_key=AUDIT_HMAC_KEY,
            require_signature=True,
            expected_key_id=AUDIT_HMAC_KEY_ID,
        ):
            raise RuntimeError("Persisted HMAC-signed audit chain failed verification.")
        _result("audit_chain_integrity", status="passed", record_count=len(records))
    finally:
        connection.close()


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "combined"
    started = time.perf_counter()
    try:
        if mode in {"broker", "combined"}:
            broker_round_trip()
        if mode in {"postgres", "combined"}:
            postgres_write_read()
        if mode in {"audit", "combined"}:
            audit_chain_integrity()
    except Exception as exc:
        _result("recovery_probe", status="failed", error_type=type(exc).__name__)
        raise
    _result("recovery_probe", status="passed", mode=mode, duration_seconds=round(time.perf_counter() - started, 3))


if __name__ == "__main__":
    main()
