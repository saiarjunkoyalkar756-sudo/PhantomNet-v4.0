from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy Breach and Attack Simulation Engine",
    description="Retired ungoverned simulation and result-disclosure boundary; no BAS execution surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_bas_api(legacy_path: str = ""):
    """Fail closed instead of starting arbitrary-target simulations or disclosing local results."""
    return error_response(
        code="LEGACY_BAS_API_RETIRED",
        message=(
            "The legacy BAS API is retired. Use controlled, tenant-scoped, "
            "authorized simulation workflows with no-live-target safeguards."
        ),
        status_code=410,
    )
