from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import threading
import json
from typing import List, Optional

from .consumer import start_kafka_consumer
from .database import create_rules_table, get_all_rules, upsert_rule
import asyncio

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()


class Rule(BaseModel):
    name: str
    description: Optional[str] = None
    logic: dict  # Storing rule logic as JSON
    action: str  # e.g., "alert", "block_ip", "isolate_host"
    severity: str
    enabled: bool = True


@app.on_event("startup")
async def startup_event():
    logger.info("Correlation Engine starting up...")
    create_rules_table()
    # Start the Kafka consumer as a background task
    asyncio.create_task(start_kafka_consumer())
    logger.info("Kafka consumer task started.")


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Correlation Engine is healthy"}


@app.post("/rules", status_code=201)
async def add_or_update_rule(rule: Rule):
    upsert_rule(rule.dict())
    logger.info(f"Rule '{rule.name}' added/updated.")
    return {"message": "Rule added/updated successfully", "rule_name": rule.name}


@app.get("/rules", response_model=List[Rule])
async def get_rules():
    rules = get_all_rules()
    return rules


@app.get("/rules/{rule_name}")
async def get_rule(rule_name: str):
    rules = get_all_rules() # In a large system, you'd have a specific get_rule_by_name function
    for rule in rules:
        if rule["name"] == rule_name:
            return rule
    raise HTTPException(status_code=404, detail="Rule not found")


@app.delete("/rules/{rule_name}")
async def delete_rule(rule_name: str):
    # This example assumes a soft delete by setting enabled=False.
    # A full delete would require a specific DB function.
    existing_rules = get_all_rules()
    rule_found = False
    for rule in existing_rules:
        if rule["name"] == rule_name:
            rule["enabled"] = False
            upsert_rule(rule) # Update the rule to be disabled
            rule_found = True
            break
    
    if not rule_found:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    logger.info(f"Rule '{rule_name}' disabled (soft-deleted).")
    return {"message": "Rule disabled successfully"}
