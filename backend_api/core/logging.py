# backend_api/core/logging.py
import logging
import json
import sys
import uuid
import time
from datetime import datetime
from pythonjsonlogger import jsonlogger
from typing import Any, Dict, Optional

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            # this doesn't use record.created, so it's slightly off
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname
        
        # Add standard fields
        log_record['service'] = "backend_api"
        if not log_record.get('request_id'):
            log_record['request_id'] = None
        if not log_record.get('user_id'):
            log_record['user_id'] = None

def setup_logging(log_level: str = "INFO"):
    logger = logging.getLogger()
    logHandler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s %(service)s %(request_id)s %(user_id)s %(event)s %(data)s')
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Disable propagation for some noisy libraries if needed
    # logging.getLogger("uvicorn.access").propagate = False
    
logger = logging.getLogger("phantomnet")
