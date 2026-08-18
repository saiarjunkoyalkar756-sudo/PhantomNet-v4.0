"""Attack Graph Engine application entrypoint.

Legacy unscoped traversal is retained only as an explicit deprecation boundary. Governed,
tenant-scoped attack-path analysis is exposed through the included router.
"""

from __future__ import annotations

import asyncio
import os

from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel

from backend_api.shared.service_factory import create_phantom_service
from .event_consumer import consume_events
from .governed_api import router as governed_attack_path_router
from .graph_builder import GraphBuilder
from .path_analyzer import PathAnalyzer


async def attack_graph_startup(app: FastAPI):
    """Start only the explicitly enabled legacy consumer during migration."""
    # Legacy event graphing has no tenant isolation. Keep it disabled unless an operator
    # explicitly enables it while migrating historical deployments to governed analysis.
    if os.getenv("PHANTOMNET_LEGACY_ATTACK_GRAPH_ENABLED", "false").strip().lower() == "true":
        app.state.graph_builder = GraphBuilder()
        app.state.path_analyzer = PathAnalyzer(app.state.graph_builder.graph)
        app.state.consumer_task = asyncio.create_task(consume_events(app.state.graph_builder))
        logger.warning("Legacy unscoped Attack Graph consumer enabled by explicit operator configuration.")
    else:
        logger.info("Legacy unscoped Attack Graph consumer disabled; use governed attack-path analysis.")


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
    custom_shutdown=attack_graph_shutdown,
)
app.include_router(governed_attack_path_router, prefix="/api")


class PathRequest(BaseModel):
    source_node: str
    target_node: str


@app.post("/api/attack-graph/find-paths")
async def find_attack_paths(_request: PathRequest):
    """Reject historical unscoped traversal requests in favor of governed analysis."""
    raise HTTPException(
        status_code=410,
        detail="Legacy unscoped graph traversal is disabled. Use /api/governed-attack-paths/analyze.",
    )
