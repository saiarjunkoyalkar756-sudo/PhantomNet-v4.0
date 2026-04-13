from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..log_streaming.websocket_broadcaster import broadcaster

router = APIRouter()

@router.websocket("/ws/logs")
async def websocket_logs_endpoint(websocket: WebSocket):
    """
    Handles WebSocket connections for real-time log streaming.
    """
    await broadcaster.connect(websocket)
    try:
        while True:
            # Keep the connection alive, waiting for messages from the client.
            # In this implementation, we don't expect messages from the client,
            # but this loop is necessary to keep the connection open.
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.disconnect(websocket)

# The user also requested /ws/logs/agent. For now, we will have it share
# the same broadcaster. A more advanced implementation could use separate
# channels or topics within the message bus.
@router.websocket("/ws/logs/agent")
async def websocket_agent_logs_endpoint(websocket: WebSocket):
    """
    Handles WebSocket connections for real-time agent log streaming.
    Currently shares the same broadcast as the main log stream.
    """
    await broadcaster.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.disconnect(websocket)
