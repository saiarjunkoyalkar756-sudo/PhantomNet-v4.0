from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy Dashboard Aggregation Service",
    description="Retired ungoverned dashboard aggregation and fabricated executive-metrics boundary.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_dashboard_api(legacy_path: str = ""):
    """Fail closed instead of aggregating unscoped incidents or serving fabricated metrics."""
    return error_response(
        code="LEGACY_DASHBOARD_API_RETIRED",
        message=(
            "The legacy dashboard aggregation API is retired. Use authenticated, "
            "tenant-scoped analyst workflows with governed evidence and case context."
        ),
        status_code=410,
    )
