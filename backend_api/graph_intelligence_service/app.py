# backend_api/graph_intelligence_service/app.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import threading
from .consumer import start_consumer
from .database import get_db_connection

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

class CypherQuery(BaseModel):
    query: str

@app.on_event("startup")
async def startup_event():
    logger.info("Graph Intelligence Service starting up...")
    # consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    # consumer_thread.start()
    # logger.info("RabbitMQ consumer for Graph Intelligence Service started.")

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Graph Intelligence Service is healthy"}

@app.post("/graph")
async def query_graph(query: CypherQuery):
    """
    Executes a Cypher query against the graph database.
    """
    db = get_db_connection()
    try:
        results = db.query(query.query)
        # Neo4j records are not directly JSON serializable
        # You need to convert them to a serializable format
        serializable_results = [dict(record) for record in results]
        return {"results": serializable_results}
    except Exception as e:
        logger.error(f"Error executing Cypher query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error during query execution."
        )
