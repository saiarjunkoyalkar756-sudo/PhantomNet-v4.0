# backend_api/shared/audit_log.py
import asyncio

# A centralized, in-memory queue for audit records destined for the blockchain.
# In a larger-scale production system, this might be replaced by a dedicated
# and persistent message queue like RabbitMQ or a specific Kafka topic.
AUDIT_LOG_QUEUE = asyncio.Queue()
