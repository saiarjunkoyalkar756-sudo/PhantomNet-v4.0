import os
import logging
from logging.handlers import RotatingFileHandler

def get_rotating_file_logger(logger_name: str, log_filename: str) -> logging.Logger:
    """
    Creates and returns a Logger with a RotatingFileHandler configured.
    Max size: 10MB, backups: 5.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if logger is already configured
    if not logger.handlers:
        # Resolve the absolute path of logs directory
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        logs_dir = os.path.join(base_dir, "logs")
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, exist_ok=True)
            
        log_filepath = os.path.join(logs_dir, log_filename)
        
        # 10MB = 10 * 1024 * 1024 bytes
        handler = RotatingFileHandler(log_filepath, maxBytes=10 * 1024 * 1024, backupCount=5)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger
