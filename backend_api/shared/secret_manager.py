# backend_api/shared/secret_manager.py
import os
import secrets
from loguru import logger

def get_secret(key: str, generate_if_missing: bool = False) -> str:
    """
    Retrieves a secret from environment variables.
    If not found:
    - In development/testing environments, automatically behaves as generate_if_missing=True.
    - If generate_if_missing is True, generates a temporary secure random secret.
    - Otherwise, raises a ValueError. This is a hard failure to prevent running without critical secrets.
    """
    value = os.getenv(key)
    if value:
        return value
    
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env in ["development", "testing"]:
        generate_if_missing = True
        
    if generate_if_missing:
        generated_secret = secrets.token_hex(32) # Generate a 64-char hex string
        logger.warning(f"Generated a temporary secret for {key}. This is INSECURE and should NOT be used in production. Configure this key in your .env file.")
        os.environ[key] = generated_secret
        return generated_secret
    
    logger.critical(f"CRITICAL: Required secret '{key}' is not set in the environment.")
    raise ValueError(f"Required secret '{key}' is not set. The application cannot start without it.")

def generate_strong_secret(length_bytes: int = 32) -> str:
    """Generates a strong, random hex secret."""
    return secrets.token_hex(length_bytes)

def validate_secrets() -> None:
    """
    Startup validation hook to inspect critical security configurations.
    Verifies that required credentials are set, avoid defaults ('changeme'),
    and meet strong complexity criteria.
    
    In production and staging environments, failures strictly prevent startup.
    In development and testing, complexity warnings are logged but startup is permitted.
    """
    critical_keys = ["JWT_SECRET_KEY", "DB_PASSWORD", "NEO4J_PASSWORD"]
    env = os.getenv("ENVIRONMENT", "development").lower()
    is_strict = env in ["production", "staging"]
    
    for key in critical_keys:
        value = os.getenv(key)
        if not value:
            if not is_strict:
                fallback_value = "changeme123" if key in ["DB_PASSWORD", "NEO4J_PASSWORD"] else secrets.token_hex(32)
                os.environ[key] = fallback_value
                logger.warning(f"Development mode fallback: Set missing environment secret '{key}' to '{fallback_value}'.")
                continue
            err_msg = f"Required environment secret '{key}' is missing."
            logger.critical(f"SECURITY AUDIT FAILED: {err_msg}")
            raise ValueError(err_msg)
            
        # Check insecure default
        if value == "changeme" or "changeme" in value.lower():
            warn_msg = f"Secret '{key}' is using an insecure default value ('{value}')."
            if is_strict:
                logger.critical(f"SECURITY AUDIT FAILED: {warn_msg}")
                raise ValueError(f"Insecure default value detected for critical secret '{key}' in production.")
            else:
                logger.warning(f"INSECURE CONFIGURATION WARNING: {warn_msg} Change this in your .env file.")
                continue
                
        # Complexity validation for passwords
        if key in ["DB_PASSWORD", "NEO4J_PASSWORD"]:
            if len(value) < 8:
                warn_msg = f"Password '{key}' must be at least 8 characters (got {len(value)})."
                if is_strict:
                    logger.critical(f"SECURITY AUDIT FAILED: {warn_msg}")
                    raise ValueError(f"Complexity violation for secret '{key}'.")
                else:
                    logger.warning(f"SECURITY COMPLEXITY WARNING: {warn_msg}")
            elif not any(c.isdigit() for c in value) or not any(c.isalpha() for c in value):
                warn_msg = f"Password '{key}' must contain both letters and numbers."
                if is_strict:
                    logger.critical(f"SECURITY AUDIT FAILED: {warn_msg}")
                    raise ValueError(f"Complexity violation for secret '{key}'.")
                else:
                    logger.warning(f"SECURITY COMPLEXITY WARNING: {warn_msg}")
                    
        # Complexity validation for cryptographic keys
        if key == "JWT_SECRET_KEY":
            if len(value) < 32:
                warn_msg = f"Cryptographic secret '{key}' must be at least 32 characters."
                if is_strict:
                    logger.critical(f"SECURITY AUDIT FAILED: {warn_msg}")
                    raise ValueError(f"Complexity violation for secret '{key}'.")
                else:
                    logger.warning(f"SECURITY COMPLEXITY WARNING: {warn_msg}")
                    
    logger.info("Startup Validation: All critical environment secrets inspected successfully.")
