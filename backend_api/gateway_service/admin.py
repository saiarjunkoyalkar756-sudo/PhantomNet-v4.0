from __future__ import annotations

from fastapi import APIRouter

from backend_api.core.response import error_response


router = APIRouter(prefix="/admin", tags=["Admin"])


def _retired_legacy_gateway_admin_api():
    return error_response(
        code="LEGACY_GATEWAY_ADMIN_API_RETIRED",
        message=(
            "The legacy gateway administration surface is retired. Administrative user "
            "and network-control operations require a governed, tenant-scoped control "
            "plane with durable audit evidence."
        ),
        status_code=410,
    )


@router.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_gateway_admin_api(legacy_path: str = ""):
    """Fail closed instead of exposing unscoped legacy administrative routes."""
    return _retired_legacy_gateway_admin_api()
