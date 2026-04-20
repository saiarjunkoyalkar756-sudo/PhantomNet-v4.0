from backend_api.shared.service_factory import create_phantom_service
from backend_api.database import create_db_and_tables
from . import consumer
from loguru import logger
from fastapi import FastAPI
import threading
import os

async def blockchain_service_startup(app: FastAPI):
    """
    Handles startup events for the Blockchain Service.
    """
    create_db_and_tables()
    thread = threading.Thread(target=consumer.main)
    thread.daemon = True
    thread.start()
    logger.info("Blockchain Service: DB initialized and consumer thread started.")

app = create_phantom_service(
    name="Blockchain Service",
    description="Maintains an immutable ledger of security events.",
    version="1.0.0",
    custom_startup=blockchain_service_startup
)

@app.get("/status")
async def status():
    return {"status": "blockchain-ledger-operational"}
