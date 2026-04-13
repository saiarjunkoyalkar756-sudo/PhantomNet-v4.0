# backend_api/attack_graph_engine/main.py
import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .graph_builder import GraphBuilder
from .path_analyzer import PathAnalyzer
from .event_consumer import consume_events

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Global instances of our core components
graph_builder: GraphBuilder
path_analyzer: PathAnalyzer
consumer_task: asyncio.Task


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the FastAPI application.
    """
    global graph_builder, path_analyzer, consumer_task
    logger.info("Attack Graph Engine starting up...")

    # 1. Initialize the graph components
    graph_builder = GraphBuilder()
    path_analyzer = PathAnalyzer(graph_builder.graph)

    # 2. Start the Kafka consumer as a background task
    consumer_task = asyncio.create_task(consume_events(graph_builder))
    logger.info("Event consumer task started.")

    yield

    # Shutdown logic
    logger.info("Attack Graph Engine shutting down...")
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        logger.info("Event consumer task successfully cancelled.")


app = FastAPI(
    title="Attack Graph Engine",
    description="Constructs and analyzes a real-time attack graph from security events.",
    version="1.0.0",
    lifespan=lifespan,
)


class PathRequest(BaseModel):
    source_node: str
    target_node: str


@app.get("/health")
async def health_check():
    """
    Returns the health status of the Attack Graph Engine.
    """
    return {"status": "ok", "message": "Attack Graph Engine is healthy"}


@app.post("/api/attack-graph/find-paths")
async def find_attack_paths(request: PathRequest):
    """
    Finds the shortest potential attack path between a source and a target node.
    The "cost" of the path is determined by the weights of the edges.
    """
    path = path_analyzer.find_shortest_path(
        request.source_node, request.target_node
    )
    if path:
        return {"path": path}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"No attack path found between {request.source_node} and {request.target_node}",
        )


# To allow running this service directly for testing
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8009)