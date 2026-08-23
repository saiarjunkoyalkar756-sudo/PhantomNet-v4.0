from __future__ import annotations

from fastapi import APIRouter

from backend_api.core.response import error_response


router = APIRouter()


@router.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_soc_copilot_router(legacy_path: str = ""):
    """Fail closed if the legacy standalone copilot router is mounted elsewhere."""
    return error_response(
        code="LEGACY_SOC_COPILOT_API_RETIRED",
        message=(
            "The legacy SOC copilot API is retired. Use evidence-bound, tenant-scoped, "
            "policy-gated advisory workflows that do not execute actions."
        ),
        status_code=410,
    )
