import json
from loguru import logger

def serialize_log_record(record):
    """
    Serializes a Loguru record (dictionary) into a JSON string for structured logging.
    """
    # Loguru records are dict-like, but have attributes.
    # Convert to a standard dict first for cleaner serialization.
    log_dict = {
        "time": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "name": record["name"],
        "function": record["function"],
        "line": record["line"],
        "file": record["file"].name,
        "extra": record["extra"],
    }
    return json.dumps(log_dict)
