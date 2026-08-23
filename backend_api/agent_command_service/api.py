"""Fail-closed boundary for legacy direct agent-command dispatch."""

from __future__ import annotations

from fastapi import APIRouter

from backend_api.core.response import error_response


router = APIRouter(prefix="/api/v1/agents", tags=["Agent Commands"])


def _retired_direct_agent_command_api():
    return error_response(
        code="LEGACY_DIRECT_AGENT_COMMAND_API_RETIRED",
        message=(
            "Direct agent command dispatch is retired. High-impact endpoint actions must "
            "use a governed, tenant-scoped request, approval, audit, execution, "
            "verification, and rollback lifecycle."
        ),
        status_code=410,
    )


@router.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_direct_agent_command_api(legacy_path: str = ""):
    """Fail closed instead of signing and dispatching arbitrary direct endpoint commands."""
    return _retired_direct_agent_command_api()
