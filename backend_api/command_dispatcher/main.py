"""Fail-closed compatibility boundary for legacy direct agent-command dispatch."""

from backend_api.shared.service_factory import create_phantom_service


app = create_phantom_service(
    name="Legacy Command Dispatcher Compatibility Boundary",
    description=(
        "Retired direct agent-command broker-consumer boundary; no agent command "
        "consumer or execution path is exposed."
    ),
    version="1.0.0",
    required_dependencies=(),
)


@app.get("/health_detailed")
async def health_detailed() -> dict[str, str]:
    """Report retirement rather than implying a direct command dispatch capability."""
    return {
        "status": "legacy-command-dispatcher-retired",
        "detail": (
            "Direct agent-command consumption is retired. Use human-approved, HMAC-audited "
            "governed containment and operator-provisioned signing controls."
        ),
    }
