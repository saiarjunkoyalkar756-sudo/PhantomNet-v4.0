# backend_api/case_management_service/database.py

import psycopg2
import logging
import json
import os
from datetime import datetime

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
        logger.info("Successfully connected to the case management database.")
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Could not connect to the case management database: {e}")
        return None

def create_cases_table():
    """Creates the cases table if it doesn't exist."""
    conn = get_db_connection()
    if conn is None:
        return
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'new', -- e.g., new, in_progress, resolved, closed
                    severity TEXT, -- e.g., low, medium, high, critical
                    assigned_to TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    timeline JSONB DEFAULT '[]'::jsonb,
                    notes JSONB DEFAULT '[]'::jsonb,
                    playbook_status JSONB DEFAULT '{}'::jsonb
                );
            """)
            conn.commit()
            logger.info("Cases table created or already exists.")
    except psycopg2.Error as e:
        logger.error(f"Error creating cases table: {e}")
    finally:
        conn.close()

def get_all_cases():
    """Retrieves all cases from the database."""
    conn = get_db_connection()
    if conn is None:
        return []

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM cases ORDER BY created_at DESC;")
            cases = cur.fetchall()
            return cases
    except psycopg2.Error as e:
        logger.error(f"Error retrieving cases: {e}")
        return []
    finally:
        conn.close()

def get_case_by_id(case_id: int):
    """Retrieves a single case by its ID."""
    conn = get_db_connection()
    if conn is None:
        return None
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM cases WHERE id = %s;", (case_id,))
            case = cur.fetchone()
            return case
    except psycopg2.Error as e:
        logger.error(f"Error retrieving case {case_id}: {e}")
        return None
    finally:
        conn.close()

def create_case(case: dict):
    """Creates a new case in the database."""
    conn = get_db_connection()
    if conn is None:
        return None

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO cases (
                    title, description, status, severity, assigned_to
                ) VALUES (
                    %s, %s, %s, %s, %s
                ) RETURNING id;
            """, (
                case.get("title"),
                case.get("description"),
                case.get("status", "new"),
                case.get("severity"),
                case.get("assigned_to")
            ))
            case_id = cur.fetchone()['id']
            conn.commit()
            logger.info(f"Case '{case.get('title')}' created with ID: {case_id}")
            return case_id
    except psycopg2.Error as e:
        logger.error(f"Error creating case '{case.get('title')}': {e}")
        return None
    finally:
        conn.close()

def update_case(case_id: int, updates: dict):
    """Updates an existing case in the database."""
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        set_clauses = []
        values = []
        for key, value in updates.items():
            set_clauses.append(f"{key} = %s")
            values.append(value)
        
        if not set_clauses:
            return False # No updates provided

        values.append(datetime.now()) # For updated_at
        set_clauses.append("updated_at = %s")
        values.append(case_id)

        cur = conn.cursor()
        cur.execute(f"UPDATE cases SET {', '.join(set_clauses)} WHERE id = %s;", tuple(values))
        conn.commit()
        logger.info(f"Case {case_id} updated.")
        return True
    except psycopg2.Error as e:
        logger.error(f"Error updating case {case_id}: {e}")
        return False
    finally:
        conn.close()
