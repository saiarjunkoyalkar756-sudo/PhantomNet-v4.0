# tests/test_e2e_pipeline.py

import pytest
import httpx
import asyncio
import uuid
import time
from datetime import datetime

# Base URL for the Gateway API (Orchestrator/Agent API)
GATEWAY_URL = "http://localhost:8000"

@pytest.fixture
async def async_client():
    async with httpx.AsyncClient(base_url=GATEWAY_URL, timeout=10.0) as client:
        yield client

@pytest.mark.asyncio
async def test_full_detection_to_blockchain_lifecycle(async_client):
    """
    E2E Test: Simulates an attack on a honeypot, verifies telemetry ingestion,
    AI analysis, and final record creation on the blockchain.
    """
    
    # 1. Login as Admin to get Token
    login_response = await async_client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin-password" # Default from .env hardening
    })
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Generate Bootstrap Token for Agent
    bootstrap_res = await async_client.post(
        "/api/v1/agents/bootstrap-token", 
        headers=headers
    )
    assert bootstrap_res.status_code == 200
    bootstrap_token = bootstrap_res.json()["data"]["bootstrap_token"]

    # 3. Register a Mock Agent
    agent_id_str = str(uuid.uuid4())
    reg_data = {
        "public_key": f"key-{agent_id_str}",
        "bootstrap_token": bootstrap_token,
        "os": "linux",
        "version": "4.0.0",
        "location": "test-lab-1"
    }
    reg_res = await async_client.post("/api/v1/agents/register", json=reg_data)
    assert reg_res.status_code == 200
    agent_id = reg_res.json()["data"]["agent_id"]

    # 4. Simulate Malicious Event (Honeypot Trigger)
    # This simulates an attacker hitting the honeypot
    attack_data = {
        "ip": "192.168.1.100",
        "port": 445,
        "data": "EternalBlue Attempt payload"
    }
    sim_res = await async_client.post(
        "/api/v1/orchestrator/honeypot/simulate_attack",
        headers=headers,
        json=attack_data
    )
    assert sim_res.status_code == 200
    
    # 5. Wait for the Pipeline to process (Async)
    # Event -> Ingestor -> Kafka -> Processor -> Blockchain
    print("Waiting for pipeline processing...")
    await asyncio.sleep(5) 

    # 6. Verify Blockchain Record
    # The attack should have triggered a new block being mined
    chain_res = await async_client.get("/api/v1/orchestrator/blockchain", headers=headers)
    assert chain_res.status_code == 200
    chain = chain_res.json()["data"]["chain"]
    
    # Check if any block contains the attacker's IP
    found_in_blockchain = False
    for block in chain:
        for tx in block.get("transactions", []):
            if tx.get("recipient") == "192.168.1.100":
                found_in_blockchain = True
                break
    
    assert found_in_blockchain, "Attacker IP not found in blockchain records after simulation."
    print("E2E Pipeline Verification Successful: Event successfully recorded on Blockchain.")

if __name__ == "__main__":
    # Standard pytest call logic would go here
    pass
