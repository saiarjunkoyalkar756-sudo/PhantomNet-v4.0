from backend_api.shared.service_factory import create_phantom_service
from .consumer import start_kafka_consumer
from loguru import logger
import asyncio
from pydantic import BaseModel
from backend_api.core.response import success_response

async def ai_startup(app: FastAPI):
    # Start the Kafka consumer as a background task
    app.state.consumer_task = asyncio.create_task(start_kafka_consumer())
    logger.info("Kafka consumer task started.")

async def ai_shutdown(app: FastAPI):
    if hasattr(app.state, "consumer_task"):
        app.state.consumer_task.cancel()
        await asyncio.gather(app.state.consumer_task, return_exceptions=True)
        logger.info("Kafka consumer task stopped.")

app = create_phantom_service(
    name="AI Behavioral Engine",
    description="Real-time behavioral analytics and anomaly detection.",
    version="1.0.0",
    custom_startup=ai_startup,
    custom_shutdown=ai_shutdown
)

class BehavioralEvent(BaseModel):
    event_id: str
    user_id: str
    entity_id: str
    timestamp: str
    data: dict

@app.post("/analyze")
async def analyze_behavioral_event(event: BehavioralEvent):
    return success_response(data={
        "event_id": event.event_id,
        "analysis_pending": False,
        "detection_status": "queued_for_deep_analysis"
    })

@app.get("/profiles/user/{user_id}")
async def get_user_profile(user_id: str):
    return success_response(data={
        "user_id": user_id,
        "risk_profile": "low",
        "last_seen": "2026-04-19T12:00:00Z"
    })
