from backend_api.shared.service_factory import create_phantom_service
from .database import (
    load_mock_data,
    get_asset_by_id,
    get_asset_dependencies,
    get_asset_dependents,
)
from .schemas import Asset
from security.authentication import get_current_user
from backend_api.core.response import success_response, error_response
from fastapi import FastAPI, HTTPException, Depends
from loguru import logger

async def asset_startup(app: FastAPI):
    """
    Handles startup events for the Asset Inventory application.
    """
    load_mock_data()
    logger.info("Asset Inventory Service: Mock asset data initialized.")

app = create_phantom_service(
    name="Asset Inventory Service",
    description="Manages organizational assets, relationships, and criticality.",
    version="1.0.0",
    custom_startup=asset_startup,
    dependencies=[Depends(get_current_user)]
)

@app.get("/assets/{asset_id}")
async def read_asset(asset_id: str):
    db_asset = await get_asset_by_id(asset_id)
    if db_asset is None:
        return error_response(code="NOT_FOUND", message="Asset not found", status_code=404)
    return success_response(data=db_asset)

@app.get("/assets/{asset_id}/dependencies")
async def read_asset_dependencies(asset_id: str):
    dependencies = await get_asset_dependencies(asset_id)
    if dependencies is None:
        return error_response(code="NOT_FOUND", message="Asset not found", status_code=404)
    return success_response(data={"asset_id": asset_id, "dependencies": dependencies})

@app.get("/assets/{asset_id}/dependents")
async def read_asset_dependents(asset_id: str):
    dependents = await get_asset_dependents(asset_id)
    if dependents is None:
        return error_response(code="NOT_FOUND", message="Asset not found", status_code=404)
    return success_response(data={"asset_id": asset_id, "dependents": dependents})
