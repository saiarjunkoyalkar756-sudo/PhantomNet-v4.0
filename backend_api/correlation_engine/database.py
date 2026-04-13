# backend_api/correlation_engine/database.py

import psycopg2
import logging
import json
import os

logger = logging.getLogger(__name__)

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "phantomnet_db"),
            user=os.getenv("DB_USER", "phantomnet"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "postgres")
        )
        logger.info("Successfully connected to the correlation engine database.")
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Could not connect to the correlation engine database: {e}")
        return None

def create_rules_table():
    """Creates the correlation_rules table if it doesn't exist."""
    conn = get_db_connection()
    if conn is None:
        return
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS correlation_rules (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    logic JSONB, -- Storing rule logic as JSON
                    action TEXT,
                    severity TEXT,
                    enabled BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            conn.commit()
            logger.info("Correlation rules table created or already exists.")
    except psycopg2.Error as e:
        logger.error(f"Error creating correlation rules table: {e}")
    finally:
        conn.close()

def get_all_rules():
    """Retrieves all enabled correlation rules from the database."""
    conn = get_db_connection()
    if conn is None:
        return []

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM correlation_rules WHERE enabled = TRUE;")
            rules = cur.fetchall()
            return rules
    except psycopg2.Error as e:
        logger.error(f"Error retrieving correlation rules: {e}")
        return []
    finally:
        conn.close()

def upsert_rule(rule: dict):
    """Inserts or updates a correlation rule in the database."""
    conn = get_db_connection()
    if conn is None:
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO correlation_rules (
                    name, description, logic, action, severity, enabled
                ) VALUES (
                    %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (name) DO UPDATE SET
                    description = EXCLUDED.description,
                    logic = EXCLUDED.logic,
                    action = EXCLUDED.action,
                    severity = EXCLUDED.severity,
                    enabled = EXCLUDED.enabled,
                    updated_at = NOW();
            """, (
                rule.get("name"),
                rule.get("description"),
                json.dumps(rule.get("logic", {})),
                rule.get("action"),
                rule.get("severity"),
                rule.get("enabled", True)
            ))
            conn.commit()
            logger.info(f"Correlation rule '{rule.get('name')}' upserted.")
    except psycopg2.Error as e:
        logger.error(f"Error upserting rule '{rule.get('name')}': {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_rules_table()
