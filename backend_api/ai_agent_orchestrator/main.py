from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy AI Agent Orchestrator",
    description="Retired ungoverned AI task-planning boundary; no autonomous planning surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_ai_agent_orchestrator_api(legacy_path: str = ""):
    """Fail closed instead of accepting unscoped natural-language agent tasks."""
    return error_response(
        code="LEGACY_AI_AGENT_ORCHESTRATOR_API_RETIRED",
        message=(
            "The legacy AI agent orchestrator API is retired. Use evidence-bound, "
            "tenant-scoped, policy-gated advisory workflows that cannot execute actions."
        ),
        status_code=410,
    )
