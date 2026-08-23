from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy DFIR Toolkit Service",
    description="Retired ungoverned forensic analysis and upload boundary; no path-based analysis or file intake is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_dfir_api(legacy_path: str = ""):
    """Fail closed instead of accepting server paths or ungoverned forensic uploads."""
    return error_response(
        code="LEGACY_DFIR_API_RETIRED",
        message=(
            "The legacy DFIR API is retired. Use governed tenant-scoped evidence intake "
            "and analyst-authorized forensic workflows."
        ),
        status_code=410,
    )
