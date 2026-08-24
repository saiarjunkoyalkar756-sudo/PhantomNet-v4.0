"""Fail-closed compatibility boundary for the retired standalone compliance API.

This legacy process previously exposed mutable compliance standards and assessments
without tenant ownership, authorization, evidence provenance, or a governed remediation
lifecycle. The separate shared compliance-engine utility is not exposed by this boundary.
"""

from fastapi import APIRouter, status

from backend_api.core.response import error_response, success_response
from backend_api.shared.service_factory import create_phantom_service


RETIREMENT_CODE = "LEGACY_COMPLIANCE_API_RETIRED"
RETIREMENT_MESSAGE = (
    "The standalone compliance API is retired because it exposed mutable standards and "
    "assessments without tenant scope, authorization, evidence provenance, or governed "
    "remediation controls."
)

router = APIRouter()

app = create_phantom_service(
    name="Legacy Compliance Compatibility Boundary",
    description="Retired standalone compliance API compatibility boundary.",
    version="1.0.0",
    required_dependencies=(),
)


def _retired_compliance_response():
    return error_response(
        code=RETIREMENT_CODE,
        message=RETIREMENT_MESSAGE,
        status_code=status.HTTP_410_GONE,
    )


@router.post("/standards/", include_in_schema=False)
async def create_standard():
    return _retired_compliance_response()


@router.get("/standards/", include_in_schema=False)
async def read_standards():
    return _retired_compliance_response()


@router.get("/standards/{standard_name}", include_in_schema=False)
async def read_standard(standard_name: str):
    del standard_name
    return _retired_compliance_response()


@router.post("/assessments/", include_in_schema=False)
async def create_assessment():
    return _retired_compliance_response()


@router.get("/assessments/", include_in_schema=False)
async def read_assessments():
    return _retired_compliance_response()


@router.get("/assessments/{assessment_id}", include_in_schema=False)
async def read_assessment(assessment_id: str):
    del assessment_id
    return _retired_compliance_response()


@router.put("/assessments/{assessment_id}", include_in_schema=False)
async def update_assessment(assessment_id: str):
    del assessment_id
    return _retired_compliance_response()


@app.get("/status", include_in_schema=False)
async def compliance_status():
    return success_response(
        data={
            "service": "compliance-service",
            "status": "legacy-compliance-api-retired",
            "retirement_code": RETIREMENT_CODE,
            "governed_replacement": "no tenant-scoped compliance replacement is currently exposed",
        }
    )


app.include_router(router)
