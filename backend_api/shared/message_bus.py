import redis
import json
from loguru import logger
from typing import Optional, Dict, Any
from unittest.mock import MagicMock

class MessageBus:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis_client.ping()
            logger.info(f"Successfully connected to Redis at {host}:{port}")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Could not connect to Redis at {host}:{port}. Using mock Redis client. Error: {e}")
            self.redis_client = MagicMock()

    def publish(
        self,
        channel: str,
        message: Dict[str, Any],
        cluster_id: Optional[str] = None,
        jwt_token: Optional[str] = None,
    ):
        if not self.redis_client:
            logger.error("Cannot publish message: Redis client is not connected.")
            return

        try:
            namespaced_channel = f"{cluster_id}:{channel}" if cluster_id else channel
            full_message = {"data": message}
            if jwt_token:
                full_message["jwt"] = jwt_token
            
            self.redis_client.publish(namespaced_channel, json.dumps(full_message))
            logger.info(
                f"Published message to channel '{namespaced_channel}': {full_message}"
            )
        except Exception as e:
            logger.error(f"Error publishing message to channel '{namespaced_channel}': {e}")

    def subscribe(self, channel: str, cluster_id: Optional[str] = None):
        if not self.redis_client:
            logger.error("Cannot subscribe to channel: Redis client is not connected.")
            return None
            
        pubsub = self.redis_client.pubsub()
        namespaced_channel = f"{cluster_id}:{channel}" if cluster_id else channel
        pubsub.subscribe(namespaced_channel)
        logger.info(f"Subscribed to channel '{namespaced_channel}'")
        return pubsub

# For singleton-like access, you can instantiate it here
# This is a simple approach; for complex apps, consider dependency injection
message_bus = MessageBus()
