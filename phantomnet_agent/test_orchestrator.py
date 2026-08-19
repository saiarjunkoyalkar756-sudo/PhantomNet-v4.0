import asyncio
from datetime import datetime
import pytest

from phantomnet_agent.orchestrator import NormalizedEvent, Orchestrator
from phantomnet_agent.schemas.events import AIAnalysisResult


def _uninitialized_orchestrator() -> Orchestrator:
    """Exercise pure orchestrator logic without starting agents, Kafka, or network fan-out."""
    orchestrator = object.__new__(Orchestrator)
    orchestrator.event_queue = asyncio.Queue()
    return orchestrator


@pytest.mark.asyncio
async def test_ingest_event_queues_raw_event_without_external_side_effects():
    orchestrator = _uninitialized_orchestrator()
    event = {"event_type": "PROCESS_CREATED", "event_id": "agent-event-001"}

    await orchestrator.ingest_event(event)

    assert await orchestrator.event_queue.get() == event


@pytest.mark.asyncio
async def test_correlation_marks_known_suspicious_network_connection():
    orchestrator = _uninitialized_orchestrator()
    event = NormalizedEvent(
        agent_id="agent-001",
        timestamp=datetime.now(),
        event_type="NETWORK_CONNECTION",
        payload={"event_type": "NETWORK_CONNECTION", "remote_address": "1.2.3.4:443"},
        ai_analysis_result=AIAnalysisResult(event_id="agent-event-001", risk_score=0.0),
    )

    findings = await orchestrator._correlate_event(event)

    assert findings == ["Connection to known suspicious IP."]


@pytest.mark.asyncio
async def test_correlation_adds_high_risk_finding_without_response_execution():
    orchestrator = _uninitialized_orchestrator()
    event = NormalizedEvent(
        agent_id="agent-001",
        timestamp=datetime.now(),
        event_type="PROCESS_CREATED",
        payload={"event_type": "PROCESS_CREATED", "cmdline": "sudo id"},
        ai_analysis_result=AIAnalysisResult(event_id="agent-event-002", risk_score=85.0),
    )

    findings = await orchestrator._correlate_event(event)

    assert "Potential privileged command execution." in findings
    assert "High risk score (85.00) indicates potential severe incident." in findings
