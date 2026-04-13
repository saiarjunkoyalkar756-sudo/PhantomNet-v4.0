from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import logging
import os
import json
import uuid
import yaml

from .plugin_manager import PluginManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

PLUGIN_DIR = os.path.join(os.path.dirname(__file__), "plugins")
os.makedirs(PLUGIN_DIR, exist_ok=True)

plugin_manager = PluginManager(PLUGIN_DIR)


class PluginUpload(BaseModel):
    # This model is mostly for API documentation; file upload is handled by UploadFile
    pass


@app.on_event("startup")
async def startup_event():
    logger.info("Plugin Marketplace service starting up...")
    plugin_manager.load_installed_plugins()


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Plugin Marketplace service is healthy"}


@app.post("/plugins/upload", status_code=201)
async def upload_plugin(file: UploadFile = File(...)):
    # In a real scenario, this would involve unpacking a zip/tar, validating manifest, etc.
    # For now, we'll just store the file and expect a manifest.json to be uploaded separately
    file_location = os.path.join(PLUGIN_DIR, file.filename)
    try:
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
        logger.info(f"Plugin file uploaded to {file_location}")

        # Attempt to load/parse as a manifest
        if file.filename.endswith(".json"):
            with open(file_location, "r") as f:
                manifest = json.load(f)
            plugin_manager.register_plugin(manifest, file.filename)
            return {
                "message": "Plugin manifest uploaded and registered",
                "filename": file.filename,
                "manifest": manifest,
            }

        return {"message": "Plugin file uploaded", "filename": file.filename}
    except Exception as e:
        logger.error(f"Error uploading plugin file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not upload plugin: {e}")


@app.get("/plugins")
async def list_plugins():
    return plugin_manager.list_plugins()


@app.get("/plugins/{plugin_id}")
async def get_plugin_details(plugin_id: str):
    plugin = plugin_manager.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin


@app.post("/plugins/{plugin_id}/enable")
async def enable_plugin(plugin_id: str):
    result = plugin_manager.enable_plugin(plugin_id)
    if not result:
        raise HTTPException(
            status_code=404, detail="Plugin not found or could not be enabled"
        )
    return {"message": f"Plugin {plugin_id} enabled", "status": result}


@app.post("/plugins/{plugin_id}/disable")
async def disable_plugin(plugin_id: str):
    result = plugin_manager.disable_plugin(plugin_id)
    if not result:
        raise HTTPException(
            status_code=404, detail="Plugin not found or could not be disabled"
        )
    return {"message": f"Plugin {plugin_id} disabled", "status": result}
