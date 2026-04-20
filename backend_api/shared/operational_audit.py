import asyncio
import httpx
import json
import uuid
import time
from typing import (
    Optional,
    List,
    Dict,
    Any,
)
from backend_api.shared.pqc_wrapper import PQCWrapper
from backend_api.shared.bio_fusion_engine import BioFusionEngine
from backend_api.shared.consensus_engine import ConsensusEngine
from loguru import logger

# --- PhantomNet Operational Audit Suite ---
# This tool verifies all hardened and agentic layers of the grid.

BASE_URL = "http://localhost:8000"
IAM_URL = "http://localhost:8002"

async def test_hardening_headers():
    logger.info("TEST: Probing Security Headers...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            headers = response.headers
            
            checks = {
                "HSTS": "Strict-Transport-Security" in headers,
                "CSP": "Content-Security-Policy" in headers,
                "X-Frame": "X-Frame-Options" in headers,
                "X-Content-Type": "X-Content-Type-Options" in headers
            }
            
            for key, val in checks.items():
                status = "PASS" if val else "FAIL"
                logger.info(f"  - {key}: {status}")
            
            return all(checks.values())
        except Exception as e:
            logger.error(f"  - Hardening Test Failed: Connection error to {BASE_URL}")
            return False

async def test_pqc_handshake():
    logger.info("TEST: Post-Quantum Cryptography Handshake...")
    async with httpx.AsyncClient() as client:
        try:
            payload = {"public_key_id": f"phantom_peer_{uuid.uuid4().hex[:8]}"}
            response = await client.post(f"{BASE_URL}/api/security/pqc-handshake", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if "ciphertext" in data and "shared_secret_id" in data:
                    logger.info("  - PQC ML-KEM Key Exchange: PASS")
                    return True
            logger.error(f"  - PQC Test Failed: {response.status_code}")
            return False
        except Exception as e:
            logger.error(f"  - PQC Test Error: {e}")
            return False

async def test_agent_consensus():
    logger.info("TEST: AI Agent Consensus Logic...")
    # Directly verify the shared ConsensusEngine logic
    consensus = ConsensusEngine()
    incident_id = str(uuid.uuid4())
    
    # Proposing a high-impact task
    await consensus.initiate_vote(
        incident_id=incident_id,
        proposed_action="ISOLATE_HOST",
        agent_count=3
    )
    
    # Simulating Quorum (Agents voting)
    await consensus.cast_vote(incident_id, "Agent_Ghost", True, "Detected lateral movement")
    await consensus.cast_vote(incident_id, "Agent_Recon", True, "Confirmed suspicious process PID 4421")
    await consensus.cast_vote(incident_id, "Agent_Sentinel", False, "Wait for memory dump")
    
    status = await consensus.check_consensus(incident_id)
    if status["status"] == "approved":
        logger.info(f"  - Multi-Agent Federation Quorum ({status['approval_ratio']*100}%): PASS")
        return True
    else:
        logger.error(f"  - Consensus Test Failed: Expected approved, got {status['status']}")
        return False

async def test_bio_identity():
    logger.info("TEST: Bio-Fusion Behavioral Identity...")
    bio = BioFusionEngine()
    user_id = "analyst_delta"
    
    # 1. Register a baseline (consistent typing cadence)
    # Extracted dwell/flight logic requires list of dicts with 'press' and 'release'
    consistent_data = {
        "keystrokes": [
            {"press": 10.0, "release": 10.12},
            {"press": 10.2, "release": 10.32},
            {"press": 10.4, "release": 10.51}
        ],
        "pointer_speed": 150.0
    }
    bio.learn_baseline(user_id, consistent_data)
    
    # 2. Verify against match (similar cadence)
    match_data = {
        "keystrokes": [
            {"press": 20.0, "release": 20.13},
            {"press": 20.2, "release": 20.31},
            {"press": 20.4, "release": 20.52}
        ]
    }
    match_result = bio.verify_session(user_id, match_data)
    
    # 3. Verify against mismatch (anomalous cadence / slow dwell)
    anomalous_data = {
        "keystrokes": [
            {"press": 30.0, "release": 30.80}, # Very long dwell
            {"press": 31.0, "release": 31.05}, # Very short dwell
            {"press": 32.0, "release": 32.99}
        ]
    }
    mismatch_result = bio.verify_session(user_id, anomalous_data)
    
    if match_result["verified"] is True and mismatch_result["verified"] is False:
        logger.info(f"  - Behavioral Biometric Recognition (Match: {match_result['score']:.2f}, Mismatch: {mismatch_result['score']:.2f}): PASS")
        return True
    else:
        logger.error(f"  - Bio-Identity Test Failed: Match={match_result['verified']}, Mismatch={mismatch_result['verified']}")
        return False

async def main():
    logger.info("--- STARTING PHANTOMNET OPERATIONAL AUDIT ---")
    results = await asyncio.gather(
        test_hardening_headers(),
        test_pqc_handshake(),
        test_agent_consensus(),
        test_bio_identity()
    )
    
    if all(results):
        logger.info("--- ALL SYSTEMS OPERATIONAL AND HARDENED ---")
    else:
        logger.warning("--- AUDIT COMPLETE WITH FAILURES ---")

if __name__ == "__main__":
    asyncio.run(main())
