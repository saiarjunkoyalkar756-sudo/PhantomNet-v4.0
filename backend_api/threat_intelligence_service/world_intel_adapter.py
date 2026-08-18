"""Read-only World Intel enrichment boundary for PhantomNet.

This module deliberately separates intelligence context from enforcement.  It accepts an
injected MCP transport for testability; deployment may supply a stdio transport only after
its server command and tool allowlist are reviewed by an operator.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Protocol


READ_ONLY_TOOLS = frozenset({"search_intelligence", "get_geopolitical_context", "lookup_indicator_context"})


class WorldIntelTransport(Protocol):
    def __call__(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]: ...


@dataclass(frozen=True)
class IntelligenceEvidence:
    provider: str
    tool_name: str
    indicator: str
    retrieved_at: str
    data: Dict[str, Any]
    provenance: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "tool_name": self.tool_name,
            "indicator": self.indicator,
            "retrieved_at": self.retrieved_at,
            "data": self.data,
            "provenance": self.provenance,
        }


class WorldIntelEnricher:
    def __init__(self, transport: WorldIntelTransport | None = None, allowed_tools: frozenset[str] = READ_ONLY_TOOLS) -> None:
        self.transport = transport
        self.allowed_tools = allowed_tools

    def enrich(self, indicator: str, tool_name: str = "lookup_indicator_context") -> Dict[str, Any]:
        if tool_name not in self.allowed_tools:
            return {"status": "failure", "detail": "Requested World Intel tool is not in the read-only allowlist.", "evidence": None}
        if self.transport is None:
            return {"status": "unavailable", "detail": "World Intel transport is not configured; no external request was made.", "evidence": None}

        raw = self.transport(tool_name, {"indicator": indicator})
        evidence = IntelligenceEvidence(
            provider="world-intel-mcp",
            tool_name=tool_name,
            indicator=indicator,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            data=raw,
            provenance={"transport": "mcp-stdio", "read_only": True, "automation": "prohibited"},
        )
        return {"status": "success", "detail": "Read-only intelligence evidence retrieved.", "evidence": evidence.as_dict()}


def correlate_evidence(event: Dict[str, Any], enrichment: Dict[str, Any]) -> Dict[str, Any]:
    """Join evidence to an event without turning intelligence into an automated response."""
    evidence = enrichment.get("evidence")
    return {
        "event_id": event.get("event_id"),
        "correlation_id": event.get("correlation_id"),
        "evidence": evidence,
        "confidence": "contextual" if evidence else "none",
        "response_recommendation": "human_review_required",
        "automatic_enforcement": False,
    }
