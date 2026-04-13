import asyncio
import logging
import json
from datetime import datetime, timezone
import os
import sys
from loguru import logger

# 1. Create a queue for inter-thread/inter-process communication
log_queue = asyncio.Queue()

# 2. Define the JSON log format
def serialize(record):
    """Custom serializer to format log records as JSON."""
    subset = {
        "timestamp": datetime.fromtimestamp(record["time"].timestamp(), tz=timezone.utc).isoformat(),
        "level": record["level"].name,
        "name": record["name"],
        "message": record["message"],
        "service_name": os.getenv("SERVICE_NAME", "unknown_service"),
        "environment": os.getenv("ENVIRONMENT", "development"),
    }
    # Add exception details if present
    if record["exception"]:
        subset["exception"] = {
            "type": record["exception"].type.__name__,
            "value": str(record["exception"].value),
            "traceback": bool(record["exception"].traceback),
        }
    return json.dumps(subset)

def json_formatter(record):
    """Formatter function to serialize the record and add a newline."""
    record["extra"]["serialized"] = serialize(record)
    return "{extra[serialized]}\n"

# 3. Define the asynchronous sink that consumes from the queue
async def async_log_sink():
    """Coroutine that reads from the log queue and writes to stdout."""
    while True:
        try:
            log_record = await log_queue.get()
            sys.stdout.write(log_record)
            sys.stdout.flush()
        except asyncio.CancelledError:
            break
        except Exception as e:
            # Handle potential errors in the logging sink itself
            print(f"CRITICAL: Error in async_log_sink: {e}", file=sys.stderr)

# 4. Define a synchronous sink function to put logs into the queue
# This function is thread-safe because it uses the asyncio.Queue which is designed for this.
def queue_sink(message):
    """
    A synchronous sink that puts log messages into the asyncio Queue.
    This is safe to call from any thread.
    """
    log_queue.put_nowait(message)

async def broadcast_logs_from_queue(log_queue: asyncio.Queue):
    """
    A coroutine that consumes logs from the global log queue and broadcasts them via WebSocket.
    """
    from ..gateway_service.log_broadcaster import log_broadcaster
    while True:
        try:
            log_record = await log_queue.get()
            await log_broadcaster.broadcast(log_record)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in log broadcasting task: {e}", exc_info=True)


# 5. The main setup function
def setup_logging(name: str = "phantomnet_backend", level: str = "INFO"):
    """
    Configures Loguru to use a thread-safe, asynchronous JSON logging setup.
    """
    # Remove default handler to prevent duplicate logs
    logger.remove()

    # Configure the main logger to use the queue sink
    # This ensures that all logging calls are non-blocking and thread-safe.
    logger.add(
        queue_sink,
        level=level.upper(),
        format=json_formatter,
        enqueue=False, # Loguru's enqueue is not needed as we use our own asyncio queue
        serialize=True # Pass the full record to the sink for serialization
    )
    
    # Also add a standard sink for debugging in case the async sink fails
    logger.add(
        sys.stderr,
        level="ERROR",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    return logger

# Example of how to start the logging task in your main application's lifespan
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup
#     setup_logging()
#     logging_task = asyncio.create_task(async_log_sink())
#     yield
#     # Shutdown
#     logging_task.cancel()
#     try:
#         await logging_task
#     except asyncio.CancelledError:
#         pass