from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy Compliance Reporting Service",
    description="Retired fixture-backed compliance report and PDF boundary; no report generation or download surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_compliance_reporting_api(legacy_path: str = ""):
    """Fail closed instead of generating or disclosing unscoped fixture compliance reports."""
    return error_response(
        code="LEGACY_COMPLIANCE_REPORTING_API_RETIRED",
        message=(
            "The legacy compliance reporting API is retired. Use governed tenant-scoped "
            "evidence collection and report-generation workflows."
        ),
        status_code=410,
    )
