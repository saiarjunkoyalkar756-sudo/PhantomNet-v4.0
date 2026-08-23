from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy Honeypot Service",
    description="Retired honeypot lifecycle boundary; no process listener or runner is exposed by this service.",
    version="0.1.0",
    required_dependencies=(),
)


@app.api_route(
    "/honeypots/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
@app.api_route(
    "/honeypots",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_honeypot_api(legacy_path: str = ""):
    """Prevent unauthenticated process lifecycle control through the legacy service."""
    return error_response(
        code="LEGACY_HONEYPOT_API_RETIRED",
        message="The legacy honeypot lifecycle API is retired. Use a governed tenant-scoped deployment integration.",
        status_code=410,
    )
