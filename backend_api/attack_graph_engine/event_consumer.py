# backend_api/attack_graph_engine/event_consumer.py
import asyncio
import json
import logging
import os
from aiokafka import AIOKafkaConsumer

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "redpanda:29092")
SOURCE_TOPIC = "normalized-events"
GROUP_ID = "attack-graph-engine-group"

async def consume_events(graph_builder):
    """
    Consumes events from Kafka and passes them to the GraphBuilder.
    """
    consumer = AIOKafkaConsumer(
        SOURCE_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )

    await consumer.start()
    logger.info("Kafka consumer started, waiting for events...")

    try:
        async for msg in consumer:
            event_data = msg.value
            event_type = event_data.get("type")
            
            # Based on the event type, delegate to the appropriate graph-building logic
            if event_type == "packet_metadata":
                await graph_builder.add_network_connection(event_data)
            elif event_type == "process_execution":
                await graph_builder.add_process_execution(event_data)
            elif event_type == "vulnerability_scan":
                await graph_builder.add_vulnerability(event_data)
            # Add more event types as needed
            
            logger.debug(f"Processed event: {event_data}")

    finally:
        logger.info("Stopping Kafka consumer...")
        await consumer.stop()
