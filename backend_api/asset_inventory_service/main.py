# backend_api/asset_inventory_service/main.py
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Depends

from security.authentication import get_current_user
from .database import (
    load_mock_data,
    get_asset_by_id,
    get_asset_dependencies,
    get_asset_dependents,
)
from .schemas import Asset

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the FastAPI application.
    """
    logger.info("Asset Inventory Service starting up...")
    load_mock_data()
    logger.info("Mock asset data loaded.")
    yield
    logger.info("Asset Inventory Service shutting down...")


app = FastAPI(
    title="Asset Inventory Service",
    description="Manages and provides data on organizational assets, their relationships, and criticality.",
    version="1.0.0",
    lifespan=lifespan,
    dependencies=[Depends(get_current_user)],
)


@app.get("/assets/{asset_id}", response_model=Asset)
async def read_asset(asset_id: str):
    """
    Retrieves detailed information about a specific asset by its ID.
    """
    db_asset = await get_asset_by_id(asset_id)
    if db_asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return db_asset


@app.get("/assets/{asset_id}/dependencies")
async def read_asset_dependencies(asset_id: str):
    """
    Retrieves all assets that the specified asset depends on (e.g., databases, APIs).
    """
    dependencies = await get_asset_dependencies(asset_id)
    if dependencies is None:
        raise HTTPException(
            status_code=404,
            detail="Asset not found, cannot retrieve dependencies",
        )
    return {
        "asset_id": asset_id,
        "dependencies": dependencies,
    }


@app.get("/assets/{asset_id}/dependents")
async def read_asset_dependents(asset_id: str):
    """
    Retrieves all assets that depend on the specified asset (its blast radius).
    This is crucial for the SOAR engine's blast radius analysis.
    """
    dependents = await get_asset_dependents(asset_id)
    if dependents is None:
        raise HTTPException(
            status_code=404, detail="Asset not found, cannot retrieve dependents"
        )
    return {
        "asset_id": asset_id,
        "dependents": dependents,
    }


# To allow running this service directly for testing
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8008,
    )  # Port 8008 for the asset service
