from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy Asset Inventory Relationship Service",
    description="Retired fixture-backed asset relationship boundary; no asset or topology data is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_asset_relationship_api(legacy_path: str = ""):
    """Fail closed instead of exposing tenant-unscoped fixture inventory data."""
    return error_response(
        code="LEGACY_ASSET_RELATIONSHIP_API_RETIRED",
        message=(
            "The legacy asset relationship API is retired. Use governed tenant-scoped "
            "asset inventory and graph-investigation services."
        ),
        status_code=410,
    )
