from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any

from .flow_schema import PlaybookFlow
from .flow_converter import convert_flow_to_steps, FlowConversionError

router = APIRouter()

@router.post("/convert", response_model=List[Dict[str, Any]])
async def convert_playbook_flow_to_steps(flow: PlaybookFlow):
    """
    Receives a PlaybookFlow definition and converts it into a list of steps
    compatible with the SOAR Playbook Engine.
    """
    try:
        converted_steps = convert_flow_to_steps(flow)
        return converted_steps
    except FlowConversionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Flow conversion failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {str(e)}")

# In a full implementation, you would add endpoints for:
# - Storing and retrieving PlaybookFlow definitions (with their own DB)
# - Triggering the creation/update of a Playbook in the soar_playbook_engine
#   after conversion.
# For now, this conversion endpoint demonstrates the core logic.