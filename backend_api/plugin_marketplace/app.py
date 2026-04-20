from backend_api.shared.service_factory import create_phantom_service
from backend_api.core.response import success_response, error_response
from .plugin_manager import PluginManager
from loguru import logger
import os
import json
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from pydantic import BaseModel

PLUGIN_DIR = os.path.join(os.path.dirname(__file__), "plugins")
plugin_manager = PluginManager(PLUGIN_DIR)

async def plugin_marketplace_startup(app: FastAPI):
    """
    Handles startup events for the Plugin Marketplace.
    """
    os.makedirs(PLUGIN_DIR, exist_ok=True)
    plugin_manager.load_installed_plugins()
    logger.info("Plugin Marketplace: Plugins loaded and directory ready.")

app = create_phantom_service(
    name="Plugin Marketplace Service",
    description="Platform for managing and deploying security plug-ins.",
    version="1.0.0",
    custom_startup=plugin_marketplace_startup
)

@app.post("/plugins/upload", status_code=201)
async def upload_plugin(file: UploadFile = File(...)):
    file_location = os.path.join(PLUGIN_DIR, file.filename)
    try:
        content = await file.read()
        with open(file_location, "wb+") as file_object:
            file_object.write(content)
        
        if file.filename.endswith(".json"):
            manifest = json.loads(content)
            plugin_manager.register_plugin(manifest, file.filename)
            return success_response(data={
                "message": "Plugin manifest uploaded and registered",
                "filename": file.filename,
                "manifest": manifest
            })

        return success_response(data={"message": "Plugin file uploaded", "filename": file.filename})
    except Exception as e:
        logger.error(f"Plugin upload failed: {e}")
        return error_response(code="UPLOAD_FAILED", message=str(e), status_code=500)

@app.get("/plugins")
async def list_plugins():
    plugins = plugin_manager.list_plugins()
    return success_response(data=plugins)

@app.get("/plugins/{plugin_id}")
async def get_plugin_details(plugin_id: str):
    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        return error_response(code="PLUGIN_NOT_FOUND", message="Plugin not found.", status_code=404)
    return success_response(data=plugin)

@app.post("/plugins/{plugin_id}/enable")
async def enable_plugin(plugin_id: str):
    result = plugin_manager.enable_plugin(plugin_id)
    if not result:
        return error_response(code="ENABLE_FAILED", message="Plugin not found or could not be enabled.", status_code=404)
    return success_response(message=f"Plugin {plugin_id} enabled.", data={"plugin_id": plugin_id, "status": "enabled"})

@app.post("/plugins/{plugin_id}/disable")
async def disable_plugin(plugin_id: str):
    result = plugin_manager.disable_plugin(plugin_id)
    if not result:
        return error_response(code="DISABLE_FAILED", message="Plugin not found or could not be disabled.", status_code=404)
    return success_response(message=f"Plugin {plugin_id} disabled.", data={"plugin_id": plugin_id, "status": "disabled"})
