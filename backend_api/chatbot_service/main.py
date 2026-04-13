from fastapi import FastAPI
from .api import router as chatbot_router

app = FastAPI(
    title="Chatbot Service",
    description="Service for the SOC Copilot chatbot.",
    version="1.0.0"
)

app.include_router(chatbot_router)

@app.get("/")
async def read_root():
    return {"message": "Chatbot Service is running"}
