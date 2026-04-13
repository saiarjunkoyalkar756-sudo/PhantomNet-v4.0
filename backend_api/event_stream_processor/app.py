from fastapi import FastAPI, Depends, Request
from datetime import datetime
import logging
import threading
from .consumer import start_kafka_consumer
import asyncio
...
@app.on_event("startup")
async def startup_event():
    logger.info("Event Stream Processor starting up...")
    # Start the Kafka consumer as a background task
    asyncio.create_task(start_kafka_consumer())
    logger.info("Kafka consumer for Event Stream Processor started.")


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Event Stream Processor is healthy"}

@app.get("/logs")
async def get_logs(request: Request, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None):
    """
    Retrieves logs from the database, with filtering.
    This is a simplified version. A production implementation should have
    pagination, filtering, and error handling.
    """
    conn = get_db_connection()
    if conn is None:
        return {"error": "Could not connect to the database."}

    # Build WHERE clause from query parameters
    query_params = request.query_params
    where_clauses = []
    values = []
    for key, value in query_params.items():
        if key not in ["start_time", "end_time"]:
            if key.endswith("__contains"):
                field = key[:-10]
                where_clauses.append(f"{field} LIKE %s")
                values.append(f"%{value}%")
            else:
                where_clauses.append(f"{key} = %s")
                values.append(value)

    if start_time:
        where_clauses.append("timestamp >= %s")
        values.append(start_time)
    if end_time:
        where_clauses.append("timestamp <= %s")
        values.append(end_time)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    query = f"SELECT * FROM events {where_sql} ORDER BY timestamp DESC LIMIT 100;"

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, tuple(values))
            logs = cur.fetchall()
            return {"logs": logs}
    except psycopg2.Error as e:
        logger.error(f"Error querying logs: {e}")
        return {"error": "Error querying logs."}
    finally:
        conn.close()
