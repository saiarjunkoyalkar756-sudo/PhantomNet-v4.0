from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy Lateral Movement Detector",
    description="Retired ungoverned lateral-movement analysis boundary; no direct event-analysis surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/api/v1/lateral-movement/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
@app.api_route(
    "/api/v1/lateral-movement",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_lateral_movement_api(legacy_path: str = ""):
    """Fail closed instead of analyzing arbitrary untenant-scoped security event batches."""
    return error_response(
        code="LEGACY_LATERAL_MOVEMENT_API_RETIRED",
        message=(
            "The legacy lateral-movement API is retired. Use governed tenant-scoped "
            "detection, correlation, and analyst investigation workflows."
        ),
        status_code=410,
    )
