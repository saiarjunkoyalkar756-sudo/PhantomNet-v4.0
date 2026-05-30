import json
from kafka import KafkaProducer
import os

KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
AGENT_COMMANDS_TOPIC = 'agent-commands'

producer = None
try:
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
except Exception as e:
    from loguru import logger
    logger.warning(f"SOAR Engine: Could not initialize KafkaProducer: {e}. running in fallback mode.")

def block_ip(ip_address: str):
    command = {
        "command_type": "block_network_address",
        "payload": {
            "address": ip_address
        }
    }
    if producer:
        try:
            producer.send(AGENT_COMMANDS_TOPIC, command)
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to send agent command via Kafka: {e}")
    else:
        from loguru import logger
        logger.info(f"[Standalone Mode] block_ip would send command: {command}")
