import asyncio
import json
from kafka import KafkaConsumer, KafkaProducer
import os
from .playbooks import trigger_playbook

KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
ALERTS_TOPIC = 'alerts'
GROUP_ID = 'soar-engine-group'

def soar_engine_thread():
    consumer = KafkaConsumer(
        ALERTS_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset='earliest',
        group_id=GROUP_ID,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    for message in consumer:
        alert = message.value
        trigger_playbook(alert)

if __name__ == "__main__":
    soar_engine_thread()
