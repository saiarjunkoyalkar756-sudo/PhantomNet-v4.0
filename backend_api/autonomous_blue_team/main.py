from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy Autonomous Blue Team Service",
    description="Retired ungoverned defensive-action and action-history boundary; no response control surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_autonomous_blue_team_api(legacy_path: str = ""):
    """Fail closed instead of accepting ungoverned defense requests or exposing local action state."""
    return error_response(
        code="LEGACY_AUTONOMOUS_BLUE_TEAM_API_RETIRED",
        message=(
            "The legacy autonomous blue-team API is retired. High-impact containment "
            "must use the governed approval, audit, verification, and rollback workflow."
        ),
        status_code=410,
    )
