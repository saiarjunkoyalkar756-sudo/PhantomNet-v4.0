"""Attack Graph Engine entry point with governed tenant-scoped analysis only.

The historical unscoped event consumer and direct traversal workflow are retired. The
included governed router projects authenticated-tenant evidence and performs bounded,
read-only analysis without response-execution authority.
"""

from fastapi import FastAPI

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service

from .governed_api import router as governed_attack_path_router


RETIREMENT_CODE = "LEGACY_UNSCOPED_ATTACK_GRAPH_RETIRED"

app = create_phantom_service(
    name="Attack Graph Engine",
    description="Governed tenant-scoped attack-path analysis service.",
    version="1.0.0",
)
app.include_router(governed_attack_path_router, prefix="/api")


@app.post("/api/attack-graph/find-paths", include_in_schema=False)
async def find_attack_paths():
    """Fail closed for the historical unscoped traversal API."""
    return error_response(
        code=RETIREMENT_CODE,
        message=(
            "The legacy unscoped attack-graph traversal and event consumer are retired. "
            "Use the governed tenant-scoped attack-path analysis API."
        ),
        status_code=410,
    )
