from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from .zero_trust_engine import ZeroTrustEngine, ZeroTrustPolicy
from loguru import logger

router = APIRouter()

# Initialize the ZeroTrustEngine (our Policy Engine)
policy_engine = ZeroTrustEngine()

@router.post("/policies/", response_model=ZeroTrustPolicy, status_code=status.HTTP_201_CREATED)
async def create_policy(policy: ZeroTrustPolicy):
    """
    Creates a new security policy.
    """
    if policy_engine.get_policy(policy.policy_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Policy with this ID already exists.")
    policy_engine.add_policy(policy)
    logger.info(f"Policy '{policy.name}' ({policy.policy_id}) created.")
    return policy

@router.get("/policies/", response_model=List[ZeroTrustPolicy])
async def get_all_policies():
    """
    Retrieves all security policies.
    """
    return policy_engine.get_all_policies()

@router.get("/policies/{policy_id}", response_model=ZeroTrustPolicy)
async def get_policy(policy_id: str):
    """
    Retrieves a specific security policy by its ID.
    """
    policy = policy_engine.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found.")
    return policy

@router.put("/policies/{policy_id}", response_model=ZeroTrustPolicy)
async def update_policy(policy_id: str, updated_policy: ZeroTrustPolicy):
    """
    Updates an existing security policy.
    """
    if policy_id != updated_policy.policy_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Policy ID in path must match policy ID in body.")
    
    existing_policy = policy_engine.get_policy(policy_id)
    if not existing_policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found.")
    
    policy_engine.update_policy(policy_id, updated_policy)
    logger.info(f"Policy '{policy_id}' updated.")
    return updated_policy

@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(policy_id: str):
    """
    Deletes a security policy by its ID.
    """
    if not policy_engine.delete_policy(policy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found.")
    logger.info(f"Policy '{policy_id}' deleted.")
    return
