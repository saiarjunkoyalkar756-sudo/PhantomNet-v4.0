from types import SimpleNamespace

from fastapi import HTTPException
import pytest

from backend_api.agent_command_service import api as command_api


class _DeliveryReceipt:
    def get(self, timeout: int):
        return {"timeout": timeout}


class _RecordingProducer:
    def __init__(self):
        self.messages: list[tuple[str, dict]] = []

    def send(self, topic: str, value: dict) -> _DeliveryReceipt:
        self.messages.append((topic, value))
        return _DeliveryReceipt()


class _AuditFailingProducer(_RecordingProducer):
    def send(self, topic: str, value: dict) -> _DeliveryReceipt:
        self.messages.append((topic, value))
        if topic == command_api.AUDIT_EVENTS_TOPIC:
            return _FailingDeliveryReceipt()
        return _DeliveryReceipt()


class _FailingDeliveryReceipt:
    def get(self, timeout: int):
        raise TimeoutError("audit broker unavailable")


@pytest.mark.asyncio
async def test_authorized_agent_command_is_audited_before_dispatch(monkeypatch):
    producer = _RecordingProducer()
    monkeypatch.setattr(command_api, "get_kafka_producer", lambda: producer)
    current_user = SimpleNamespace(tenant_id="tenant-001", username="analyst-1")

    result = await command_api.send_agent_command(
        "agent-009",
        command_api.AgentCommandPayload(
            command_type="collect_processes",
            arguments={"include_hashes": True},
            task_id="task-001",
        ),
        current_user,
    )

    assert result["data"]["task_id"] == "task-001"
    assert [topic for topic, _ in producer.messages] == [
        command_api.AUDIT_EVENTS_TOPIC,
        command_api.AGENT_COMMANDS_TOPIC,
    ]
    audit_event = producer.messages[0][1]
    command_event = producer.messages[1][1]
    assert audit_event == {
        "event_type": "agent.command.requested",
        "tenant_id": "tenant-001",
        "actor_id": "analyst-1",
        "target_agent_id": "agent-009",
        "command_type": "collect_processes",
        "task_id": "task-001",
        "timestamp": command_event["issued_at"],
        "status": "requested",
    }
    assert command_event["arguments"] == {"include_hashes": True}


@pytest.mark.asyncio
async def test_audit_publish_failure_prevents_agent_command_dispatch(monkeypatch):
    producer = _AuditFailingProducer()
    monkeypatch.setattr(command_api, "get_kafka_producer", lambda: producer)
    current_user = SimpleNamespace(tenant_id="tenant-001", username="admin-1")

    with pytest.raises(HTTPException) as unavailable:
        await command_api.send_network_action(
            command_api.NetworkActionPayload(action="block_ip", agent_id="agent-010", task_id="task-002"),
            current_user,
        )

    assert unavailable.value.status_code == 503
    assert [topic for topic, _ in producer.messages] == [command_api.AUDIT_EVENTS_TOPIC]
