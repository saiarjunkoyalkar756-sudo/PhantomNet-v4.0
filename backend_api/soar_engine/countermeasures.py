import json
from kafka import KafkaProducer
import os

KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
AGENT_COMMANDS_TOPIC = 'agent-commands'

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def block_ip(ip_address: str):
    command = {
        "command_type": "block_network_address",
        "payload": {
            "address": ip_address
        }
    }
    producer.send(AGENT_COMMANDS_TOPIC, command)
