from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy Analyzer Service",
    description="Retired ungoverned analyzer chat and consumer boundary; no AI analysis surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_analyzer_api(legacy_path: str = ""):
    """Fail closed instead of serving an unauthenticated analyzer or starting legacy consumers."""
    return error_response(
        code="LEGACY_ANALYZER_API_RETIRED",
        message=(
            "The legacy analyzer API is retired. Use governed tenant-scoped advisory "
            "workflows with evidence, policy, and analyst controls."
        ),
        status_code=410,
    )
