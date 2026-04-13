from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
import os
from sqlalchemy.orm import Session
from backend_api.database import get_db
import httpx # Import httpx

# This is a bit of a hack for now to make sure the orchestrator has a file to snapshot
# In a real system, this would be a path to a critical system file
DUMMY_SYSTEM_FILE = "dummy_system_state.txt"
if not os.path.exists(DUMMY_SYSTEM_FILE):
    with open(DUMMY_SYSTEM_FILE, "w") as f:
        f.write("Initial system state.")

from phantomnet_agent.orchestrator import Orchestrator

router = APIRouter()

def get_orchestrator(db: Session = Depends(get_db)) -> Orchestrator:
    return Orchestrator(db_session=db, target_system_file=DUMMY_SYSTEM_FILE)

class ThreatData(BaseModel):
    threat_string: str

class MarketplaceModule(BaseModel):
    developer_id: str
    module_name: str
    module_code: str

class ChatRequest(BaseModel): # New Pydantic model for chat requests
    message: str
    conversation_history: list = []

@router.post("/orchestrator/threats/")
async def handle_threat_endpoint(threat_data: ThreatData, orchestrator: Orchestrator = Depends(get_orchestrator)):
    """
    Receives a threat, passes it to the orchestrator, and returns the analysis with explanation.
    """
    # Assuming orchestrator.cognitive_core.analyze_threat now returns a dict with 'label', 'score', and 'explanation'
    analysis_result = orchestrator.cognitive_core.analyze_threat(threat_data.threat_string)
    
    # Extract label and explanation for conditional handling
    threat_label = analysis_result.get("label")
    explanation = analysis_result.get("explanation", "No explanation provided.")

    if threat_label == "NEGATIVE": # Assuming "NEGATIVE" implies a critical threat for this example
        orchestrator.handle_threat(threat_data.threat_string)
        return {"message": "Critical threat detected and handled.", "analysis": analysis_result}
    return {"message": "Threat analyzed.", "analysis": analysis_result}

@router.post("/orchestrator/marketplace/validate")
async def validate_module_endpoint(module_data: MarketplaceModule, orchestrator: Orchestrator = Depends(get_orchestrator)):
    """
    Receives a new marketplace module and passes it to the orchestrator for validation.
    """
    orchestrator.validate_marketplace_module(
        developer_id=module_data.developer_id,
        module_name=module_data.module_name,
        module_code=module_data.module_code
    )
    return {"message": "Module submitted for validation. Check the blockchain for confirmation."}

@router.get("/orchestrator/blockchain/")
async def get_blockchain_endpoint(orchestrator: Orchestrator = Depends(get_orchestrator)):
    """
    Returns the current state of the PhantomChain.
    """
    return {"chain": orchestrator.phantom_chain.chain}

@router.post("/orchestrator/chat") # New chat endpoint
async def chat_with_analyzer(chat_request: ChatRequest):
    """
    Forwards chat messages to the Analyzer service and returns its response.
    """
    analyzer_service_url = os.getenv("ANALYZER_SERVICE_URL", "http://analyzer:8000") # Use environment variable
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{analyzer_service_url}/chat",
                json={"message": chat_request.message, "conversation_history": chat_request.conversation_history}
            )
            response.raise_for_status() # Raise an exception for 4xx or 5xx status codes
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Analyzer service error: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Could not connect to Analyzer service: {e}")
