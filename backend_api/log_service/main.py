from fastapi import FastAPI
from .api import router as logs_router

app = FastAPI(
    title="Log Service",
    description="Service for storing and retrieving logs.",
    version="1.0.0"
)

app.include_router(logs_router)

@app.get("/")
async def read_root():
    return {"message": "Log Service is running"}
