import asyncio
import logging
import json
from typing import Dict, Any, AsyncGenerator, Optional, List

import redis.asyncio as redis
from redis.asyncio.client import Redis as RedisClient
from redis.exceptions import ConnectionError as RedisConnectionError # Specific Redis connection error

from phantomnet_agent.bus.base import Transport
from utils.logger import get_logger # Use the structured logger

class RedisTransport(Transport):
    """
    Redis Streams/PubSub transport for events and commands.
    Events are sent to a Redis Stream, commands are received via PubSub.
    Implements graceful fallback + Dead Letter Queue if Redis is unavailable.
    """
    MAX_RETRIES: int = 3
    DLQ_LIST_KEY: str = "phantomnet:dlq"
    DLQ_TTL_SECONDS: int = 86400  # 24 hours

    def __init__(self, url: str, events_channel: str, commands_channel: str, stream_max_len: int = 10000):
        self.logger = get_logger("phantomnet_agent.bus.redis")
        self.url = url
        self.events_channel = events_channel
        self.commands_channel = commands_channel
        self.stream_max_len = stream_max_len
        self.redis: Optional[RedisClient] = None
        self.pubsub = None
        self._listener_task: Optional[asyncio.Task] = None
        self._command_queue: asyncio.Queue = asyncio.Queue()
        self._local_dlq: List[Dict[str, Any]] = []  # Local fallback when Redis itself is down
        self.connected: bool = False
        self.logger.info(f"RedisTransport initialized for URL: {self.url}")

    async def connect(self):
        """Establishes connection to Redis with graceful failure."""
        try:
            self.redis = redis.from_url(self.url, decode_responses=True)
            # Ping Redis to verify connection
            await self.redis.ping()
            
            self.pubsub = self.redis.pubsub()
            # We don't subscribe here directly, _listen_for_commands will do it.
            
            self.connected = True
            self.logger.info(f"Connected to Redis at {self.url}")
            # Update agent_state's bus connection status
            agent_state = get_agent_state()
            agent_state.update_component_health("bus_redis", "connected", {"url": self.url})
        except (RedisConnectionError, ConnectionRefusedError) as e:
            self.connected = False
            self.logger.warning(f"Failed to connect to Redis at {self.url}: {e}. Redis bus will operate in no-op mode.", extra={"error": str(e)})
            agent_state = get_agent_state()
            agent_state.update_component_health("bus_redis", "disconnected", {"url": self.url, "reason": "Connection failed"})
        except Exception as e:
            self.connected = False
            self.logger.error(f"Unexpected error connecting to Redis at {self.url}: {e}", exc_info=True)
            agent_state = get_agent_state()
            agent_state.update_component_health("bus_redis", "error", {"url": self.url, "reason": "Unexpected error", "details": str(e)})


    async def disconnect(self):
        """Closes the Redis connection and stops the listener task."""
        self.logger.info("Disconnecting from Redis bus.")
        self.connected = False
        if self._listener_task:
            self._listener_task.cancel()
            await asyncio.gather(self._listener_task, return_exceptions=True)
            self._listener_task = None
        if self.pubsub:
            await self.pubsub.unsubscribe(self.commands_channel)
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
        self.logger.info("Redis transport disconnected.")
        agent_state = get_agent_state()
        agent_state.update_component_health("bus_redis", "disconnected", {"url": self.url})

    async def send_event(self, event_data: Dict[str, Any]):
        """Sends an event to the Redis Stream with retry and DLQ fallback."""
        if not self.connected or not self.redis:
            self.logger.warning(
                f"Redis not connected. Event '{event_data.get('event_type', 'N/A')}' pushed to local DLQ.",
                extra={"event_data": event_data}
            )
            self._local_dlq.append(event_data)
            return

        last_exc: Optional[Exception] = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                await self.redis.xadd(
                    self.events_channel,
                    {"data": json.dumps(event_data)},
                    maxlen=self.stream_max_len,
                    approx=True
                )
                self.logger.debug(
                    f"Event '{event_data.get('event_type', 'N/A')}' published to "
                    f"Redis Stream '{self.events_channel}'.",
                    extra={"event_data": event_data}
                )
                return  # success
            except Exception as e:
                last_exc = e
                self.logger.warning(
                    f"Redis send attempt {attempt}/{self.MAX_RETRIES} failed: {e}"
                )
                await asyncio.sleep(0.5 * attempt)

        # All retries exhausted — push to DLQ Redis list (best-effort) + local fallback
        dlq_record = {
            "original_event": event_data,
            "failure_reason": str(last_exc),
            "retry_count": self.MAX_RETRIES,
            "dlq_timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        }
        try:
            await self.redis.lpush(self.DLQ_LIST_KEY, json.dumps(dlq_record))
            await self.redis.expire(self.DLQ_LIST_KEY, self.DLQ_TTL_SECONDS)
            self.logger.error(
                f"Event moved to Redis DLQ list '{self.DLQ_LIST_KEY}' after "
                f"{self.MAX_RETRIES} retries."
            )
        except Exception:
            self._local_dlq.append(dlq_record)
            self.logger.error(
                f"Redis DLQ write also failed. Event stored in local memory DLQ. "
                f"Local DLQ size: {len(self._local_dlq)}"
            )
        agent_state = get_agent_state()
        agent_state.update_component_health(
            "bus_redis", "degraded",
            {"reason": "Event moved to DLQ", "details": str(last_exc)}
        )

    async def flush_dlq(self) -> int:
        """
        Replays all events from the Redis DLQ list + local fallback DLQ.
        Should be called after successful reconnect.
        Returns the total number of successfully replayed events.
        """
        flushed = 0

        # Flush Redis DLQ list
        if self.connected and self.redis:
            try:
                while True:
                    raw = await self.redis.rpop(self.DLQ_LIST_KEY)
                    if raw is None:
                        break
                    record = json.loads(raw)
                    event = record.get("original_event", record)
                    try:
                        await self.redis.xadd(
                            self.events_channel,
                            {"data": json.dumps(event)},
                            maxlen=self.stream_max_len,
                            approx=True
                        )
                        flushed += 1
                    except Exception as e:
                        self.logger.error(f"DLQ flush failed for event: {e}")
                        await self.redis.lpush(self.DLQ_LIST_KEY, raw)  # Put it back
            except Exception as e:
                self.logger.error(f"Error reading Redis DLQ list: {e}")

        # Flush local memory DLQ
        remaining: List[Dict[str, Any]] = []
        for record in list(self._local_dlq):
            event = record.get("original_event", record)
            try:
                await self.redis.xadd(
                    self.events_channel,
                    {"data": json.dumps(event)},
                    maxlen=self.stream_max_len,
                    approx=True
                )
                flushed += 1
            except Exception:
                remaining.append(record)
        self._local_dlq = remaining

        self.logger.info(f"Redis DLQ flush complete: {flushed} events replayed.")
        return flushed

    async def _listen_for_commands(self):
        """Internal task to listen for commands via Redis PubSub and put them into a queue."""
        if not self.pubsub: # Ensure pubsub is initialized if called directly without connect()
            await self.connect() # Attempt to connect again if pubsub is None

        if not self.connected or not self.pubsub:
            self.logger.error("PubSub not initialized or Redis not connected. Cannot listen for commands.")
            return

        try:
            await self.pubsub.subscribe(self.commands_channel)
            self.logger.info(f"Subscribed to Redis commands channel '{self.commands_channel}'.")
            while self.connected and not self._listener_task.cancelled(): # Continue while connected and task not cancelled
                message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0) # Short timeout
                if message and message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        await self._command_queue.put(data) # Put command data into queue
                        self.logger.debug(f"Received command from Redis PubSub: {data.get('action_type')}", extra={"command": data})
                    except json.JSONDecodeError:
                        self.logger.warning(f"Received malformed JSON command from Redis PubSub on channel '{self.commands_channel}'.")
                await asyncio.sleep(0.01) # Yield control
        except asyncio.CancelledError:
            self.logger.info("Redis command listener task cancelled.")
        except Exception as e:
            self.logger.error(f"Error in Redis command listener task: {e}", exc_info=True)
            agent_state = get_agent_state()
            agent_state.update_component_health("bus_redis", "degraded", {"reason": "Command listener error", "details": str(e)})
        finally:
            if self.pubsub:
                await self.pubsub.unsubscribe(self.commands_channel)

    async def receive_commands(self, commands_topic: str) -> AsyncGenerator[Any, None]:
        """
        Asynchronously yields commands received from the Redis commands channel.
        Starts the internal listener task if it's not already running.
        """
        if not self.connected:
            self.logger.warning("Redis not connected. Cannot receive commands.", extra={"topic": commands_topic})
            return # Yield nothing

        if self._listener_task is None:
            # Ensure the topic matches the configured commands_channel for Redis PubSub
            if commands_topic != self.commands_channel:
                self.logger.warning(f"RedisTransport receive_commands only listens on '{self.commands_channel}'. Requested topic '{commands_topic}' ignored.")
            
            self._listener_task = asyncio.create_task(self._listen_for_commands())
            self.logger.info(f"Started Redis command listener for channel '{self.commands_channel}'.")

        while self.connected:
            try:
                command = await self._command_queue.get()
                yield command
                self._command_queue.task_done()
            except asyncio.CancelledError:
                self.logger.info("Redis receive_commands generator cancelled.")
                break
            except Exception as e:
                self.logger.error(f"Error yielding command from Redis queue: {e}", exc_info=True)
                await asyncio.sleep(1) # Prevent busy loop on error and allow retry
        self.logger.info("Redis receive_commands generator stopped.")