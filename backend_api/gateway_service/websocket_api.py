from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
from .websocket_manager import manager
from .log_broadcaster import log_broadcaster
import logging
from jose import JWTError, jwt
from backend_api.shared.secret_manager import get_secret
import os

logger = logging.getLogger("phantomnet_gateway.websocket_api")

SECRET_KEY = get_secret("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

router = APIRouter()

async def verify_ws_token(websocket: WebSocket) -> bool:
    """Verifies the JWT token from query parameters."""
    token = websocket.query_params.get("token")
    if not token:
        logger.warning(f"WebSocket connection attempt without token from {websocket.client.host}")
        return False
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return True
    except JWTError:
        logger.error(f"WebSocket JWT validation failed for {websocket.client.host}")
        return False

@router.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    if not await verify_ws_token(websocket):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket)
    try:
        while True:
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
    if not await verify_ws_token(websocket):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await log_broadcaster.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        log_broadcaster.disconnect(websocket)
    except Exception as e:
        logger.error(f"Logs WebSocket error for client {websocket.client.host}: {e}", exc_info=True)
        log_broadcaster.disconnect(websocket)
