"""Fail-closed compatibility boundary for legacy unauthenticated log normalization."""

from fastapi import APIRouter

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


router = APIRouter()


def _retired_legacy_normalization_api():
    return error_response(
        code="LEGACY_LOG_NORMALIZER_API_RETIRED",
        message=(
            "Legacy HTTP log normalization is retired because it did not authenticate the "
            "source or establish tenant-scoped event provenance. Use the canonical "
            "tenant-aware event-normalization pipeline."
        ),
        status_code=410,
    )


@router.post("/normalize/", include_in_schema=False)
async def retired_legacy_normalize_single():
    """Fail closed instead of normalizing unauthenticated raw input."""
    return _retired_legacy_normalization_api()


@router.post("/normalize/batch", include_in_schema=False)
async def retired_legacy_normalize_batch():
    """Fail closed instead of normalizing unauthenticated raw batches."""
    return _retired_legacy_normalization_api()


app = create_phantom_service(
    name="Legacy Log Normalizer Compatibility Boundary",
    description="Retired unauthenticated HTTP log-normalization compatibility boundary.",
    version="1.0.0",
)

app.include_router(router, prefix="/api/v1/normalizer")


@app.get("/status")
async def status() -> dict[str, str]:
    return {
        "status": "legacy-log-normalizer-retired",
        "detail": "Use the canonical tenant-aware event-normalization pipeline.",
    }
