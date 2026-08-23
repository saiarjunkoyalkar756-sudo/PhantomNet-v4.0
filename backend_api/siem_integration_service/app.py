from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy SIEM Integration Service",
    description="Retired untenant-scoped SIEM ingestion and query boundary; no log-access or ingestion surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/api/siem/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
@app.api_route(
    "/api/siem",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_siem_api(legacy_path: str = ""):
    """Fail closed instead of accepting or disclosing untenant-scoped SIEM data."""
    return error_response(
        code="LEGACY_SIEM_INTEGRATION_API_RETIRED",
        message="The legacy SIEM integration API is retired. Use governed tenant-scoped ingestion and analytical services.",
        status_code=410,
    )
