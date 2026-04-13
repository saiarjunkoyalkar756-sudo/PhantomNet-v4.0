# core/logging_config.py
import logging
from typing import Any
from utils.logger import get_logger # Import the new logger factory

def setup_logging(log_level_str: str, agent_id: str, mode: str) -> logging.Logger:
    """
    Sets up logging for the PhantomNet Agent using the structured JSON logger.
    """
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    # Assuming 'localhost' as host for now, will refine when host detection is implemented
    agent_host = "localhost" 

    # Get the main agent logger configured for structured JSON output
    main_logger = get_logger("phantomnet_agent", level=log_level, agent_id=agent_id, host=agent_host)
    
    main_logger.info(f"Logging initialized for agent {agent_id} in {mode} mode.")
    main_logger.info(f"Log level set to: {log_level_str.upper()}")
    main_logger.info(f"Logs are being written to: {main_logger.handlers[-1].baseFilename} (structured JSON)") # Access file handler's path

    return main_logger