"""Fail-closed compatibility boundary for legacy network WebSocket ingestion."""

from fastapi import APIRouter, WebSocket, status

from backend_api.shared.service_factory import create_phantom_service


router = APIRouter()


@router.websocket("/ws/network")
async def retired_network_websocket(websocket: WebSocket) -> None:
    """Reject legacy agent streaming without accepting telemetry or broker publication."""
    await websocket.close(
        code=status.WS_1008_POLICY_VIOLATION,
        reason=(
            "Legacy network telemetry streaming is retired. Use governed, tenant-scoped, "
            "signed telemetry integration."
        ),
    )


app = create_phantom_service(
    name="Legacy Network WebSocket Compatibility Boundary",
    description="Retired fixed-agent WebSocket telemetry compatibility boundary.",
    version="1.0.0",
)
app.include_router(router)


@app.get("/status")
async def status_endpoint() -> dict[str, str]:
    return {
        "status": "legacy-network-websocket-retired",
        "detail": "Use governed tenant-scoped signed telemetry integration.",
    }
