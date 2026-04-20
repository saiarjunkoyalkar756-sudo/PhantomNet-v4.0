from backend_api.shared.service_factory import create_phantom_service
from loguru import logger
from pydantic import BaseModel
from backend_api.core.response import success_response, error_response
from fastapi import FastAPI, HTTPException
from .database import get_db_connection

app = create_phantom_service(
    name="Graph Intelligence Service",
    description="Advanced graph-based intelligence and analytics.",
    version="1.0.0"
)

class CypherQuery(BaseModel):
    query: str

@app.post("/graph")
async def query_graph(query: CypherQuery):
    """
    Executes a Cypher query against the graph database.
    """
    db = get_db_connection()
    try:
        results = db.query(query.query)
        # Neo4j records are not directly JSON serializable
        serializable_results = [dict(record) for record in results]
        return success_response(data={"results": serializable_results})
    except Exception as e:
        logger.error(f"Error executing Cypher query: {e}")
        return error_response(code="QUERY_EXECUTION_FAILED", message=str(e), status_code=500)
