# backend_api/gateway_service/log_broadcaster.py

import asyncio
from typing import List
from fastapi import WebSocket
from loguru import logger

class LogBroadcaster:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
        logger.info(f"Log WebSocket client connected: {websocket.client.host}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)
            logger.info(f"Log WebSocket client disconnected: {websocket.client.host}")

    async def broadcast(self, message: str):
        # Create a copy of the list to handle disconnections during iteration
        for connection in self.connections[:]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send log to client {connection.client.host}, disconnecting: {e}")
                self.disconnect(connection)

log_broadcaster = LogBroadcaster()

# This function is now defined in the logger_config itself to avoid circular deps
# async def broadcast_logs_from_queue(log_queue: asyncio.Queue):
#     """
#     A coroutine that consumes logs from the global log queue and broadcasts them.
#     This runs in parallel to the main async_log_sink.
#     """
#     while True:
#         try:
#             log_record = await log_queue.get()
#             # The log_record is already a JSON string from our formatter
#             await log_broadcaster.broadcast(log_record)
#         except asyncio.CancelledError:
#             break
#         except Exception as e:
#             logger.error(f"Error in log broadcasting task: {e}", exc_info=True)
