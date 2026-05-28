# backend_api/shared/kafka_client.py
import os
import json
import time
import asyncio
from typing import Callable, Any, Dict
from loguru import logger

from backend_api.core_config import SAFE_MODE

if not SAFE_MODE:
    from kafka import KafkaConsumer, KafkaProducer
    from kafka.errors import NoBrokersAvailable, KafkaError
else:
    # Dummy classes for SAFE_MODE to prevent ModuleNotFoundError
    class KafkaConsumer:
        def __init__(self, *args, **kwargs):
            logger.warning("SAFE_MODE: KafkaConsumer is a dummy object.")
        def poll(self, *args, **kwargs):
            return None
        def close(self):
            pass
        def commit(self, *args, **kwargs):
            pass
        def __iter__(self):
            return iter([])

    class KafkaProducer:
        def __init__(self, *args, **kwargs):
            logger.warning("SAFE_MODE: KafkaProducer is a dummy object.")
        def send(self, *args, **kwargs):
            pass
        def flush(self):
            pass
        def close(self):
            pass

class ResilientKafkaProducer:
    """
    Standardized Kafka Producer with automatic reconnect, exponential backoff,
    and fallback mock capability under testing/safe mode.
    """
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self._connect()

    def _connect(self):
        if SAFE_MODE:
            return
        
        attempt = 1
        backoff = 0.5
        while not self.producer:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                logger.info("ResilientKafkaProducer: Connected to Kafka brokers successfully.")
            except Exception as e:
                logger.error(f"ResilientKafkaProducer: Connection attempt {attempt} failed: {e}. Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
                attempt += 1

    def send(self, topic: str, value: Any):
        if SAFE_MODE:
            logger.debug(f"SAFE_MODE: Mock publishing to {topic}: {value}")
            return
            
        if not self.producer:
            self._connect()
            
        try:
            self.producer.send(topic, value)
            logger.debug(f"Published message to {topic}")
        except Exception as e:
            logger.error(f"Failed to send message to {topic}: {e}. Retrying connection...")
            self.producer = None
            # Retry once after reconnecting
            self._connect()
            if self.producer:
                try:
                    self.producer.send(topic, value)
                except Exception as retry_err:
                    logger.error(f"Retry sending message to {topic} failed: {retry_err}")

class ResilientKafkaConsumer:
    """
    Standardized Kafka Consumer with automatic reconnect, exponential backoff,
    and built-in 3-strike DLQ (Dead Letter Queue) routing capability.
    """
    def __init__(self, topic: str, bootstrap_servers: str, group_id: str, dlq_topic: str = None):
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.dlq_topic = dlq_topic or f"{topic}.dlq"
        self.consumer = None
        self.producer_for_dlq = None
        self._connect()

    def _connect(self):
        if SAFE_MODE:
            return
            
        attempt = 1
        backoff = 0.5
        while not self.consumer:
            try:
                self.consumer = KafkaConsumer(
                    self.topic,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=self.group_id,
                    auto_offset_reset='earliest',
                    enable_auto_commit=False, # Disable auto commit to support custom DLQ commit control
                    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
                )
                self.producer_for_dlq = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                logger.info(f"ResilientKafkaConsumer: Connected to topic '{self.topic}' successfully.")
            except Exception as e:
                logger.error(f"ResilientKafkaConsumer: Connection attempt {attempt} failed: {e}. Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff = min(backoff * 2, 30)
                attempt += 1

    def listen(self, process_fn: Callable[[Any], None]):
        """
        Listens to Kafka topic and processes messages using process_fn.
        Implements 3-strike retry with exponential backoff, routing persistent failures to a DLQ.
        """
        if SAFE_MODE:
            logger.warning("SAFE_MODE is ON. ResilientKafkaConsumer listen is disabled.")
            return

        logger.info(f"ResilientKafkaConsumer: Starting consumer loop for topic '{self.topic}'...")
        while True:
            if not self.consumer:
                self._connect()
                
            try:
                for message in self.consumer:
                    raw_value = message.value
                    success = False
                    backoff = 0.5
                    
                    # 3-strike retry loop
                    for attempt in range(1, 4):
                        try:
                            # Handle coroutine vs standard function
                            if asyncio.iscoroutinefunction(process_fn):
                                try:
                                    loop = asyncio.get_running_loop()
                                    future = asyncio.run_coroutine_threadsafe(process_fn(raw_value), loop)
                                    future.result()
                                except RuntimeError:
                                    asyncio.run(process_fn(raw_value))
                            else:
                                process_fn(raw_value)
                            
                            success = True
                            break
                        except Exception as err:
                            logger.warning(f"Error processing message (Attempt {attempt}/3): {err}. Retrying in {backoff}s...")
                            time.sleep(backoff)
                            backoff *= 2
                            
                    if success:
                        self.consumer.commit()
                        logger.debug("Successfully processed and committed message.")
                    else:
                        # Route message to DLQ
                        logger.error(f"Message failed processing 3 times. Routing to DLQ topic '{self.dlq_topic}'...")
                        dlq_payload = {
                            "original_topic": self.topic,
                            "failed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "error": "Failed after 3 attempts.",
                            "message_value": raw_value
                        }
                        try:
                            self.producer_for_dlq.send(self.dlq_topic, dlq_payload)
                            self.producer_for_dlq.flush()
                            self.consumer.commit()
                            logger.info("Message routed to DLQ successfully and offset committed.")
                        except Exception as dlq_err:
                            logger.critical(f"Failed to route message to DLQ: {dlq_err}. Message may be processed again on restart.")
            except Exception as e:
                logger.error(f"Error in consumer loop: {e}. Reconnecting in 5 seconds...")
                self.consumer = None
                time.sleep(5)
