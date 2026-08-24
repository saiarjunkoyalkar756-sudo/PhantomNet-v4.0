"""Fail-closed compatibility boundary for legacy unauthenticated SIEM ingestion."""

from fastapi import APIRouter, FastAPI

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


router = APIRouter()


def _retired_legacy_siem_api():
    return error_response(
        code="LEGACY_SIEM_INGEST_API_RETIRED",
        message=(
            "Legacy SIEM ingestion and raw-log retrieval are retired because they did not "
            "authenticate the source or establish tenant-scoped evidence provenance. Use "
            "the governed tenant-scoped telemetry integration."
        ),
        status_code=410,
    )


@router.post("/ingest/", include_in_schema=False)
async def retired_legacy_single_ingest():
    """Fail closed instead of accepting unauthenticated raw events."""
    return _retired_legacy_siem_api()


@router.post("/ingest/batch", include_in_schema=False)
async def retired_legacy_batch_ingest():
    """Fail closed instead of accepting unauthenticated raw event batches."""
    return _retired_legacy_siem_api()


@router.get("/logs/{log_id}", include_in_schema=False)
async def retired_legacy_log_lookup(log_id: int):
    """Fail closed instead of exposing raw evidence without a tenant boundary."""
    return _retired_legacy_siem_api()


@router.get("/logs/", include_in_schema=False)
async def retired_legacy_log_list():
    """Fail closed instead of listing raw evidence without a tenant boundary."""
    return _retired_legacy_siem_api()


app = create_phantom_service(
    name="Legacy SIEM Compatibility Boundary",
    description="Retired raw SIEM ingestion and retrieval compatibility boundary.",
    version="1.0.0",
)

app.include_router(router, prefix="/api/v1/siem")


@app.get("/status")
async def status() -> dict[str, str]:
    return {
        "status": "legacy-siem-ingest-retired",
        "detail": "Use governed tenant-scoped telemetry integrations.",
    }
