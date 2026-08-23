from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy MITRE ATT&CK Mapper",
    description="Retired ungoverned ATT&CK dataset and event-mapping boundary; no direct mapping surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_mitre_mapper_api(legacy_path: str = ""):
    """Fail closed instead of exposing ungoverned ATT&CK mapping and dataset access."""
    return error_response(
        code="LEGACY_MITRE_MAPPER_API_RETIRED",
        message=(
            "The legacy MITRE mapper API is retired. Use governed tenant-scoped "
            "detection content and analyst investigation workflows."
        ),
        status_code=410,
    )
