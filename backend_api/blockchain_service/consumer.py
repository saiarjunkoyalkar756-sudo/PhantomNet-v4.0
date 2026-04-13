import pika
import json
import os
import threading
import time
import datetime
from datetime import timezone

from blockchain_layer.blockchain import Blockchain
from ..database import (
    get_db,
    Block,
    AttackLog,
    Alert,
    NormalizedEvent,
    ForensicRecord,
)

rabbitmq_host = os.getenv(
    "RABBITMQ_HOST", "rabbitmq"
)  # Use 'rabbitmq' for docker-compose


def create_transaction_for_data(
    db_session, blockchain_instance, data_type, record_id, record_obj
):
    """
    Creates a transaction and mines a block for a given data record.
    """
    try:
        sender_id = record_obj.get("source", "system")  # Example sender
        recipient_id = record_obj.get(
            "target_ip", record_obj.get("ip", "unknown")
        )  # Example recipient

        # Ensure unique IDs for transaction and data_type
        transaction_data = {
            "sender": sender_id,
            "recipient": recipient_id,
            "amount": 1,  # Placeholder
            "data": json.dumps(record_obj),
            "data_type": data_type,
        }

        # Dynamically add foreign key based on data_type
        fk_id = None
        if data_type == "attack_log":
            transaction_data["attack_type"] = record_obj.get("attack_type")
            transaction_data["confidence_score"] = record_obj.get("confidence_score")
            fk_id = (
                db_session.query(AttackLog.id)
                .filter(AttackLog.id == record_id)
                .scalar()
            )
            transaction_data["attack_log_id"] = fk_id
        elif data_type == "alert":
            fk_id = (
                db_session.query(Alert.id).filter(Alert.alert_id == record_id).scalar()
            )
            transaction_data["alert_id"] = fk_id
        elif data_type == "normalized_event":
            fk_id = (
                db_session.query(NormalizedEvent.id)
                .filter(NormalizedEvent.event_id == record_id)
                .scalar()
            )
            transaction_data["normalized_event_id"] = fk_id
        elif data_type == "forensic_record":
            fk_id = (
                db_session.query(ForensicRecord.id)
                .filter(ForensicRecord.record_id == record_id)
                .scalar()
            )
            transaction_data["forensic_record_id"] = fk_id

        if fk_id is None:
            logger.warning(
                f"Record with ID {record_id} not found for {data_type}. Transaction not created."
            )
            return

        blockchain_instance.new_transaction(**transaction_data)

        # Mine a new block
        last_block_obj = blockchain_instance.last_block
        last_proof = last_block_obj.proof if last_block_obj else 0
        proof = blockchain_instance.proof_of_work(last_proof)
        previous_hash = (
            blockchain_instance.hash(last_block_obj.to_dict())
            if last_block_obj
            else "1"
        )

        new_block_obj = blockchain_instance.new_block(proof, previous_hash)
        db_session.add(new_block_obj)
        db_session.commit()
        db_session.refresh(new_block_obj)
        logger.info(
            f" [Blockchain Service] New block mined for {data_type} (ID: {record_id}): {new_block_obj.index}"
        )

    except Exception as e:
        db_session.rollback()
        logger.error(
            f" [Blockchain Service] Error creating transaction for {data_type} (ID: {record_id}): {e}",
            exc_info=True,
        )
    finally:
        db_session.close()


def callback_router(ch, method, properties, body):
    message_data = json.loads(body.decode())
    queue_name = method.routing_key  # Get the queue name

    logger.info(
        f" [Blockchain Service] Received message from {queue_name}: {message_data}"
    )

    db = next(get_db())
    blockchain = Blockchain(db)

    try:
        record_id = None
        record_obj = message_data  # Assume message_data is the full record

        if queue_name == "attack_logs":
            record_id = message_data.get("id")
            if record_id:
                attack_log_entry = (
                    db.query(AttackLog).filter(AttackLog.id == record_id).first()
                )
                if attack_log_entry:
                    create_transaction_for_data(
                        db,
                        blockchain,
                        "attack_log",
                        record_id,
                        attack_log_entry.to_dict(),
                    )
                else:
                    logger.warning(
                        f" [Blockchain Service] AttackLog with ID {record_id} not found. Cannot add to blockchain."
                    )
            else:
                logger.warning(
                    f" [Blockchain Service] Message from attack_logs missing 'id'."
                )

        elif queue_name == "alerts":
            record_id = message_data.get("alert_id")
            if record_id:
                alert_entry = (
                    db.query(Alert).filter(Alert.alert_id == record_id).first()
                )
                if alert_entry:
                    create_transaction_for_data(
                        db, blockchain, "alert", record_id, alert_entry.to_dict()
                    )
                else:
                    logger.warning(
                        f" [Blockchain Service] Alert with ID {record_id} not found. Cannot add to blockchain."
                    )
            else:
                logger.warning(
                    f" [Blockchain Service] Message from alerts missing 'alert_id'."
                )

        elif queue_name == "normalized_events":
            record_id = message_data.get("event_id")
            if record_id:
                event_entry = (
                    db.query(NormalizedEvent)
                    .filter(NormalizedEvent.event_id == record_id)
                    .first()
                )
                if event_entry:
                    create_transaction_for_data(
                        db,
                        blockchain,
                        "normalized_event",
                        record_id,
                        event_entry.to_dict(),
                    )
                else:
                    logger.warning(
                        f" [Blockchain Service] NormalizedEvent with ID {record_id} not found. Cannot add to blockchain."
                    )
            else:
                logger.warning(
                    f" [Blockchain Service] Message from normalized_events missing 'event_id'."
                )

        elif queue_name == "forensic_records":  # Assuming a queue for forensic data
            record_id = message_data.get("record_id")
            if record_id:
                forensic_entry = (
                    db.query(ForensicRecord)
                    .filter(ForensicRecord.record_id == record_id)
                    .first()
                )
                if forensic_entry:
                    create_transaction_for_data(
                        db,
                        blockchain,
                        "forensic_record",
                        record_id,
                        forensic_entry.to_dict(),
                    )
                else:
                    logger.warning(
                        f" [Blockchain Service] ForensicRecord with ID {record_id} not found. Cannot add to blockchain."
                    )
            else:
                logger.warning(
                    f" [Blockchain Service] Message from forensic_records missing 'record_id'."
                )

        else:
            logger.warning(
                f" [Blockchain Service] Unrecognized queue: {queue_name}. Message not processed."
            )

    except Exception as e:
        logger.error(
            f" [Blockchain Service] Error in callback_router for queue {queue_name}: {e}",
            exc_info=True,
        )
    finally:
        ch.basic_ack(
            method.delivery_tag
        )  # Acknowledge message after processing or error


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()

    # Declare all queues that this consumer will listen to
    channel.queue_declare(queue="attack_logs", durable=True)
    channel.queue_declare(queue="alerts", durable=True)
    channel.queue_declare(queue="normalized_events", durable=True)
    channel.queue_declare(queue="forensic_records", durable=True)

    # Set up consumers for each queue
    channel.basic_consume(queue="attack_logs", on_message_callback=callback_router)
    channel.basic_consume(queue="alerts", on_message_callback=callback_router)
    channel.basic_consume(
        queue="normalized_events", on_message_callback=callback_router
    )
    channel.basic_consume(queue="forensic_records", on_message_callback=callback_router)

    logger.info(
        " [Blockchain Service] Waiting for messages from multiple queues. To exit press CTRL+C"
    )
    channel.start_consuming()


if __name__ == "__main__":
    main()
