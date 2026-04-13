# backend_api/sandbox_service/app.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import logging
from typing import Dict, Any
import base64
import random
import hashlib
import os
import os

logger = logging.getLogger(__name__)

app = FastAPI()

class AnalysisResult(BaseModel):
    file_name: str
    file_hash: str
    analysis_id: str
    status: str
    verdict: str
    api_behaviors: Dict[str, Any]
    network_traffic: Dict[str, Any]
    crypto_routines: Dict[str, Any]
    dropped_artifacts: Dict[str, Any]
    raw_output: str


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Sandbox Service is healthy"}


@app.post("/analyze", response_model=AnalysisResult)
async def analyze_file(file: UploadFile = File(...)):
    """
    Submits a file for simulated malware analysis in the sandbox.
    """
    logger.info(f"Received file for analysis: {file.filename}")

    try:
        file_content = await file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        analysis_id = base64.urlsafe_b64encode(os.urandom(16)).decode('utf-8').rstrip('=')

        # Simulate analysis results
        verdict = random.choice(["MALICIOUS", "CLEAN", "SUSPICIOUS"])
        api_behaviors = {
            "create_process": random.randint(0, 10),
            "read_registry": random.randint(0, 5),
            "network_connect": random.randint(0, 7),
        }
        network_traffic = {
            "dns_requests": [f"example.com.{i}" for i in range(random.randint(0, 3))],
            "http_requests": [f"http://malicious.site/{i}" for i in range(random.randint(0, 2))],
        }
        crypto_routines = {
            "aes_usage": random.choice([True, False]),
            "rsa_usage": random.choice([True, False]),
        }
        dropped_artifacts = {
            "files": [f"temp_file_{i}.tmp" for i in range(random.randint(0, 2))],
            "registry_keys": [f"HKLM\Software\Malware_{i}" for i in range(random.randint(0, 1))],
        }
        raw_output = f"Simulated sandbox analysis report for {file.filename} (hash: {file_hash}). Verdict: {verdict}"

        return AnalysisResult(
            file_name=file.filename,
            file_hash=file_hash,
            analysis_id=analysis_id,
            status="COMPLETED",
            verdict=verdict,
            api_behaviors=api_behaviors,
            network_traffic=network_traffic,
            crypto_routines=crypto_routines,
            dropped_artifacts=dropped_artifacts,
            raw_output=raw_output,
        )

    except Exception as e:
        logger.error(f"Error during file analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"File analysis failed: {e}")

