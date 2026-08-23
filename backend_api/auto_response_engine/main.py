from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy Auto-Response Engine",
    description="Retired ungoverned playbook-execution boundary; response actions are not exposed here.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_auto_response_api(legacy_path: str = ""):
    """Fail closed instead of running untenant-scoped simulated response actions."""
    return error_response(
        code="LEGACY_AUTO_RESPONSE_API_RETIRED",
        message=(
            "The legacy auto-response API is retired. High-impact containment must use "
            "the governed approval, audit, verification, and rollback workflow."
        ),
        status_code=410,
    )
