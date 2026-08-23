from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy Forensics Engine",
    description="Retired ungoverned forensic-job and evidence-routing boundary; no forensic control surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_forensics_api(legacy_path: str = ""):
    """Fail closed instead of scheduling placeholder forensic work or exposing unscoped evidence state."""
    return error_response(
        code="LEGACY_FORENSICS_API_RETIRED",
        message=(
            "The legacy forensics API is retired. Use governed tenant-scoped evidence intake "
            "and analyst-authorized investigation workflows."
        ),
        status_code=410,
    )
