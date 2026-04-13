# backend_api/shared/secret_manager.py
import os
import secrets
from loguru import logger

import os
import secrets
from loguru import logger

def get_secret(key: str, generate_if_missing: bool = False) -> str:
    """
    Retrieves a secret from environment variables.
    If not found:
    - If generate_if_missing is True, generates a temporary secure random secret.
    - Otherwise, raises a ValueError. This is a hard failure to prevent running without critical secrets.
    """
    value = os.getenv(key)
    if value:
        return value
    
    if generate_if_missing:
        generated_secret = secrets.token_hex(32) # Generate a 64-char hex string
        logger.warning(f"Generated a temporary secret for {key}. This is INSECURE and should NOT be used in production. Configure this key in your .env file.")
        return generated_secret
    
    logger.critical(f"CRITICAL: Required secret '{key}' is not set in the environment.")
    raise ValueError(f"Required secret '{key}' is not set. The application cannot start without it.")

def generate_strong_secret(length_bytes: int = 32) -> str:
    """Generates a strong, random hex secret."""
    return secrets.token_hex(length_bytes)
