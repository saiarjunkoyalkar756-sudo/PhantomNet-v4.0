from __future__ import annotations

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy Event Stream Processor",
    description="Retired untenant-scoped log-query and consumer boundary; no event-data surface is exposed.",
    version="1.0.0",
    required_dependencies=(),
)


@app.api_route(
    "/{legacy_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def retired_legacy_event_stream_processor_api(legacy_path: str = ""):
    """Fail closed instead of exposing direct cross-tenant event queries or starting legacy consumers."""
    return error_response(
        code="LEGACY_EVENT_STREAM_PROCESSOR_API_RETIRED",
        message=(
            "The legacy event stream processor API is retired. Use governed tenant-scoped "
            "telemetry ingestion and analyst-query services."
        ),
        status_code=410,
    )
