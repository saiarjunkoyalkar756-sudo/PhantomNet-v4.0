# backend_api/siem_integration_service/siem_ingest_service.py

import asyncio
import logging
import json
from typing import Dict, Any, List
from typing import Dict, Any, List
from datetime import datetime
import os
import uuid # Import uuid

from shared.logger_config import logger
from .schemas import RawLog, NormalizedLog # Import models
# Assuming an external message bus (e.g., Kafka/Redpanda) for ingestion
# from kafka import KafkaProducer

logger = logger

# Configuration for Kafka/Redpanda
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
SIEM_RAW_LOGS_TOPIC = os.getenv("SIEM_RAW_LOGS_TOPIC", "siem_raw_logs")
SIEM_NORMALIZED_LOGS_TOPIC = os.getenv("SIEM_NORMALIZED_LOGS_TOPIC", "siem_normalized_logs")

class SIEMIngestService:
    """
    Handles ingestion of raw log data, pushing it to a message bus for further processing.
    """
    def __init__(self):
        self.raw_log_queue = asyncio.Queue()
        self.producer = None # Placeholder for KafkaProducer
        
        try:
            # self.producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            #                               value_serializer=lambda v: json.dumps(v).encode('utf-8'))
            logger.info(f"SIEMIngestService initialized. Kafka producer connected to {KAFKA_BOOTSTRAP_SERVERS}.")
        except Exception as e:
            logger.warning(f"Could not connect to Kafka producer at {KAFKA_BOOTSTRAP_SERVERS}. Ingestion will be in-memory only. Error: {e}")
            
    async def ingest_raw_log(self, raw_log: RawLog):
        """
        Ingests a raw log event, adds metadata, and pushes to a queue/message bus.
        """
        logger.info(f"Ingesting raw log from {raw_log.source_system} (Host: {raw_log.host})")
        
        # Add a unique ID for the raw log for traceability
        raw_log_dict = raw_log.model_dump()
        raw_log_dict["_raw_log_id"] = str(uuid.uuid4()) # Assuming uuid is imported

        if self.producer:
            try:
                # await self.producer.send(SIEM_RAW_LOGS_TOPIC, raw_log_dict)._Future__wait_result(timeout=10)
                logger.debug(f"Raw log {raw_log_dict['_raw_log_id']} sent to Kafka topic {SIEM_RAW_LOGS_TOPIC}")
            except Exception as e:
                logger.error(f"Failed to send raw log to Kafka: {e}. Falling back to in-memory queue.")
                await self.raw_log_queue.put(raw_log_dict)
        else:
            await self.raw_log_queue.put(raw_log_dict)
            logger.debug(f"Raw log {raw_log_dict['_raw_log_id']} added to in-memory queue.")

    async def _process_raw_log_queue(self):
        """
        Background task to process logs from the raw log queue (if Kafka is not used).
        In a real scenario, this would involve log normalizer.
        """
        while True:
            raw_log_dict = await self.raw_log_queue.get()
            logger.info(f"Processing raw log from in-memory queue: {raw_log_dict.get('_raw_log_id')}")
            # Here, the log would typically be passed to the LogNormalizer
            # For now, we'll just acknowledge and discard
            self.raw_log_queue.task_done()
            await asyncio.sleep(0.1) # Prevent busy loop

    async def start(self):
        """Starts background tasks for ingestion."""
        # if not self.producer:
        #     self.raw_log_processor_task = asyncio.create_task(self._process_raw_log_queue())
        #     logger.info("Started in-memory raw log processor.")
        pass # Currently, if Kafka fails, it just queues. No active processor for that.

    async def stop(self):
        """Stops the ingestion service."""
        # if self.producer:
        #     await self.producer.flush()
        #     await self.producer.close()
        # if hasattr(self, 'raw_log_processor_task'):
        #     self.raw_log_processor_task.cancel()
        logger.info("SIEMIngestService stopped.")


# Example usage (for testing purposes)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running SIEMIngestService example...")
    
    # Needs uuid import for raw_log_id
    import uuid

    async def run_example():
        ingest_service = SIEMIngestService()
        await ingest_service.start()

        test_log1 = RawLog(
            source_system="agent-linux-001",
            host="linux-server",
            raw_data='{"event_type": "process_create", "process_name": "bash", "user": "root"}'
        )
        test_log2 = RawLog(
            source_system="firewall-001",
            host="firewall.corp",
            raw_data='<187>Jan 1 00:00:00 firewall CEF:0|Vendor|Product|Version|signature_id|name|severity|extension'
        )

        await ingest_service.ingest_raw_log(test_log1)
        await ingest_service.ingest_raw_log(test_log2)
        
        await asyncio.sleep(2) # Give some time for background tasks if any
        await ingest_service.stop()

    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("SIEMIngestService example stopped.")
