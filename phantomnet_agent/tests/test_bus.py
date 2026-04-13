import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import json

# Import the Transport implementations
from phantomnet_agent.bus.http_bus import HttpTransport
from phantomnet_agent.bus.redis_bus import RedisTransport
from phantomnet_agent.bus.kafka_bus import KafkaTransport
from phantomnet_agent.schemas.events import AgentEvent
from phantomnet_agent.schemas.actions import AgentAction

# --- HttpTransport Tests ---
@pytest.mark.asyncio
async def test_http_transport_send_event_success():
    mock_async_client = MagicMock(spec=httpx.AsyncClient)
    mock_async_client.post = AsyncMock(return_value=MagicMock(raise_for_status=MagicMock()))
    mock_async_client.aclose = AsyncMock()

    with patch('bus.http_bus.httpx.AsyncClient', return_value=mock_async_client):
        transport = HttpTransport("http://test-endpoint.com/events")
        
        event_payload = {
            "agent_id": "test-http",
            "timestamp": 123.45,
            "event_type": "test_event",
            "payload": {"message": "hello"}
        }
        await transport.send_event("any_topic", event_payload)
        
        mock_async_client.post.assert_called_once()
        assert mock_async_client.post.call_args[0][0] == "http://test-endpoint.com/events"
        assert json.loads(mock_async_client.post.call_args[1]['json']) == event_payload
        
        await transport.close()
        mock_async_client.aclose.assert_called_once()

@pytest.mark.asyncio
async def test_http_transport_send_event_failure():
    mock_async_client = MagicMock(spec=httpx.AsyncClient)
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("Bad Request", request=MagicMock(), response=mock_response)
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_async_client.post = AsyncMock(side_effect=httpx.HTTPStatusError("Bad Request", request=MagicMock(), response=mock_response))
    mock_async_client.aclose = AsyncMock()

    with patch('bus.http_bus.httpx.AsyncClient', return_value=mock_async_client):
        transport = HttpTransport("http://test-endpoint.com/events")
        
        event_payload = {
            "agent_id": "test-http-fail",
            "timestamp": 123.45,
            "event_type": "test_event",
            "payload": {"message": "hello"}
        }
        await transport.send_event("any_topic", event_payload)
        
        mock_async_client.post.assert_called_once()
        # Check that error was logged (requires capturing logs, which is more complex)
        
        await transport.close()
        mock_async_client.aclose.assert_called_once()

@pytest.mark.asyncio
async def test_http_transport_receive_commands():
    transport = HttpTransport("http://test-endpoint.com/events")
    # HttpTransport's receive_commands should yield nothing
    async for command in await transport.receive_commands("any_topic"):
        assert False, "HttpTransport should not yield any commands"


# --- RedisTransport Tests ---
@pytest.mark.asyncio
async def test_redis_transport_send_event(monkeypatch):
    mock_redis = AsyncMock()
    mock_redis.xadd = AsyncMock()
    
    monkeypatch.setattr("bus.redis_bus.redis.from_url", MagicMock(return_value=mock_redis))

    transport = RedisTransport(
        url="redis://localhost:6379/0",
        events_channel="events",
        commands_channel="commands"
    )
    await transport.connect()

    event_payload = {
        "agent_id": "test-redis",
        "timestamp": 123.45,
        "event_type": "test_event",
        "payload": {"data": "test"}
    }
    await transport.send_event("events", event_payload)

    mock_redis.xadd.assert_called_once()
    assert mock_redis.xadd.call_args[0][0] == "events"
    sent_data = json.loads(mock_redis.xadd.call_args[0][1]['data'])
    assert sent_data == event_payload

    await transport.close()

@pytest.mark.asyncio
async def test_redis_transport_receive_commands(monkeypatch):
    mock_redis = AsyncMock()
    mock_pubsub = AsyncMock()
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.get_message = AsyncMock()
    mock_pubsub.unsubscribe = AsyncMock()
    mock_pubsub.close = AsyncMock()
    mock_redis.pubsub.return_value = mock_pubsub
    
    monkeypatch.setattr("bus.redis_bus.redis.from_url", MagicMock(return_value=mock_redis))

    transport = RedisTransport(
        url="redis://localhost:6379/0",
        events_channel="events",
        commands_channel="commands"
    )
    await transport.connect()

    # Simulate a command message
    command_data = {
        "agent_id": "test-redis",
        "action_id": "1",
        "action_type": "process_kill",
        "timestamp": 123.45,
        "payload": {"pid": 123}
    }
    mock_pubsub.get_message.side_effect = [
        {"type": "subscribe", "channel": "commands"}, # Ignore this
        {"type": "message", "channel": "commands", "data": json.dumps(command_data)},
        {"type": "message", "channel": "commands", "data": "invalid json"}, # Simulate error
        None, # No more messages
    ]

    received_commands = []
    # Using a timeout to ensure the test doesn't hang
    with pytest.raises(asyncio.TimeoutError):
        async for command in transport.receive_commands("commands"):
            received_commands.append(command)
            if len(received_commands) == 1: # Only expect one valid command
                break # Exit the loop after processing the first valid command
            await asyncio.sleep(0.01) # Yield control

    assert len(received_commands) == 1
    assert received_commands[0].action_type == "process_kill"
    assert received_commands[0].payload["pid"] == 123

    await transport.close()
    mock_pubsub.unsubscribe.assert_called_once_with("commands")
    mock_pubsub.close.assert_called_once()


# --- KafkaTransport Tests ---
@pytest.mark.asyncio
async def test_kafka_transport_send_event(monkeypatch):
    mock_producer = AsyncMock()
    mock_producer.start = AsyncMock()
    mock_producer.send_and_wait = AsyncMock()
    mock_producer.stop = AsyncMock()

    monkeypatch.setattr("bus.kafka_bus.AIOKafkaProducer", MagicMock(return_value=mock_producer))
    monkeypatch.setattr("bus.kafka_bus.AIOKafkaConsumer", AsyncMock()) # Don't need consumer for send test

    transport = KafkaTransport(
        bootstrap_servers="localhost:9092",
        events_topic="events",
        commands_topic="commands",
        consumer_group_id="test_group"
    )
    await transport.connect()

    event_payload = {
        "agent_id": "test-kafka",
        "timestamp": 123.45,
        "event_type": "test_event",
        "payload": {"key": "value"}
    }
    await transport.send_event("events", event_payload)

    mock_producer.send_and_wait.assert_called_once()
    assert mock_producer.send_and_wait.call_args[0][0] == "events"
    sent_data = json.loads(mock_producer.send_and_wait.call_args[0][1].decode('utf-8'))
    assert sent_data == event_payload

    await transport.close()
    mock_producer.stop.assert_called_once()


@pytest.mark.asyncio
async def test_kafka_transport_receive_commands(monkeypatch):
    mock_producer = AsyncMock()
    mock_consumer = AsyncMock()
    mock_consumer.start = AsyncMock()
    mock_consumer.stop = AsyncMock()

    # Create an async generator for mock_consumer.__aiter__
    async def mock_aiter_messages():
        yield MagicMock(value=json.dumps({
            "agent_id": "test-kafka",
            "action_id": "1",
            "action_type": "process_kill",
            "timestamp": 123.45,
            "payload": {"pid": 123}
        }).encode('utf-8'))
        yield MagicMock(value=b"invalid json") # Simulate bad message
        await asyncio.sleep(0.1) # Simulate some delay

    mock_consumer.__aiter__.return_value = mock_aiter_messages()

    monkeypatch.setattr("bus.kafka_bus.AIOKafkaProducer", MagicMock(return_value=mock_producer))
    monkeypatch.setattr("bus.kafka_bus.AIOKafkaConsumer", MagicMock(return_value=mock_consumer))

    transport = KafkaTransport(
        bootstrap_servers="localhost:9092",
        events_topic="events",
        commands_topic="commands",
        consumer_group_id="test_group"
    )
    await transport.connect()

    received_commands = []
    # Using a timeout to ensure the test doesn't hang
    with pytest.raises(asyncio.TimeoutError):
        async for command in transport.receive_commands("commands"):
            received_commands.append(command)
            if len(received_commands) == 1: # Only expect one valid command
                break
            await asyncio.sleep(0.01) # Yield control
    
    assert len(received_commands) == 1
    assert received_commands[0].action_type == "process_kill"
    assert received_commands[0].payload["pid"] == 123

    await transport.close()
    mock_consumer.stop.assert_called_once()
