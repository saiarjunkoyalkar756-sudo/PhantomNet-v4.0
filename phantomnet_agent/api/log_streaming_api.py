from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import List, Optional, Dict, Any
import os
import asyncio
import logging
from pathlib import Path
import json
from utils.logger import AGENT_OUTPUT_LOG_PATH # Import the path to the structured log file

router = APIRouter()
logger = logging.getLogger("phantomnet_agent.log_streaming_api")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.log_queue = asyncio.Queue() # Queue for logs coming from LogForwarder

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected: {websocket.client}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                self.disconnect(connection)
            except Exception as e:
                logger.error(f"Error broadcasting message to WebSocket client {connection.client}: {e}")
                self.disconnect(connection)

    async def ingest_log(self, log_entry: str):
        """
        Ingests a log entry from an internal component (e.g., LogForwarder)
        and adds it to the queue for broadcasting.
        """
        await self.log_queue.put(log_entry)

    async def broadcast_logs_from_queue(self):
        """
        Continuously takes logs from the queue and broadcasts them to connected clients.
        """
        while True:
            log_entry = await self.log_queue.get()
            if log_entry:
                await self.broadcast(log_entry)
            self.log_queue.task_done()

manager = ConnectionManager()

@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive, clients might send pings, or just wait for disconnect
            _ = await websocket.receive_text() # Clients can send messages, but we don't process them here yet
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error for client {websocket.client}: {e}")
        manager.disconnect(websocket)

# Helper function to read recent lines from a file
async def get_recent_logs_from_file(file_path: Path, num_lines: int) -> List[Dict[str, Any]]:
    logs = []
    if not file_path.exists():
        return logs
    
    try:
        # Read the file in reverse to get the most recent lines efficiently
        # This is a basic implementation; for very large files, more optimized solutions exist
        with open(file_path, 'r') as f:
            # Go to the end of the file
            f.seek(0, os.SEEK_END)
            buffer = bytearray()
            ptr = f.tell() # Current position

            while ptr >= 0 and len(logs) < num_lines:
                ptr -= 1
                f.seek(ptr)
                char = f.read(1)
                if char == '\n' and buffer:
                    line = buffer[::-1].decode('utf-8') # Reverse buffer and decode
                    try:
                        logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse log line as JSON: {line[:100]}...")
                    buffer = bytearray() # Clear buffer for next line
                elif char != '\n':
                    buffer.extend(char.encode('utf-8'))
            
            if buffer and len(logs) < num_lines: # Add the last line if any
                line = buffer[::-1].decode('utf-8')
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse log line as JSON: {line[:100]}...")
    except Exception as e:
        logger.error(f"Error reading log file {file_path}: {e}")
    
    return logs[::-1] # Return in chronological order


@router.get("/agent/logs/tail", response_model=List[Dict[str, Any]])
async def tail_agent_logs(lines: int = Query(100, ge=1, le=1000)) -> List[Dict[str, Any]]:
    """
    Returns the most recent N structured log entries from logs/agent_output.log.
    """
    return await get_recent_logs_from_file(AGENT_OUTPUT_LOG_PATH, lines)

# Start the background task for broadcasting logs from the queue
@router.on_event("startup")
async def startup_event():
    asyncio.create_task(manager.broadcast_logs_from_queue())
