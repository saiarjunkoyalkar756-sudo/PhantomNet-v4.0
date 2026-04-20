from backend_api.shared.service_factory import create_phantom_service
from backend_api.core.response import success_response, error_response
from .tools import run_yara_scan, analyze_memory_dump, analyze_pcap, reconstruct_timeline
from loguru import logger
import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from pydantic import BaseModel

UPLOAD_DIR = "/tmp/dfir_uploads"

class YaraScanRequest(BaseModel):
    file_path: str
    rules_path: str = None

class MemoryAnalysisRequest(BaseModel):
    dump_path: str

class PcapAnalysisRequest(BaseModel):
    pcap_path: str

class TimelineReconstructionRequest(BaseModel):
    event_logs_path: str

async def dfir_startup(app: FastAPI):
    """
    Handles startup events for the DFIR Toolkit.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    logger.info(f"DFIR Toolkit: Upload directory {UPLOAD_DIR} initialized.")

app = create_phantom_service(
    name="DFIR Toolkit Service",
    description="Provides forensic capabilities (YARA, Memory, PCAP, Timeline).",
    version="1.0.0",
    custom_startup=dfir_startup
)

@app.post("/yara_scan")
async def yara_scan_endpoint(request: YaraScanRequest):
    logger.info(f"YARA scan request: {request.file_path}")
    results = run_yara_scan(request.file_path, request.rules_path)
    return success_response(data=results)

@app.post("/memory_analysis")
async def memory_analysis_endpoint(request: MemoryAnalysisRequest):
    logger.info(f"Memory analysis request: {request.dump_path}")
    results = analyze_memory_dump(request.dump_path)
    return success_response(data=results)

@app.post("/pcap_analysis")
async def pcap_analysis_endpoint(request: PcapAnalysisRequest):
    logger.info(f"PCAP analysis request: {request.pcap_path}")
    results = analyze_pcap(request.pcap_path)
    return success_response(data=results)

@app.post("/timeline_reconstruction")
async def timeline_reconstruction_endpoint(request: TimelineReconstructionRequest):
    logger.info(f"Timeline reconstruction request: {request.event_logs_path}")
    results = reconstruct_timeline(request.event_logs_path)
    return success_response(data=results)

@app.post("/upload_for_analysis")
async def upload_file_for_analysis(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    try:
        content = await file.read()
        with open(file_location, "wb+") as file_object:
            file_object.write(content)
        logger.info(f"File uploaded: {file_location}")
        return success_response(data={"filename": file.filename, "location": file_location})
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return error_response(code="UPLOAD_FAILED", message=str(e), status_code=500)
