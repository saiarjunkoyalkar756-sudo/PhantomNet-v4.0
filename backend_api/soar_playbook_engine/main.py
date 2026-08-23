from __future__ import annotations

from fastapi import APIRouter

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


router = APIRouter()


@router.api_route("/playbooks", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
@router.api_route("/playbooks/{legacy_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
@router.api_route("/playbook_runs", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
@router.api_route("/playbook_runs/{legacy_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
@router.api_route("/playbook_approvals", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
@router.api_route("/playbook_approvals/{legacy_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
async def retired_legacy_soar_api(legacy_path: str = ""):
    """Block the non-tenant legacy playbook API rather than retaining an approval bypass."""
    return error_response(
        code="LEGACY_SOAR_PLAYBOOK_API_RETIRED",
        message="The legacy playbook API is retired. Use the tenant-scoped governed containment APIs with required approval.",
        status_code=410,
    )


app = create_phantom_service(
    name="Legacy SOAR Playbook Engine",
    description="Retired legacy playbook boundary; governed containment is the supported approval-bound control plane.",
    version="1.0.0",
    required_dependencies=(),
)
app.include_router(router)
