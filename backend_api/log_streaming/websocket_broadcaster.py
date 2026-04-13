import asyncio
from fastapi import WebSocket
from typing import List, Any
import json
from loguru import logger

class WebsocketBroadcaster:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accepts a new WebSocket connection and adds it to the list of active connections.
        """
        await websocket.accept()
        self.connections.append(websocket)
        logger.info(f"New WebSocket connection established: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        """
        Removes a WebSocket connection from the list of active connections.
        """
        self.connections.remove(websocket)
        logger.info(f"WebSocket connection closed: {websocket.client}")

    async def broadcast(self, message: Any):
        """
        Broadcasts a message to all active WebSocket connections.
        """
        if isinstance(message, dict) or isinstance(message, list):
            message_str = json.dumps(message)
        else:
            message_str = str(message)
            
        # Create a list of tasks for sending messages
        tasks = [self._send_message(connection, message_str) for connection in self.connections]
        
        # Run all send tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle connections that might have closed in the meantime
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # The connection is likely closed, remove it from the list
                closed_connection = self.connections[i]
                logger.warning(f"Failed to send message to {closed_connection.client}. Removing connection.")
                # We can't remove it directly while iterating, so we'll build a new list
                # This is handled more safely below

        # Clean up closed connections
        active_connections = []
        for i, result in enumerate(results):
            if not isinstance(result, Exception):
                active_connections.append(self.connections[i])
        self.connections = active_connections


    async def _send_message(self, websocket: WebSocket, message: str):
        """
        Helper function to send a message to a single WebSocket.
        This allows us to catch exceptions for individual connections.
        """
        await websocket.send_text(message)

# Create a single, globally accessible instance of the broadcaster
broadcaster = WebsocketBroadcaster()
