"""Docker-host integration proof for the isolated PhantomNet dependency topology.

This test is intentionally gated by ``PHANTOMNET_INTEGRATION=true``. It connects only to the
internal Compose service names and creates disposable probe data under unique identifiers.
"""

from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import asyncpg
import httpx
import pytest
from kafka import KafkaConsumer, KafkaProducer
from redis import Redis


pytestmark = pytest.mark.skipif(
    os.getenv("PHANTOMNET_INTEGRATION", "").lower() != "true",
    reason="Docker topology validation requires PHANTOMNET_INTEGRATION=true.",
)


POSTGRES_DSN = os.environ.get("POSTGRES_DSN", "postgresql://phantomnet:phantomnet-test-only@postgres:5432/phantomnet_test")
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "redpanda:29092")
NEO4J_HTTP_URL = os.environ.get("NEO4J_HTTP_URL", "http://neo4j:7474/db/neo4j/tx/commit")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "phantomnet-test-only")


@pytest.mark.asyncio
async def test_postgres_supports_a_real_write_read_round_trip():
    probe_value = f"phantomnet-topology-{uuid4()}"
    connection = await asyncpg.connect(POSTGRES_DSN, timeout=10)
    try:
        await connection.execute("CREATE TABLE IF NOT EXISTS phantomnet_topology_probes (probe_value TEXT PRIMARY KEY)")
        await connection.execute("INSERT INTO phantomnet_topology_probes (probe_value) VALUES ($1)", probe_value)
        stored = await connection.fetchval("SELECT probe_value FROM phantomnet_topology_probes WHERE probe_value = $1", probe_value)
        assert stored == probe_value
    finally:
        await connection.close()


def test_redis_supports_a_real_write_read_round_trip():
    probe_key = f"phantomnet:topology:{uuid4()}"
    client = Redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=10, socket_timeout=10)
    try:
        assert client.ping() is True
        assert client.set(probe_key, "verified", ex=60) is True
        assert client.get(probe_key) == "verified"
    finally:
        client.delete(probe_key)
        client.close()


def test_redpanda_supports_a_real_produce_consume_round_trip():
    topic = f"phantomnet.topology.{uuid4().hex}"
    payload = f"verified-{uuid4()}".encode("utf-8")
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="latest",
        enable_auto_commit=False,
        consumer_timeout_ms=12_000,
        request_timeout_ms=15_000,
        api_version_auto_timeout_ms=15_000,
    )
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        acks="all",
        request_timeout_ms=15_000,
        api_version_auto_timeout_ms=15_000,
    )
    try:
        producer.send(topic, payload).get(timeout=15)
        producer.flush(timeout=15)
        received = next(iter(consumer), None)
        assert received is not None
        assert received.value == payload
    finally:
        producer.close(timeout=15)
        consumer.close()


@pytest.mark.asyncio
async def test_neo4j_supports_an_authenticated_read_only_query():
    request_body = {"statements": [{"statement": "RETURN 'phantomnet-topology-verified' AS status"}]}
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(NEO4J_HTTP_URL, auth=(NEO4J_USER, NEO4J_PASSWORD), json=request_body)
    response.raise_for_status()
    body = response.json()
    assert body["errors"] == []
    assert body["results"][0]["data"][0]["row"] == ["phantomnet-topology-verified"]
