import asyncio
import json
import os
from typing import List, Dict, Any
from kafka import KafkaConsumer
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError
from starlette.websockets import WebSocket
import logging
from uuid import UUID # Import UUID

logger = logging.getLogger("phantomnet_gateway.websocket_manager")

DEFAULT_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001") # Placeholder for now

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._consumer_task = None
        self._kafka_consumer = None
        self.should_run_consumer = asyncio.Event() # To control consumer loop

        self.KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
        self.SOURCE_TOPIC = 'alerts' # Listen to the alerts topic for real-time updates

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected: {websocket.client.host}")
        # Ensure consumer is running if a client connects
        if not self.should_run_consumer.is_set():
            self.should_run_consumer.set()

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected: {websocket.client.host}")
        # Optionally stop consumer if no clients are left

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except (ConnectionClosedOK, ConnectionClosedError):
            logger.warning(f"Failed to send message to closed WebSocket: {websocket.client.host}")

    async def broadcast(self, message: Dict[str, Any]):
        message_str = json.dumps(message)
        logger.debug(f"Broadcasting message to {len(self.active_connections)} clients.")
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except (ConnectionClosedOK, ConnectionClosedError):
                logger.warning(f"Client {connection.client.host} disconnected during broadcast. Removing.")
                self.disconnect(connection) # Remove disconnected client

    async def _consume_and_broadcast_kafka_messages(self):
        """Consumes messages from Kafka and broadcasts them to WebSocket clients."""
        logger.info(f"Starting Kafka consumer for topic: {self.SOURCE_TOPIC}")
        await self.should_run_consumer.wait() # Wait until at least one client connects

        try:
            self._kafka_consumer = KafkaConsumer(
                self.SOURCE_TOPIC,
                bootstrap_servers=self.KAFKA_BOOTSTRAP_SERVERS,
                auto_offset_reset='latest', # Only get new messages
                enable_auto_commit=True,
                group_id='websocket-broadcaster-group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
        except Exception as e:
            logger.error(f"Failed to connect Kafka consumer for WebSocket: {e}", exc_info=True)
            return

        logger.info("Kafka consumer connected. Waiting for messages...")
        for message in self._kafka_consumer:
            if not self.should_run_consumer.is_set(): # Check if we should still run
                break
            
            # Convert Kafka message value (dict) to JSON string and broadcast
            event_data = message.value
            logger.debug(f"Received Kafka message for broadcast: {event_data.get('alert_id')}")
            await self.broadcast(event_data)
        
        logger.info("Kafka consumer loop finished.")
        if self._kafka_consumer:
            self._kafka_consumer.close()
            self._kafka_consumer = None

    async def start_consumer(self):
        """Starts the Kafka consumer in a background task."""
        if self._consumer_task is None or self._consumer_task.done():
            self.should_run_consumer.clear() # Initially, consumer is paused
            self._consumer_task = asyncio.create_task(self._consume_and_broadcast_kafka_messages())
            logger.info("WebSocket Kafka consumer background task initiated.")

    async def stop_consumer(self):
        """Stops the Kafka consumer background task."""
        if self._consumer_task:
            logger.info("Stopping WebSocket Kafka consumer background task.")
            self.should_run_consumer.clear() # Signal consumer to stop
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                logger.info("WebSocket Kafka consumer task cancelled.")
            self._consumer_task = None
            if self._kafka_consumer:
                self._kafka_consumer.close()
                self._kafka_consumer = None
            logger.info("WebSocket Kafka consumer background task stopped.")

manager = ConnectionManager()