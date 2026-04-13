from fastapi import FastAPI
from .api import router as agent_command_router

app = FastAPI(
    title="Agent Command Service",
    description="Service for sending commands to agents.",
    version="1.0.0"
)

app.include_router(agent_command_router)

@app.get("/")
async def read_root():
    return {"message": "Agent Command Service is running"}
