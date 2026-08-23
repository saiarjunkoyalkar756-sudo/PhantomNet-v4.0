from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy PhantomQL Service",
    description="Retired untenant-scoped query boundary; no direct event-query or analytics surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_phantomql_api(legacy_path: str = ""):
    """Fail closed instead of allowing direct unauthenticated cross-tenant event queries."""
    return error_response(
        code="LEGACY_PHANTOMQL_API_RETIRED",
        message="The legacy PhantomQL API is retired. Use governed tenant-scoped analytical workflows.",
        status_code=410,
    )
