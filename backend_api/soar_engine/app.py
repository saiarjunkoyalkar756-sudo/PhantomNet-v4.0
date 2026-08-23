from __future__ import annotations

from fastapi import FastAPI

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service

from .governed_api import router as governed_containment_router
from .governed_containment import init_governed_containment_store


async def governed_soar_startup(_app: FastAPI) -> None:
    """Initialize only the durable store required by the governed containment workflow."""
    await init_governed_containment_store()


app = create_phantom_service(
    name="SOAR Engine",
    description="Governed human-approved containment control plane; legacy unscoped SOAR routes are retired.",
    version="1.0.0",
    custom_startup=governed_soar_startup,
    required_dependencies=("database",),
)
app.include_router(governed_containment_router, prefix="/api/soar")


@app.api_route(
    "/api/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_soar_api(legacy_path: str = ""):
    """Fail closed instead of executing legacy playbooks or accepting caller-supplied approvals."""
    return error_response(
        code="LEGACY_SOAR_API_RETIRED",
        message=(
            "The legacy SOAR API is retired. Use the tenant-scoped governed containment "
            "workflow, which requires human approval, signed audit evidence, verification, and rollback."
        ),
        status_code=410,
    )
