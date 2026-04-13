from fastapi import FastAPI
from .api import router as config_router

app = FastAPI(
    title="Config Service",
    description="Service for managing agent configuration.",
    version="1.0.0"
)

app.include_router(config_router)

@app.get("/")
async def read_root():
    return {"message": "Config Service is running"}
