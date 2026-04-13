import logging
import os
import json
import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import requests
import time
from threading import Thread, Lock

# --- Remote Logging Configuration ---
INGESTOR_URL = "http://localhost:8000/ingest"

# Define the directory for agent_output.log
LOG_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / ".." / "logs"
os.makedirs(LOG_DIR, exist_ok=True)
AGENT_OUTPUT_LOG_PATH = LOG_DIR / "agent_output.log"
ATTACKS_LOG_PATH = LOG_DIR / "attacks.log"

class HttpLogHandler(logging.Handler):
    """
    A custom log handler that sends log records to a remote HTTP endpoint.
    """
    def __init__(self, url: str, agent_id: Optional[str] = None):
        super().__init__()
        self.url = url
        self.agent_id = agent_id or "unknown_agent"
        self.session = requests.Session()
        # Add retry logic
        retries = requests.adapters.Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
        self.session.mount('http://', requests.adapters.HTTPAdapter(max_retries=retries))

    def format_to_telemetry(self, record: logging.LogRecord) -> Dict[str, Any]:
        """
        Transforms a LogRecord object into the TelemetryEvent schema.
        """
        # Base data structure
        data_payload = {
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
            "process": record.process,
            "thread": record.thread,
        }

        # Add any extra attributes from the log call into the nested 'data' field
        for key, value in record.__dict__.items():
            if key not in data_payload and not key.startswith('_') and key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename', 'levelname', 'levelno', 'msecs', 'msg', 'pathname', 'processName', 'relativeCreated', 'stack_info', 'threadName', 'name']:
                data_payload[key] = value
        
        # The main event type can be derived from the 'extra' data, or default to the logger name
        event_type = data_payload.pop('event_type', record.name)

        telemetry_event = {
            "agent_id": self.agent_id,
            "timestamp": datetime.datetime.fromtimestamp(record.created, tz=datetime.timezone.utc).isoformat(),
            "event_type": event_type,
            "data": data_payload
        }
        return telemetry_event

    def emit(self, record: logging.LogRecord):
        """

        Sends the log record to the remote ingestor.
        """
        try:
            telemetry_data = self.format_to_telemetry(record)
            self.session.post(self.url, json=telemetry_data, timeout=2)
        except requests.exceptions.RequestException:
            # If the remote endpoint is down, we don't want to spam the console.
            # The file logger will still capture the log. We can add more robust
            # offline caching logic here in the future.
            pass
        except Exception:
            # Catch any other exceptions during formatting or sending
            pass

class JsonFormatter(logging.Formatter):
    """
    A custom log formatter that outputs records as JSON objects.
    Includes additional context like agent_id and host.
    """
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None, style: str = '%', agent_id: Optional[str] = None, host: Optional[str] = None):
        super().__init__(fmt, datefmt, style)
        self.agent_id = agent_id
        self.host = host

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
            "message": record.getMessage(),
            "process": record.process,
            "thread": record.thread,
        }

        if self.agent_id:
            log_record["agent_id"] = self.agent_id
        if self.host:
            log_record["host"] = self.host
        
        # Add any extra attributes attached to the record
        for key, value in record.__dict__.items():
            if key not in log_record and not key.startswith('_') and key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename', 'levelname', 'levelno', 'msecs', 'msg', 'pathname', 'processName', 'relativeCreated', 'stack_info', 'threadName']:
                log_record[key] = value

        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_record["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(log_record)


_loggers: Dict[str, logging.Logger] = {} # Cache for loggers
_logger_lock = Lock()

def get_logger(name: str, level: int = logging.INFO, agent_id: Optional[str] = None, host: Optional[str] = None) -> logging.Logger:
    """
    Factory function to get a pre-configured logger instance.
    Logs structured JSON to console, a local file, and a remote HTTP endpoint.
    """
    with _logger_lock:
        if name in _loggers:
            return _loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False

        if logger.hasHandlers():
            logger.handlers.clear()

        # Get a consistent agent_id for the logger session
        session_agent_id = agent_id or os.environ.get("PHANTOMNET_AGENT_ID", "default-agent")

        # --- Handler 1: Remote HTTP Handler ---
        http_handler = HttpLogHandler(url=INGESTOR_URL, agent_id=session_agent_id)
        http_handler.setLevel(logging.INFO) # Send INFO and above to the backend
        logger.addHandler(http_handler)

        # --- Handler 2 & 3: Local File and Console Handlers ---
        json_formatter = JsonFormatter(agent_id=session_agent_id, host=host)

        # Console handler for local debugging
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(json_formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

        # File handler for local persistence
        file_handler = logging.FileHandler(AGENT_OUTPUT_LOG_PATH)
        file_handler.setFormatter(json_formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

        _loggers[name] = logger
        return logger

def log_event(event_data: Dict[str, Any]):
    """
    Writes a raw event dictionary to 'attacks.log' AND sends it to the backend.
    """
    # Also log to local file for redundancy
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(ATTACKS_LOG_PATH, "a") as f:
        event_data["timestamp"] = datetime.datetime.now().isoformat()
        f.write(json.dumps(event_data) + "\n")

    # Send to backend via the standard logger
    # We wrap it in a log call at ERROR level to ensure it gets sent,
    # with a special event_type.
    event_logger = get_logger("event.raw_attack")
    event_logger.error(event_data.get("summary", "Raw attack event"), extra=event_data)


# Example usage (for testing this module directly)
if __name__ == "__main__":
    print(f"Testing logger. Sending logs to {INGESTOR_URL}")
    # Set an env var for agent_id for testing
    os.environ["PHANTOMNET_AGENT_ID"] = "test-agent-from-main"

    test_logger = get_logger("test_app", level=logging.DEBUG)
    
    print("\n--- Sending a standard log message ---")
    test_logger.info("This is an info message from the test app.")
    
    print("\n--- Sending a log with 'extra' data (will be nested) ---")
    test_logger.warning("This is a warning.", extra={"custom_field": "value1", "some_id": 456})

    print("\n--- Sending a log with 'event_type' in extra data ---")
    test_logger.info("This is a specific event type.", extra={"event_type": "USER_LOGIN_SUCCESS", "username": "testuser"})

    print(f"\nCheck {AGENT_OUTPUT_LOG_PATH} for local file output.")
    print("Check the telemetry-ingestor service logs to see the received events.")
    # Give the background thread a moment to send the logs
    time.sleep(2)
    print("\nTest complete.")