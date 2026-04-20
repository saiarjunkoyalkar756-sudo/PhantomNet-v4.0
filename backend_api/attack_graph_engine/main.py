from backend_api.shared.service_factory import create_phantom_service
from .graph_builder import GraphBuilder
from .path_analyzer import PathAnalyzer
from .event_consumer import consume_events
from loguru import logger
import asyncio
from pydantic import BaseModel
from backend_api.core.response import success_response, error_response
from fastapi import FastAPI, HTTPException

async def attack_graph_startup(app: FastAPI):
    """
    Handles startup events for the Attack Graph Engine.
    """
    # 1. Initialize the graph components
    app.state.graph_builder = GraphBuilder()
    app.state.path_analyzer = PathAnalyzer(app.state.graph_builder.graph)

    # 2. Start the Kafka consumer as a background task
    app.state.consumer_task = asyncio.create_task(consume_events(app.state.graph_builder))
    logger.info("Attack Graph Engine: Event consumer task started.")

async def attack_graph_shutdown(app: FastAPI):
    if hasattr(app.state, "consumer_task"):
        app.state.consumer_task.cancel()
        await asyncio.gather(app.state.consumer_task, return_exceptions=True)
        logger.info("Attack Graph Engine: Event consumer task stopped.")

app = create_phantom_service(
    name="Attack Graph Engine",
    description="Constructs and analyzes a real-time attack graph from security events.",
    version="1.0.0",
    custom_startup=attack_graph_startup,
    custom_shutdown=attack_graph_shutdown
)

class PathRequest(BaseModel):
    source_node: str
    target_node: str

@app.post("/api/attack-graph/find-paths")
async def find_attack_paths(request: PathRequest):
    """
    Finds the shortest potential attack path between a source and a target node.
    """
    if not hasattr(app.state, "path_analyzer"):
         return error_response(code="SERVICE_UNAVAILABLE", message="Path analyzer not initialized", status_code=503)

    path = app.state.path_analyzer.find_shortest_path(
        request.source_node, request.target_node
    )
    if path:
        return success_response(data={"path": path})
    else:
        return error_response(
            code="NOT_FOUND",
            message=f"No attack path found between {request.source_node} and {request.target_node}",
            status_code=404
        )