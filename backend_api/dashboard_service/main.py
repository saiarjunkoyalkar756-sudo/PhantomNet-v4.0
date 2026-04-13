from fastapi import FastAPI
from .api import router as dashboard_router

app = FastAPI(
    title="Dashboard Service",
    description="Service for the main dashboard.",
    version="1.0.0"
)

app.include_router(dashboard_router)

@app.get("/")
async def read_root():
    return {"message": "Dashboard Service is running"}
