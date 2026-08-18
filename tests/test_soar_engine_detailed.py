# tests/test_soar_engine_detailed.py
import pytest
from unittest.mock import patch, MagicMock
from backend_api.soar_engine.consumer import (
    block_ip, isolate_host, create_ticket, execute_playbook
)
from backend_api.soar_engine.models import Playbook, PlaybookStep, PlaybookRun, PlaybookStatus

def test_block_ip_action():
    """Verify that an allowlisted block action is truthful in default dry-run mode."""
    result = block_ip("198.51.100.42")
    assert result["status"] == "success"
    assert result["enforced"] is False
    assert result["verified"] is False
    assert "Dry-run" in result["detail"]


def test_isolate_host_action():
    """Verify that unsupported host isolation does not claim enforcement."""
    result = isolate_host("compromised-server")
    assert result["status"] == "failure"
    assert result["enforced"] is False
    assert "requires a configured endpoint-management provider" in result["detail"]


def test_create_ticket_action():
    """Verify that the create_ticket action initiates ticket creation in ITSM."""
    result = create_ticket(
        title="Incident alert",
        description="Critical alert raised.",
        priority="high"
    )
    assert result["status"] == "success"
    assert "ticket_id" in result
    assert result["ticket_id"].startswith("INC-")

@pytest.mark.asyncio
async def test_critical_alert_triggers_forensics():
    """Verify that critical severity alerts trigger automated forensic workflow."""
    mock_playbook = Playbook(
        name="Critical Alert Playbook",
        description="Handles critical level alerts.",
        trigger={"severity": "critical"},
        steps=[
            PlaybookStep(action="isolate_host", tool_name="EDR", parameters={"hostname": "{{ event.host }}"}),
            PlaybookStep(action="create_ticket", tool_name="ITSM", parameters={"title": "Forensic Escalation", "description": "Triggered", "priority": "critical"})
        ]
    )
    
    mock_run = PlaybookRun(
        run_id="run-1234",
        playbook_name=mock_playbook.name,
        triggered_by={"severity": "critical", "host": "database-prod"},
        playbook=mock_playbook,
        current_context={"event": {"host": "database-prod"}, "context": {}}
    )

    with patch("backend_api.soar_engine.consumer.ACTION_MAP") as mock_actions:
        mock_actions.get.return_value = MagicMock(return_value={"status": "success", "detail": "Executed"})
        # Run execution
        execute_playbook(mock_run)
        assert mock_run.status == PlaybookStatus.COMPLETED
        assert len(mock_run.execution_logs) == 2
