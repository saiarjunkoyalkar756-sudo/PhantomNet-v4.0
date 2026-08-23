from __future__ import annotations

from fastapi import APIRouter, WebSocket, status

from backend_api.core.response import error_response


router = APIRouter(tags=["Agents"])


def _retired_legacy_gateway_agent_api():
    return error_response(
        code="LEGACY_GATEWAY_AGENT_API_RETIRED",
        message=(
            "The legacy gateway agent-management surface is retired. Agent enrollment, "
            "identity, configuration, and lifecycle operations require a governed, "
            "tenant-scoped control plane."
        ),
        status_code=410,
    )


@router.api_route(
    "/agents/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_gateway_agent_api(legacy_path: str = ""):
    """Fail closed instead of exposing legacy agent enrollment and management routes."""
    return _retired_legacy_gateway_agent_api()


@router.websocket("/ws/agent-events")
async def retired_legacy_agent_events_websocket(websocket: WebSocket):
    """Reject the former unauthenticated legacy agent-event subscription."""
    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
