from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy Cloud Security Service",
    description="Retired caller-credential cloud-posture boundary; no cloud credential or discovery surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_cloud_security_api(legacy_path: str = ""):
    """Fail closed instead of accepting cloud credentials or running ungoverned posture checks."""
    return error_response(
        code="LEGACY_CLOUD_SECURITY_API_RETIRED",
        message=(
            "The legacy cloud security API is retired. Use deployment-managed credentials "
            "and governed tenant-scoped cloud integrations."
        ),
        status_code=410,
    )
