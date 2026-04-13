from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import logging
import os
import time

from .tools import (
    run_yara_scan,
    analyze_memory_dump,
    analyze_pcap,
    reconstruct_timeline,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Directory to store uploaded files for analysis
UPLOAD_DIR = "/tmp/dfir_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class YaraScanRequest(BaseModel):
    file_path: str
    rules_path: str = None  # Path to YARA rules file on the server


class MemoryAnalysisRequest(BaseModel):
    dump_path: str  # Path to memory dump file on the server


class PcapAnalysisRequest(BaseModel):
    pcap_path: str  # Path to PCAP file on the server


class TimelineReconstructionRequest(BaseModel):
    event_logs_path: str  # Path to event logs directory on the server


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "DFIR Toolkit service is healthy"}


@app.post("/yara_scan")
async def yara_scan_endpoint(request: YaraScanRequest):
    logger.info(f"Received YARA scan request for {request.file_path}")
    # In a real scenario, handle file uploads or access remote files securely
    results = run_yara_scan(request.file_path, request.rules_path)
    return {"status": "success", "results": results}


@app.post("/memory_analysis")
async def memory_analysis_endpoint(request: MemoryAnalysisRequest):
    logger.info(f"Received memory analysis request for {request.dump_path}")
    results = analyze_memory_dump(request.dump_path)
    return {"status": "success", "results": results}


@app.post("/pcap_analysis")
async def pcap_analysis_endpoint(request: PcapAnalysisRequest):
    logger.info(f"Received PCAP analysis request for {request.pcap_path}")
    results = analyze_pcap(request.pcap_path)
    return {"status": "success", "results": results}


@app.post("/timeline_reconstruction")
async def timeline_reconstruction_endpoint(request: TimelineReconstructionRequest):
    logger.info(
        f"Received timeline reconstruction request for {request.event_logs_path}"
    )
    results = reconstruct_timeline(request.event_logs_path)
    return {"status": "success", "results": results}


@app.post("/upload_for_analysis")
async def upload_file_for_analysis(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_location, "wb+") as file_object:
            file_object.write(file.file.read())
        logger.info(f"File uploaded to {file_location}")
        return {"info": f"file '{file.filename}' saved at '{file_location}'"}
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not upload file")
