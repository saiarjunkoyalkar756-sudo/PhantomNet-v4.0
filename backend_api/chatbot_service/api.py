from __future__ import annotations

from fastapi import APIRouter

from backend_api.core.response import error_response


router = APIRouter()


@router.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_chatbot_api(legacy_path: str = ""):
    """Fail closed instead of processing attack payloads through an ungoverned chatbot path."""
    return error_response(
        code="LEGACY_CHATBOT_API_RETIRED",
        message=(
            "The legacy chatbot API is retired. Use evidence-bound, tenant-scoped, "
            "policy-gated advisory workflows that do not expose or execute countermeasures."
        ),
        status_code=410,
    )
