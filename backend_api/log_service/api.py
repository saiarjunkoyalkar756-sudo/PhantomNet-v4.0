"""Fail-closed compatibility boundary for legacy raw-log retrieval routes."""

from fastapi import APIRouter

from backend_api.core.response import error_response


router = APIRouter()


def _retired_legacy_log_retrieval():
    return error_response(
        code="LEGACY_LOG_RETRIEVAL_API_RETIRED",
        message=(
            "Legacy raw-log retrieval is retired because it did not establish tenant-scoped "
            "evidence authorization or data-minimization controls. Use governed, "
            "tenant-scoped analyst evidence workflows."
        ),
        status_code=410,
    )


@router.get("/logs", include_in_schema=False)
async def retired_legacy_get_logs():
    """Fail closed instead of disclosing untenant-scoped raw attack logs."""
    return _retired_legacy_log_retrieval()


@router.get("/logs/poll", include_in_schema=False)
async def retired_legacy_poll_logs():
    """Fail closed instead of polling raw SIEM records without tenant controls."""
    return _retired_legacy_log_retrieval()
