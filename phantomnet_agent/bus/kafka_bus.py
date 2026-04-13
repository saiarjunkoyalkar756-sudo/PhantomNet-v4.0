import asyncio
import logging
import json
from typing import Dict, Any, AsyncGenerator, Optional

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError, NoBrokersAvailable

from phantomnet_agent.bus.base import Transport
from utils.logger import get_logger # Use the structured logger
from core.state import get_agent_state # For updating agent state

class KafkaTransport(Transport):
    """
    Kafka transport for events and commands.
    Events are sent to a Kafka topic, commands are received from another Kafka topic.
    Implements graceful fallback if Kafka is unavailable.
    """
    def __init__(self, bootstrap_servers: str, events_topic: str, commands_topic: str, consumer_group_id: str):
        self.logger = get_logger("phantomnet_agent.bus.kafka")
        self.bootstrap_servers = bootstrap_servers
        self.events_topic = events_topic
        self.commands_topic = commands_topic
        self.consumer_group_id = consumer_group_id
        self.producer: Optional[AIOKafkaProducer] = None
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._listener_task: Optional[asyncio.Task] = None
        self._command_queue: asyncio.Queue = asyncio.Queue() # Queue to hold incoming commands
        self.connected: bool = False
        self.logger.info(f"KafkaTransport initialized for bootstrap_servers: {self.bootstrap_servers}")

    async def connect(self):
        """Establishes connection to Kafka producer and consumer with graceful failure."""
        try:
            self.producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)
            self.consumer = AIOKafkaConsumer(
                self.commands_topic, # Consumer listens on the commands topic
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.consumer_group_id,
                auto_offset_reset='latest', # Start consuming from the latest message
                enable_auto_commit=True # Auto commit offsets
            )
            await self.producer.start()
            await self.consumer.start()
            self.connected = True
            self.logger.info(f"Connected to Kafka at {self.bootstrap_servers}")
            agent_state = get_agent_state()
            agent_state.update_component_health("bus_kafka", "connected", {"bootstrap_servers": self.bootstrap_servers})
        except (KafkaError, NoBrokersAvailable, ConnectionRefusedError) as e:
            self.connected = False
            self.logger.warning(f"Failed to connect to Kafka at {self.bootstrap_servers}: {e}. Kafka bus will operate in no-op mode.", extra={"error": str(e)})
            agent_state = get_agent_state()
            agent_state.update_component_health("bus_kafka", "disconnected", {"bootstrap_servers": self.bootstrap_servers, "reason": "Connection failed"})
        except Exception as e:
            self.connected = False
            self.logger.error(f"Unexpected error connecting to Kafka at {self.bootstrap_servers}: {e}", exc_info=True)
            agent_state = get_agent_state()
            agent_state.update_component_health("bus_kafka", "error", {"bootstrap_servers": self.bootstrap_servers, "reason": "Unexpected error", "details": str(e)})

    async def disconnect(self):
        """Closes the Kafka producer and consumer and stops the listener task."""
        self.logger.info("Disconnecting from Kafka bus.")
        self.connected = False
        if self._listener_task:
            self._listener_task.cancel()
            await asyncio.gather(self._listener_task, return_exceptions=True)
            self._listener_task = None
        if self.producer:
            await self.producer.stop()
        if self.consumer:
            await self.consumer.stop()
        self.logger.info("Kafka transport disconnected.")
        agent_state = get_agent_state()
        agent_state.update_component_health("bus_kafka", "disconnected", {"bootstrap_servers": self.bootstrap_servers})

    async def send_event(self, event_data: Dict[str, Any]):
        """Sends an event to the configured Kafka events topic."""
        if not self.connected or not self.producer:
            self.logger.warning(f"Kafka not connected. Event '{event_data.get('event_type', 'N/A')}' will not be sent.", extra={"event_data": event_data})
            return

        try:
            await self.producer.send_and_wait(self.events_topic, json.dumps(event_data).encode('utf-8'))
            self.logger.debug(f"Event '{event_data.get('event_type', 'N/A')}' published to Kafka topic '{self.events_topic}'.", extra={"event_data": event_data})
        except Exception as e:
            self.logger.error(f"Error publishing event to Kafka topic '{self.events_topic}': {e}", exc_info=True, extra={"event_data": event_data})
            agent_state = get_agent_state()
            agent_state.update_component_health("bus_kafka", "degraded", {"reason": "Error sending event", "details": str(e)})

    async def _listen_for_commands(self):
        """Internal task to listen for commands from Kafka topic and put them into a queue."""
        if not self.connected or not self.consumer:
            self.logger.error("Kafka consumer not initialized or connected. Cannot listen for commands.")
            return

        try:
            async for msg in self.consumer:
                if self._listener_task.cancelled(): # Check for cancellation
                    break
                try:
                    data = json.loads(msg.value.decode('utf-8'))
                    await self._command_queue.put(data) # Put command data into queue
                    self.logger.debug(f"Received command from Kafka: {data.get('action_type')}", extra={"command": data})
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Received malformed JSON command from Kafka: {e}", extra={"raw_message": msg.value.decode('utf-8', errors='ignore')})
                except Exception as e:
                    self.logger.error(f"Error processing message from Kafka: {e}", exc_info=True)
        except asyncio.CancelledError:
            self.logger.info("Kafka command listener task cancelled.")
        except KafkaError as e:
            self.logger.error(f"Kafka error during command consumption: {e}", exc_info=True)
            agent_state = get_agent_state()
            agent_state.update_component_health("bus_kafka", "degraded", {"reason": "Command consumption error", "details": str(e)})
        except Exception as e:
            self.logger.error(f"An unexpected error occurred in Kafka command listener: {e}", exc_info=True)
            agent_state = get_agent_state()
            agent_state.update_component_health("bus_kafka", "error", {"reason": "Unexpected error in listener", "details": str(e)})

    async def receive_commands(self, commands_topic: str) -> AsyncGenerator[Any, None]:
        """
        Asynchronously yields commands received from the Kafka commands topic.
        Starts the internal listener task if it's not already running.
        """
        if not self.connected:
            self.logger.warning("Kafka not connected. Cannot receive commands.", extra={"topic": commands_topic})
            return # Yield nothing

        if self._listener_task is None:
            # Ensure the topic matches the configured commands_topic for this consumer
            if commands_topic != self.commands_topic:
                self.logger.warning(f"KafkaTransport receive_commands only listens on '{self.commands_topic}'. Requested topic '{commands_topic}' ignored.")
            
            self._listener_task = asyncio.create_task(self._listen_for_commands())
            self.logger.info(f"Started Kafka command listener for topic '{self.commands_topic}'.")

        while self.connected:
            try:
                command = await self._command_queue.get()
                yield command
                self._command_queue.task_done()
            except asyncio.CancelledError:
                self.logger.info("Kafka receive_commands generator cancelled.")
                break
            except Exception as e:
                self.logger.error(f"Error yielding command from Kafka queue: {e}", exc_info=True)
                await asyncio.sleep(1) # Prevent busy loop on error and allow retry
        self.logger.info("Kafka receive_commands generator stopped.")