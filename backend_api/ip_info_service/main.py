from fastapi import FastAPI
from .api import router as ip_info_router

app = FastAPI(
    title="IP Info Service",
    description="Service for retrieving information about IP addresses.",
    version="1.0.0"
)

app.include_router(ip_info_router)

@app.get("/")
async def read_root():
    return {"message": "IP Info Service is running"}
