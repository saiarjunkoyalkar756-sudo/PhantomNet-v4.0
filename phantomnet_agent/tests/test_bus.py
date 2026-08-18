import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from phantomnet_agent.bus.http_bus import HttpTransport
from phantomnet_agent.bus.kafka_bus import KafkaTransport
from phantomnet_agent.bus.redis_bus import RedisTransport
from phantomnet_agent.schemas.actions import AgentAction


@pytest.mark.asyncio
async def test_http_transport_send_event_success(monkeypatch):
    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.aclose = AsyncMock()
    monkeypatch.setattr("phantomnet_agent.bus.http_bus.httpx.AsyncClient", MagicMock(return_value=mock_client))

    transport = HttpTransport("http://test-endpoint.com")
    await transport.connect()
    event_payload = {
        "agent_id": "test-http",
        "timestamp": "2026-01-01T00:00:00Z",
        "event_type": "test_event",
        "payload": {"message": "hello"},
    }
    await transport.send_event(event_payload)

    mock_client.post.assert_awaited_once()
    assert mock_client.post.call_args.args[0] == "/api/v1/events/ingest"
    assert mock_client.post.call_args.kwargs["json"] == event_payload
    await transport.disconnect()
    mock_client.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_http_transport_send_event_failure(monkeypatch):
    mock_client = MagicMock(spec=httpx.AsyncClient)
    mock_response = MagicMock(status_code=400, text="Bad Request")
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Bad Request", request=MagicMock(), response=mock_response
    )
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.aclose = AsyncMock()
    monkeypatch.setattr("phantomnet_agent.bus.http_bus.httpx.AsyncClient", MagicMock(return_value=mock_client))

    transport = HttpTransport("http://test-endpoint.com")
    await transport.connect()
    await transport.send_event(
        {
            "agent_id": "test-http-fail",
            "timestamp": "2026-01-01T00:00:00Z",
            "event_type": "test_event",
            "payload": {"message": "hello"},
        }
    )

    mock_client.post.assert_awaited_once()
    await transport.disconnect()


@pytest.mark.asyncio
async def test_http_transport_receive_commands():
    transport = HttpTransport("http://test-endpoint.com")
    received_commands = [command async for command in transport.receive_commands("any_topic")]
    assert received_commands == []


def _redis_client_stub():
    client = MagicMock()
    client.ping = AsyncMock()
    client.xadd = AsyncMock()
    client.close = AsyncMock()
    pubsub = MagicMock()
    pubsub.subscribe = AsyncMock()
    pubsub.unsubscribe = AsyncMock()
    pubsub.close = AsyncMock()
    client.pubsub.return_value = pubsub
    return client, pubsub


@pytest.mark.asyncio
async def test_redis_transport_send_event(monkeypatch):
    mock_redis, _ = _redis_client_stub()
    monkeypatch.setattr("phantomnet_agent.bus.redis_bus.redis.from_url", MagicMock(return_value=mock_redis))
    transport = RedisTransport("redis://localhost:6379/0", "events", "commands")
    await transport.connect()

    event_payload = {
        "agent_id": "test-redis",
        "timestamp": "2026-01-01T00:00:00Z",
        "event_type": "test_event",
        "payload": {"data": "test"},
    }
    await transport.send_event(event_payload)

    mock_redis.xadd.assert_awaited_once()
    assert mock_redis.xadd.call_args.args[0] == "events"
    assert json.loads(mock_redis.xadd.call_args.args[1]["data"]) == event_payload
    await transport.disconnect()


@pytest.mark.asyncio
async def test_redis_transport_receive_commands(monkeypatch):
    mock_redis, _ = _redis_client_stub()
    monkeypatch.setattr("phantomnet_agent.bus.redis_bus.redis.from_url", MagicMock(return_value=mock_redis))
    transport = RedisTransport("redis://localhost:6379/0", "events", "commands")
    await transport.connect()
    transport._listener_task = asyncio.create_task(asyncio.sleep(3600))
    await transport._command_queue.put(
        AgentAction(
            agent_id="test-redis",
            action_id="1",
            action_type="process_kill",
            timestamp=123.45,
            payload={"pid": 123},
        )
    )

    received_commands = []
    async for command in transport.receive_commands("commands"):
        received_commands.append(command)
        break

    assert len(received_commands) == 1
    assert received_commands[0].action_type == "process_kill"
    assert received_commands[0].payload["pid"] == 123
    await transport.disconnect()


def _kafka_client_stubs():
    producer = MagicMock()
    producer.start = AsyncMock()
    producer.stop = AsyncMock()
    producer.send_and_wait = AsyncMock()
    consumer = MagicMock()
    consumer.start = AsyncMock()
    consumer.stop = AsyncMock()
    return producer, consumer


@pytest.mark.asyncio
async def test_kafka_transport_send_event(monkeypatch):
    mock_producer, mock_consumer = _kafka_client_stubs()
    monkeypatch.setattr("phantomnet_agent.bus.kafka_bus.AIOKafkaProducer", MagicMock(return_value=mock_producer))
    monkeypatch.setattr("phantomnet_agent.bus.kafka_bus.AIOKafkaConsumer", MagicMock(return_value=mock_consumer))
    transport = KafkaTransport("localhost:9092", "events", "commands", "test_group")
    await transport.connect()

    event_payload = {
        "agent_id": "test-kafka",
        "timestamp": "2026-01-01T00:00:00Z",
        "event_type": "test_event",
        "payload": {"key": "value"},
    }
    await transport.send_event(event_payload)

    mock_producer.send_and_wait.assert_awaited_once()
    assert mock_producer.send_and_wait.call_args.args[0] == "events"
    assert json.loads(mock_producer.send_and_wait.call_args.args[1].decode("utf-8")) == event_payload
    await transport.disconnect()
    mock_producer.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_kafka_transport_receive_commands(monkeypatch):
    mock_producer, mock_consumer = _kafka_client_stubs()
    monkeypatch.setattr("phantomnet_agent.bus.kafka_bus.AIOKafkaProducer", MagicMock(return_value=mock_producer))
    monkeypatch.setattr("phantomnet_agent.bus.kafka_bus.AIOKafkaConsumer", MagicMock(return_value=mock_consumer))
    transport = KafkaTransport("localhost:9092", "events", "commands", "test_group")
    await transport.connect()
    transport._listener_task = asyncio.create_task(asyncio.sleep(3600))
    await transport._command_queue.put(
        AgentAction(
            agent_id="test-kafka",
            action_id="1",
            action_type="process_kill",
            timestamp=123.45,
            payload={"pid": 123},
        )
    )

    received_commands = []
    async for command in transport.receive_commands("commands"):
        received_commands.append(command)
        break

    assert len(received_commands) == 1
    assert received_commands[0].action_type == "process_kill"
    assert received_commands[0].payload["pid"] == 123
    await transport.disconnect()
    mock_consumer.stop.assert_awaited_once()
