from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from sqlalchemy.orm import Session
from loguru import logger
from jose import jwt, JWTError
import os

from ..iam_service.auth_methods import get_user
from ..database import get_db, AttackLog

router = APIRouter()

clients = set()

@router.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    logger.info("Client connected to /ws/events.")  # No PII
    try:
        while True:
            # Keep the connection alive. Incoming messages are not expected for this broadcast endpoint.
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)
        logger.info("Client disconnected from events.")  # No PII
    except Exception as e:
        clients.remove(websocket)
        logger.error(f"WebSocket event error: {e}", exc_info=True)  # No PII
        import traceback

        traceback.print_exc()

@router.websocket("/ws/logs")
async def websocket_log_endpoint(
    websocket: WebSocket,
    token: str = None,
    db: Session = Depends(get_db),  # Inject the database session
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user = get_user(db, username=username)
    user_id_for_logging = user.id if user else "UNKNOWN"

    await websocket.accept()
    clients.add(websocket)
    logger.info(
        f"Client connected to /ws/logs. User ID: {user_id_for_logging}"
    )
    try:
        logs = (
            db.query(AttackLog).order_by(AttackLog.timestamp.desc()).limit(100).all()
        )
        formatted_logs = [
            {
                "timestamp": log.timestamp.isoformat(),
                "ip": log.ip,
                "port": log.port,
                "data": log.data,
                "attack_type": log.attack_type,
                "confidence_score": log.confidence_score,
                "is_anomaly": log.is_anomaly,
                "anomaly_score": log.anomaly_score,
                "is_verified_threat": log.is_verified_threat,
                "is_blacklisted": log.is_blacklisted,
            }
            for log in logs
        ]
        await websocket.send_json({"type": "initial_logs", "logs": formatted_logs})

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)
        logger.info("Client disconnected from logs.")
    except Exception as e:
        clients.remove(websocket)
        logger.error(f"WebSocket log error: {e}", exc_info=True)
        import traceback

        traceback.print_exc()

async def broadcast_event(message: dict):
    logger.info(f"Broadcasting event: {message.get('type')}")
    for client in list(clients):
        try:
            await client.send_json(message)
        except RuntimeError as e:
            logger.error(f"Error sending to websocket client: {e}")
            clients.remove(client)
        except WebSocketDisconnect:
            logger.info("Client disconnected during broadcast.")
            clients.remove(client)
        except Exception as e:
            logger.error(f"Unexpected error broadcasting to client: {e}")
