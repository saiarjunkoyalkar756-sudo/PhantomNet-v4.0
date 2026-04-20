from backend_api.shared.service_factory import create_phantom_service
from .consumer import start_kafka_consumer
from .database import get_db_connection
from loguru import logger
import asyncio
from datetime import datetime
from typing import Optional
import psycopg2.extras
from backend_api.core.response import success_response, error_response
from fastapi import Request, FastAPI

async def stream_startup(app: FastAPI):
    # Start the Kafka consumer as a background task
    app.state.consumer_task = asyncio.create_task(start_kafka_consumer())
    logger.info("Kafka consumer for Event Stream Processor started.")

async def stream_shutdown(app: FastAPI):
    if hasattr(app.state, "consumer_task"):
        app.state.consumer_task.cancel()
        await asyncio.gather(app.state.consumer_task, return_exceptions=True)
        logger.info("Kafka consumer task stopped.")

app = create_phantom_service(
    name="Event Stream Processor",
    description="Real-time event processing and archiving.",
    version="1.0.0",
    custom_startup=stream_startup,
    custom_shutdown=stream_shutdown
)

@app.get("/logs")
async def get_logs(request: Request, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None):
    """
    Retrieves logs from the database, with filtering.
    """
    conn = get_db_connection()
    if conn is None:
        return error_response(code="DATABASE_ERROR", message="Could not connect to the database.", status_code=500)

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
            return success_response(data={"logs": logs})
    except Exception as e:
        logger.error(f"Error querying logs: {e}")
        return error_response(code="QUERY_ERROR", message="Error querying logs.", status_code=500)
    finally:
        conn.close()
