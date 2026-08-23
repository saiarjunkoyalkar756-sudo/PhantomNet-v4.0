from __future__ import annotations

from fastapi import APIRouter

from backend_api.core.response import error_response


router = APIRouter()


def _retired_legacy_api_ecosystem():
    return error_response(
        code="LEGACY_GATEWAY_ECOSYSTEM_API_RETIRED",
        message=(
            "The legacy API ecosystem surface is retired. Use governed, tenant-scoped "
            "analytics and evidence-backed reporting workflows."
        ),
        status_code=410,
    )


@router.get("/analytics/threat_summary", include_in_schema=False)
async def retired_legacy_threat_summary():
    """Fail closed instead of returning conceptual threat analytics."""
    return _retired_legacy_api_ecosystem()


@router.get("/reports/daily_digest", include_in_schema=False)
async def retired_legacy_daily_digest():
    """Fail closed instead of disclosing a conceptual raw-log digest."""
    return _retired_legacy_api_ecosystem()


@router.post("/graphql", include_in_schema=False)
async def retired_legacy_graphql():
    """Fail closed instead of echoing caller-provided conceptual GraphQL input."""
    return _retired_legacy_api_ecosystem()
