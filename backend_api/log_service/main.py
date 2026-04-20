from backend_api.shared.service_factory import create_phantom_service
from .api import router as logs_router
from fastapi import FastAPI

app = create_phantom_service(
    name="Log Service",
    description="Centralized event logging and retrieval service.",
    version="1.0.0"
)

app.include_router(logs_router)

@app.get("/status")
async def read_root():
    return {"status": "log-service-operational"}
