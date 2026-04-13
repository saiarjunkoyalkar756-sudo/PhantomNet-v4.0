# backend_api/event_stream_processor/database.py

import psycopg2
import logging
import json
from psycopg2.extras import Json

logger = logging.getLogger(__name__)

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname="phantomnet",
            user="phantomnet",
            password="password",
            host="postgres"
        )
        logger.info("Successfully connected to the database.")
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Could not connect to the database: {e}")
        return None

def create_events_table():
    """Creates the events table if it doesn't exist."""
    conn = get_db_connection()
    if conn is None:
        return
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    source TEXT,
                    event_type TEXT,
                    raw_event JSONB,
                    source_ip INET,
                    destination_ip INET,
                    protocol TEXT,
                    details JSONB
                );
            """)
            conn.commit()
            logger.info("Events table created or already exists.")
    except psycopg2.Error as e:
        logger.error(f"Error creating events table: {e}")
    finally:
        conn.close()

def insert_event(event: dict):
    """Inserts a normalized event into the database."""
    conn = get_db_connection()
    if conn is None:
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO events (
                    timestamp, source, event_type, raw_event,
                    source_ip, destination_ip, protocol, details
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s
                );
            """, (
                event.get("timestamp"),
                event.get("source"),
                event.get("event_type"),
                Json(event.get("raw_event")),
                event.get("source_ip"),
                event.get("destination_ip"),
                event.get("protocol"),
                Json(event.get("details"))
            ))
            conn.commit()
    except psycopg2.Error as e:
        logger.error(f"Error inserting event: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_events_table()
