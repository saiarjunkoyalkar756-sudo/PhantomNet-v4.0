from __future__ import annotations

from fastapi import FastAPI
from loguru import logger

from backend_api.core.response import error_response
from backend_api.shared.service_factory import create_phantom_service
from .database import Neo4jConnection, get_db_connection


async def graph_startup(app: FastAPI) -> None:
    """Verify the required graph store before serving graph-intelligence process endpoints."""
    database = get_db_connection()
    database.query("RETURN 1 AS ready")
    app.state.graph_database = database
    logger.info("Graph intelligence Neo4j connection verified.")


async def graph_shutdown(app: FastAPI) -> None:
    """Close the graph driver owned by this process during controlled shutdown."""
    database = getattr(app.state, "graph_database", None)
    if isinstance(database, Neo4jConnection):
        database.close()
        logger.info("Graph intelligence Neo4j connection closed.")


app = create_phantom_service(
    name="Graph Intelligence Service",
    description="Internal graph-store readiness boundary; tenant-scoped graph investigation is exposed only through governed APIs.",
    version="1.0.0",
    custom_startup=graph_startup,
    custom_shutdown=graph_shutdown,
    required_dependencies=("neo4j",),
)


@app.api_route("/graph", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
@app.api_route("/graph/{legacy_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
async def retired_raw_graph_api(legacy_path: str = ""):
    """Fail closed instead of exposing an unbounded external Cypher execution surface."""
    return error_response(
        code="RAW_GRAPH_API_RETIRED",
        message="Raw graph queries are retired. Use the tenant-scoped governed graph investigation APIs.",
        status_code=410,
    )
