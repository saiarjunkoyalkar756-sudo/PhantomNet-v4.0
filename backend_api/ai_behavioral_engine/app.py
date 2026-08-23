from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy AI Behavioral Engine",
    description="Retired ungoverned behavioral-analysis boundary; no direct event-analysis surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_ai_behavioral_api(legacy_path: str = ""):
    """Fail closed instead of analyzing arbitrary event data or exposing user profiles."""
    return error_response(
        code="LEGACY_AI_BEHAVIORAL_API_RETIRED",
        message=(
            "The legacy AI behavioral API is retired. Use evidence-bound, tenant-scoped, "
            "policy-gated advisory and governed detection workflows."
        ),
        status_code=410,
    )
