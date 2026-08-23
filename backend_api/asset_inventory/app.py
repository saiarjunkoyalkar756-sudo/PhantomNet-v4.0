from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy Asset Inventory Service",
    description="Retired ungoverned asset scanning and inventory boundary; no scan or asset-data surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_asset_inventory_api(legacy_path: str = ""):
    """Fail closed instead of accepting arbitrary scan targets or disclosing unscoped assets."""
    return error_response(
        code="LEGACY_ASSET_INVENTORY_API_RETIRED",
        message=(
            "The legacy asset inventory API is retired. Use governed tenant-scoped "
            "inventory and authorized discovery workflows."
        ),
        status_code=410,
    )
