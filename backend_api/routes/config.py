from fastapi import APIRouter, Depends
from loguru import logger
import os
import json

from iam_service.auth_methods import get_current_user, User, UserRole, has_role

router = APIRouter()

CONFIG_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "phantomnet_agent", "config.json"
)

@router.get("/config", dependencies=[Depends(has_role([UserRole.ADMIN]))])
def get_config(current_user: dict = Depends(get_current_user)):
    # Note: Exposing the agent's configuration, even if not critically sensitive,
    # can provide reconnaissance information to an authenticated attacker.
    # Consider implementing more granular access control or filtering sensitive fields
    # if this endpoint is exposed to non-administrative users in production.
    if not os.path.exists(CONFIG_FILE):
        logger.warning(
            f"User ID: {current_user.id} attempted to fetch non-existent config file."
        )  # Redact username
        return {"error": "Config file not found"}, 404
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    logger.info(f"User ID: {current_user.id} fetched config.")  # Redact username
    return config
