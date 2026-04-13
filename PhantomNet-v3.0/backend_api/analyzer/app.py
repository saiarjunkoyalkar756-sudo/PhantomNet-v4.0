from fastapi import FastAPI, Body
import threading
import os
from . import consumer
from .neural_threat_brain import brain

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    thread = threading.Thread(target=consumer.main)
    thread.start()

@app.get("/")
def read_root():
    return {"Hello": "Analyzer"}

@app.post("/chat")
async def chat_with_ai(message: str = Body(..., embed=True), conversation_history: list = Body([], embed=True)):
    """
    Engage in a conversation with the AI.
    """
    response = brain.chat(message, conversation_history)
    return {"response": response}
