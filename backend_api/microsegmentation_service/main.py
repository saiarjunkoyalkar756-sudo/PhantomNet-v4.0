from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy Micro-Segmentation Service",
    description="Retired fixture micro-segmentation boundary; no topology, policy, or enforcement surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/api/v1/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_microsegmentation_api(legacy_path: str = ""):
    """Fail closed instead of exposing fixture topology or ungoverned policy behavior."""
    return error_response(
        code="LEGACY_MICROSEGMENTATION_API_RETIRED",
        message="The legacy micro-segmentation API is retired. Use governed tenant-scoped network policy integrations.",
        status_code=410,
    )
