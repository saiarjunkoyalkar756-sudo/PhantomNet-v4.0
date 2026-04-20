from backend_api.shared.service_factory import create_phantom_service
from backend_api.core.response import success_response, error_response
from .flow_schema import PlaybookFlow
from .flow_converter import convert_flow_to_steps, FlowConversionError
from loguru import logger
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, FastAPI, Request

router = APIRouter()

@router.post("/convert")
async def convert_playbook_flow_to_steps(flow: PlaybookFlow):
    """
    Receives a PlaybookFlow definition and converts it into a list of steps.
    """
    try:
        converted_steps = convert_flow_to_steps(flow)
        return success_response(data=converted_steps)
    except FlowConversionError as e:
        return error_response(code="CONVERSION_FAILED", message=str(e), status_code=400)
    except Exception as e:
        logger.error(f"Unexpected conversion error: {e}")
        return error_response(code="INTERNAL_ERROR", message=str(e), status_code=500)

app = create_phantom_service(
    name="Playbook Flow Builder",
    description="Visual orchestration tool for defining security playbooks.",
    version="1.0.0"
)

app.include_router(router, prefix="/api/v1/playbook-builder", tags=["orchestration"])