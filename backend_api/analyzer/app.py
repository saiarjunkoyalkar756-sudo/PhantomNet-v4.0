from backend_api.shared.service_factory import create_phantom_service
import threading
import asyncio
from fastapi import Body
from . import consumer
from .neural_threat_brain import brain
from backend_api.core.response import success_response

async def analyzer_startup(app: FastAPI):
    # Start consumer in a separate thread as per legacy requirement, but managed via lifespan
    app.state.consumer_thread = threading.Thread(target=consumer.main, daemon=True)
    app.state.consumer_thread.start()

app = create_phantom_service(
    name="Analyzer Service",
    description="Neural threat brain and log analysis service.",
    version="1.0.0",
    custom_startup=analyzer_startup
)

@app.post("/chat")
async def chat_with_ai(
    message: str = Body(..., embed=True),
    conversation_history: list = Body([], embed=True),
):
    """
    Engage in a conversation with the AI.
    """
    response = brain.chat(message, conversation_history)
    return success_response(data={"response": response})
