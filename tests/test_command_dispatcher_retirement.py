"""Source-contract regressions for retired legacy command-dispatcher behavior."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMMAND_DISPATCHER = ROOT / "backend_api/command_dispatcher/main.py"
AGENT_COMMAND_BOUNDARY = ROOT / "backend_api/agent_command_service/api.py"
GOVERNED_SOAR_API = ROOT / "backend_api/soar_engine/governed_api.py"


def test_legacy_command_dispatcher_has_no_direct_broker_consumer_or_command_topic():
    source = COMMAND_DISPATCHER.read_text(encoding="utf-8")

    assert "agent-commands" not in source
    assert "KafkaConsumer" not in source
    assert "consume_and_process_kafka_messages" not in source
    assert "asyncio.create_task" not in source
    assert "check_kafka_health" not in source
    assert "required_dependencies=()" in source


def test_dispatcher_reports_retired_boundary_with_governed_replacement_context():
    dispatcher_source = COMMAND_DISPATCHER.read_text(encoding="utf-8")
    direct_boundary_source = AGENT_COMMAND_BOUNDARY.read_text(encoding="utf-8")
    governed_source = GOVERNED_SOAR_API.read_text(encoding="utf-8")

    assert '"status": "legacy-command-dispatcher-retired"' in dispatcher_source
    assert "human-approved, HMAC-audited" in dispatcher_source
    assert "governed containment and operator-provisioned signing controls" in dispatcher_source
    assert "LEGACY_DIRECT_AGENT_COMMAND_API_RETIRED" in direct_boundary_source
    assert 'require_capability("response:approve")' in governed_source
