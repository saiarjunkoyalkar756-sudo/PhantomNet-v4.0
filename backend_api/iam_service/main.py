from fastapi import FastAPI
from .api import router as iam_router

app = FastAPI(
    title="IAM Service",
    description="Service for Identity and Access Management.",
    version="1.0.0"
)

app.include_router(iam_router)

@app.get("/")
async def read_root():
    return {"message": "IAM Service is running"}
