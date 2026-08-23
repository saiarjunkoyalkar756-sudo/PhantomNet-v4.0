from __future__ import annotations

from fastapi import Request

from backend_api.core.response import error_response, success_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy PhantomNet API Gateway",
    description="Retired compatibility gateway; use the self-hosted governed gateway and tenant-scoped service APIs.",
    version="3.0.0",
    required_dependencies=(),
)


@app.get("/health_status", include_in_schema=False)
async def health_status(request: Request):
    """Compatibility liveness response; dependency-aware readiness is available at `/ready`."""
    return success_response(data={"status": "healthy", "version": "3.0.0", "legacy_gateway": "retired"})


@app.api_route("/{legacy_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"], include_in_schema=False)
async def retired_legacy_gateway(legacy_path: str):
    """Fail closed instead of exposing untenant-scoped legacy gateway routes."""
    return error_response(
        code="LEGACY_API_GATEWAY_RETIRED",
        message="This legacy gateway is retired. Use the self-hosted governed gateway and tenant-scoped APIs.",
        status_code=410,
    )
