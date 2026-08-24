"""Fail-closed compatibility boundary for the retired standalone audit-log collector API.

The integrity and verification modules in this package remain internal dependencies of the
separately governed containment lifecycle.  They are not exposed through this legacy
HTTP service.
"""

from fastapi import APIRouter, FastAPI, status

from backend_api.core.response import error_response, success_response
from backend_api.shared.service_factory import create_phantom_service


RETIREMENT_CODE = "LEGACY_AUDIT_LOG_COLLECTOR_API_RETIRED"
RETIREMENT_MESSAGE = (
    "The standalone audit-log collector API is retired because it accepted and returned "
    "audit records without tenant scope, authorization, source provenance, or immutable "
    "audit controls. Use the governed containment audit lifecycle instead."
)

router = APIRouter()

app = create_phantom_service(
    name="Legacy Audit Log Compatibility Boundary",
    description="Retired standalone audit-log collector compatibility boundary.",
    version="1.0.0",
    required_dependencies=(),
)


def _retired_audit_log_collector_response():
    return error_response(
        code=RETIREMENT_CODE,
        message=RETIREMENT_MESSAGE,
        status_code=status.HTTP_410_GONE,
    )


@router.post("/ingest/", include_in_schema=False)
async def ingest_single_audit_log():
    return _retired_audit_log_collector_response()


@router.post("/ingest/batch", include_in_schema=False)
async def ingest_batch_audit_logs():
    return _retired_audit_log_collector_response()


@router.get("/logs/", include_in_schema=False)
async def get_audit_logs():
    return _retired_audit_log_collector_response()


@app.get("/status", include_in_schema=False)
async def audit_log_collector_status():
    return success_response(
        data={
            "service": "audit-log-collector",
            "status": "legacy-audit-log-collector-retired",
            "retirement_code": RETIREMENT_CODE,
            "governed_replacement": "governed containment audit lifecycle",
        }
    )


app.include_router(router)
