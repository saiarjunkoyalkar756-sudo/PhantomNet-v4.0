from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy PNQL Engine Service",
    description="Retired untenant-scoped query executor; no direct parser or execution surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_pnql_api(legacy_path: str = ""):
    """Fail closed instead of executing unauthenticated direct query requests."""
    return error_response(
        code="LEGACY_PNQL_API_RETIRED",
        message="The legacy PNQL API is retired. Use governed tenant-scoped analytical workflows.",
        status_code=410,
    )
