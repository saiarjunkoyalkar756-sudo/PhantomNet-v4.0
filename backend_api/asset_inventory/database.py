# backend_api/asset_inventory/database.py

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
        logger.info("Successfully connected to the asset inventory database.")
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Could not connect to the asset inventory database: {e}")
        return None

def create_assets_table():
    """Creates the assets table if it doesn't exist."""
    conn = get_db_connection()
    if conn is None:
        return
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS assets (
                    id SERIAL PRIMARY KEY,
                    ip_address INET UNIQUE,
                    hostname TEXT,
                    mac_address MACADDR,
                    os TEXT,
                    asset_type TEXT, -- e.g., "endpoint", "server", "container", "cloud_workload"
                    last_seen TIMESTAMPTZ,
                    details JSONB
                );
            """)
            conn.commit()
            logger.info("Assets table created or already exists.")
    except psycopg2.Error as e:
        logger.error(f"Error creating assets table: {e}")
    finally:
        conn.close()

def upsert_asset(asset: dict):
    """Inserts or updates an asset in the database."""
    conn = get_db_connection()
    if conn is None:
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO assets (
                    ip_address, hostname, mac_address, os, asset_type, last_seen, details
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (ip_address) DO UPDATE SET
                    hostname = EXCLUDED.hostname,
                    mac_address = EXCLUDED.mac_address,
                    os = EXCLUDED.os,
                    asset_type = EXCLUDED.asset_type,
                    last_seen = EXCLUDED.last_seen,
                    details = EXCLUDED.details;
            """, (
                asset.get("ip_address"),
                asset.get("hostname"),
                asset.get("mac_address"),
                asset.get("os"),
                asset.get("asset_type"),
                asset.get("last_seen"),
                json.dumps(asset.get("details", {}))
            ))
            conn.commit()
            logger.info(f"Asset {asset.get('ip_address')} upserted.")
    except psycopg2.Error as e:
        logger.error(f"Error upserting asset {asset.get('ip_address')}: {e}")
    finally:
        conn.close()

def get_all_assets():
    """Retrieves all assets from the database."""
    conn = get_db_connection()
    if conn is None:
        return []

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM assets;")
            assets = cur.fetchall()
            return assets
    except psycopg2.Error as e:
        logger.error(f"Error retrieving assets: {e}")
        return []
    finally:
        conn.close()

if __name__ == "__main__":
    create_assets_table()
    # Example usage:
    # upsert_asset({
    #     "ip_address": "192.168.1.10",
    #     "hostname": "my-server",
    #     "mac_address": "00:11:22:33:44:55",
    #     "os": "Linux",
    #     "asset_type": "server",
    #     "last_seen": "2025-01-01T12:00:00Z",
    #     "details": {"cpu": "Intel i7"}
    # })
