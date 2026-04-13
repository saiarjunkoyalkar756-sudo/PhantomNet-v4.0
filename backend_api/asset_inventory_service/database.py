# backend_api/asset_inventory_service/database.py
import json
import logging
from typing import Dict, List, Any, Optional

import networkx as nx

# Configure logger
logger = logging.getLogger(__name__)

# In-memory storage for the asset graph and details
asset_graph = nx.DiGraph()
asset_details: Dict[str, Dict[str, Any]] = {}

MOCK_DATA = {
    "assets": [
        {
            "asset_id": "prod-db-01",
            "asset_type": "database",
            "owner": "data_eng_dept",
            "criticality": 10,
        },
        {
            "asset_id": "billing-api",
            "asset_type": "service",
            "owner": "finance_dept",
            "criticality": 9,
        },
        {
            "asset_id": "auth-service",
            "asset_type": "service",
            "owner": "platform_eng_dept",
            "criticality": 10,
        },
        {
            "asset_id": "cfo-laptop",
            "asset_type": "endpoint",
            "owner": "c_suite",
            "criticality": 8,
        },
        {
            "asset_id": "frontend-web",
            "asset_type": "service",
            "owner": "frontend_dept",
            "criticality": 7,
        },
    ],
    "relationships": [
        {"source": "billing-api", "target": "prod-db-01"},  # billing-api depends on prod-db-01
        {"source": "billing-api", "target": "auth-service"}, # billing-api depends on auth-service
        {"source": "frontend-web", "target": "billing-api"}, # frontend-web depends on billing-api
        {"source": "cfo-laptop", "target": "auth-service"},  # CFO's laptop needs auth
    ],
}


def load_mock_data():
    """
    Loads the mock asset and relationship data into the in-memory graph.
    This simulates loading data from a persistent CMDB or graph database.
    """
    global asset_graph, asset_details
    asset_graph = nx.DiGraph()
    asset_details = {}

    for asset in MOCK_DATA["assets"]:
        asset_id = asset["asset_id"]
        asset_details[asset_id] = asset
        asset_graph.add_node(asset_id, **asset)

    for rel in MOCK_DATA["relationships"]:
        source = rel["source"]
        target = rel["target"]
        # The edge direction represents dependency: source -> target means "source depends on target"
        if source in asset_graph and target in asset_graph:
            asset_graph.add_edge(source, target)

    logger.info(
        f"Loaded {len(asset_details)} assets and {len(asset_graph.edges)} relationships into the graph."
    )


async def get_asset_by_id(asset_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the details of a single asset by its ID.
    """
    return asset_details.get(asset_id)


async def get_asset_dependencies(asset_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Finds all nodes that the given asset_id has an edge to (its successors).
    These are the services it depends on.
    """
    if asset_id not in asset_graph:
        return None
    # Successors in the graph are the dependencies
    dependency_ids = list(asset_graph.successors(asset_id))
    return [asset_details[dep_id] for dep_id in dependency_ids if dep_id in asset_details]


async def get_asset_dependents(asset_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Finds all nodes that have an edge to the given asset_id (its predecessors).
    These are the services that depend on it — i.e., the blast radius.
    """
    if asset_id not in asset_graph:
        return None
    # Predecessors in the graph are the assets that depend on the given asset
    dependent_ids = list(asset_graph.predecessors(asset_id))
    return [asset_details[dep_id] for dep_id in dependent_ids if dep_id in asset_details]
