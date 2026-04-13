from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .websocket_manager import manager
from .log_broadcaster import log_broadcaster # Import the new log broadcaster
import logging

logger = logging.getLogger("phantomnet_gateway.websocket_api")

router = APIRouter()

@router.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection open. We don't expect messages from client for this stream.
            # If client sends anything, just log or ignore.
            data = await websocket.receive_text()
            logger.debug(f"Received message from client {websocket.client.host}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket client {websocket.client.host} disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error for client {websocket.client.host}: {e}", exc_info=True)
        manager.disconnect(websocket)

@router.websocket("/ws/logs")
async def logs_websocket_endpoint(websocket: WebSocket):
    await log_broadcaster.connect(websocket)
    try:
        while True:
            # Keep the connection open and listen for client messages if needed
            # For a pure broadcast, we just keep it alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        log_broadcaster.disconnect(websocket)
    except Exception as e:
        logger.error(f"Logs WebSocket error for client {websocket.client.host}: {e}", exc_info=True)
        log_broadcaster.disconnect(websocket)
