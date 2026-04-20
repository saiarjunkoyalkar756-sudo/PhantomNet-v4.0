from backend_api.shared.service_factory import create_phantom_service
from .consumer import start_kafka_consumer
from .database import init_db, get_all_rules, upsert_rule
from loguru import logger
import asyncio
from pydantic import BaseModel
from typing import List, Optional
from backend_api.core.response import success_response, error_response

async def correlation_startup(app: FastAPI):
    # Startup: Initialize DB and background consumer
    await init_db()
    app.state.consumer_task = asyncio.create_task(start_kafka_consumer())
    logger.info("Kafka consumer task started.")

async def correlation_shutdown(app: FastAPI):
    if hasattr(app.state, "consumer_task"):
        app.state.consumer_task.cancel()
        await asyncio.gather(app.state.consumer_task, return_exceptions=True)
        logger.info("Kafka consumer task stopped.")

app = create_phantom_service(
    name="Correlation Engine",
    description="Real-time threat correlation using Kafka streams.",
    version="1.0.0",
    custom_startup=correlation_startup,
    custom_shutdown=correlation_shutdown
)

class Rule(BaseModel):
    name: str
    description: Optional[str] = None
    logic: dict
    action: str
    severity: str
    enabled: bool = True

@app.post("/rules", status_code=201)
async def add_or_update_rule(rule: Rule):
    await upsert_rule(rule.model_dump())
    return success_response(data={"rule_name": rule.name})

@app.get("/rules")
async def get_rules():
    rules = await get_all_rules()
    return success_response(data=rules)

@app.get("/rules/{rule_name}")
async def get_rule(rule_name: str):
    rules = await get_all_rules()
    for rule in rules:
        if rule["name"] == rule_name:
            return success_response(data=rule)
    return error_response(code="NOT_FOUND", message="Rule not found", status_code=404)

@app.delete("/rules/{rule_name}")
async def delete_rule(rule_name: str):
    existing_rules = await get_all_rules()
    rule_found = False
    for rule in existing_rules:
        if rule["name"] == rule_name:
            rule["enabled"] = False
            await upsert_rule(rule)
            rule_found = True
            break
    
    if not rule_found:
        return error_response(code="NOT_FOUND", message="Rule not found", status_code=404)
    
    return success_response(data={"message": "Rule disabled successfully"})
