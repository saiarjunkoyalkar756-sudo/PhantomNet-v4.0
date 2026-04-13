# backend_api/graph_intelligence_service/consumer.py

import pika
import time
import logging
import json
from .database import get_db_connection

logger = logging.getLogger(__name__)

def connect_to_rabbitmq(retries=5, delay=5):
    # ... (same as in event_stream_processor)
    pass

def process_event(event: dict):
    """
    Processes a single event and creates graph objects.
    """
    db = get_db_connection()
    event_type = event.get("event_type")

    if event_type == "PROCESS_CREATE":
        # Create process node and parent process node if it exists
        process_name = event.get("details", {}).get("name")
        pid = event.get("details", {}).get("pid")
        parent_pid = event.get("details", {}).get("parent_pid")

        if process_name and pid:
            db.query(
                "MERGE (p:Process {pid: $pid}) SET p.name = $name",
                parameters={"pid": pid, "name": process_name}
            )
            if parent_pid:
                db.query(
                    "MERGE (parent:Process {pid: $parent_pid}) "
                    "MERGE (child:Process {pid: $child_pid}) "
                    "MERGE (parent)-[:SPAWNED]->(child)",
                    parameters={"parent_pid": parent_pid, "child_pid": pid}
                )

    elif event_type == "FILE_OPEN":
        # Create file node and relationship to process
        filename = event.get("details", {}).get("filename")
        pid = event.get("pid")

        if filename and pid:
            db.query(
                "MERGE (f:File {name: $filename})",
                parameters={"filename": filename}
            )
            db.query(
                "MERGE (p:Process {pid: $pid}) "
                "MERGE (f:File {name: $filename}) "
                "MERGE (p)-[:OPENED]->(f)",
                parameters={"pid": pid, "filename": filename}
            )

    # Add more event types here...

def callback(ch, method, properties, body):
    try:
        event = json.loads(body)
        process_event(event)
    except json.JSONDecodeError:
        logger.error(f"Failed to decode message body as JSON: {body}")
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
    finally:
        ch.basic_ack(method.delivery_tag)

def start_consumer():
    # ... (same as in event_stream_processor, but consuming from 'normalized_events')
    pass
