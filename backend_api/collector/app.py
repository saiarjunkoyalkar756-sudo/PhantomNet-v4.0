from backend_api.shared.service_factory import create_phantom_service
from backend_api.core.response import success_response, error_response
from ..database import get_db, AttackLog
from sqlalchemy.orm import Session
from loguru import logger
import pika
import json
import os
import datetime
from fastapi import FastAPI, Request, HTTPException, Depends

rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")

app = create_phantom_service(
    name="Log Collector Service",
    description="Ingests raw attack logs and relays them to RabbitMQ.",
    version="1.0.0"
)

@app.post("/logs/ingest")
async def ingest_log_entry(request: Request, db: Session = Depends(get_db)):
    try:
        log_data = await request.json()

        # Create a new AttackLog entry in the database
        new_log = AttackLog(
            ip=log_data.get("ip"),
            port=log_data.get("port"),
            data=log_data.get("data"),
            timestamp=datetime.datetime.now(),
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)

        # Prepare message for RabbitMQ
        message_to_publish = {
            "id": new_log.id,
            "ip": new_log.ip,
            "port": new_log.port,
            "data": new_log.data,
            "timestamp": new_log.timestamp.isoformat(),
        }

        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbitmq_host)
            )
            channel = connection.channel()
            channel.queue_declare(queue="attack_logs")
            channel.basic_publish(
                exchange="", routing_key="attack_logs", body=json.dumps(message_to_publish)
            )
            connection.close()
            logger.info(f"Log {new_log.id} ingested and published to RabbitMQ.")
        except Exception as mq_err:
            logger.error(f"Failed to publish to RabbitMQ: {mq_err}")
            # We don't fail the whole request if only MQ failed, but we logged it.
            # In a stricter system, we might rollback DB or return partial success.

        return success_response(
            message="Log entry ingested and published.",
            data={"log_id": new_log.id}
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Log ingestion failed: {e}")
        return error_response(code="INGESTION_FAILED", message=str(e), status_code=500)
