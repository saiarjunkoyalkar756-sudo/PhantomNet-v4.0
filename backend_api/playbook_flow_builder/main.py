from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy Playbook Flow Builder",
    description="Retired ungoverned playbook-flow conversion boundary; no response-workflow construction surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/api/v1/playbook-builder/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
@app.api_route(
    "/api/v1/playbook-builder",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_playbook_builder_api(legacy_path: str = ""):
    """Fail closed instead of constructing ungoverned playbook step sequences."""
    return error_response(
        code="LEGACY_PLAYBOOK_FLOW_BUILDER_API_RETIRED",
        message=(
            "The legacy playbook flow builder API is retired. Use governed tenant-scoped "
            "response workflows with approval, audit, verification, and rollback controls."
        ),
        status_code=410,
    )
