from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy Plugin Marketplace Service",
    description="Retired unverified plugin marketplace boundary; no artifact upload or activation surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/plugins/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
@app.api_route(
    "/plugins",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_plugin_marketplace_api(legacy_path: str = ""):
    """Fail closed rather than accept unverified extension artifacts or activation changes."""
    return error_response(
        code="LEGACY_PLUGIN_MARKETPLACE_API_RETIRED",
        message="The legacy plugin marketplace API is retired. Use a governed signed-artifact deployment integration.",
        status_code=410,
    )
