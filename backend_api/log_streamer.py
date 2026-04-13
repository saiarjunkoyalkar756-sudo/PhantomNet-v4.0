import asyncio
import json
import os
from datetime import datetime
from typing import AsyncGenerator, List, Tuple
from watchfiles import awatch

# Define a maximum buffer size for logs to prevent excessive memory usage
MAX_LOG_BUFFER_SIZE = 1000

# In-memory buffer for logs, useful for new connections to get some history
log_buffer = asyncio.Queue(maxsize=MAX_LOG_BUFFER_SIZE)

async def _tail_file(filepath: str, source_type: str) -> AsyncGenerator[str, None]:
    """
    Asynchronously tails a file, yielding new lines as they appear.
    """
    # Ensure the file exists before attempting to open
    if not os.path.exists(filepath):
        print(f"Warning: Log file not found, creating it: {filepath}")
        with open(filepath, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] INFO: Log file created for {source_type}\n")
        
    
    # Start by reading the last few lines to provide some initial context
    try:
        with open(filepath, 'r') as f:
            f.seek(0, os.SEEK_END)
            f_size = f.tell()
            if f_size > 1024 * 10:  # Read last 10KB
                f.seek(max(0, f_size - 1024 * 10), os.SEEK_SET)
            for line in f.readlines():
                yield line.strip()
    except Exception as e:
        print(f"Error reading initial lines from {filepath}: {e}")

    async for changes in awatch(filepath):
        for change_type, changed_path in changes:
            if change_type.name == 'modified' or change_type.name == 'added':
                try:
                    # Open the file and seek to the end to read only new content
                    with open(changed_path, 'r') as f:
                        f.seek(0, os.SEEK_END)
                        # Keep track of the file size to detect truncations
                        current_file_size = f.tell()

                        # If the file size has decreased, it was likely truncated or rotated
                        # In such cases, we should re-read from the beginning or a safe point.
                        # For simplicity, we'll re-read the last few lines as if it's a new file.
                        if current_file_size < getattr(f, '_prev_size', 0):
                            print(f"File {changed_path} truncated, re-tailing...")
                            f.seek(max(0, current_file_size - 1024 * 10), os.SEEK_SET) # Read last 10KB of new file
                        
                        setattr(f, '_prev_size', current_file_size) # Store current size

                        for line in f:
                            yield line.strip()
                except Exception as e:
                    print(f"Error reading new lines from {changed_path}: {e}")

async def _parse_log_line(line: str, source: str) -> dict:
    """
    Parses a log line and formats it into a standardized dictionary.
    Attempts to extract timestamp, severity, and message.
    If parsing fails, it defaults to a generic format.
    """
    timestamp = datetime.now().isoformat()
    severity = "INFO"
    message = line

    # Basic attempt to parse common log formats
    # Example: [2023-10-27 10:00:00,123] INFO: This is a log message
    # Example: 2023-10-27T10:00:00.123Z - INFO - This is another message
    
    # Regex could be more robust, but simple string checks for common patterns
    if "[" in line and "]" in line and ":" in line:
        try:
            parts = line.split("]", 1)
            ts_part = parts[0].lstrip("[")
            if "," in ts_part: # Handle Python logging format with milliseconds
                ts_part = ts_part.split(",")[0]
            timestamp_obj = datetime.fromisoformat(ts_part.replace(" ", "T")) # Assume ISO-like
            timestamp = timestamp_obj.isoformat()

            if len(parts) > 1:
                msg_part = parts[1].strip()
                if ":" in msg_part:
                    level_msg = msg_part.split(":", 1)
                    if len(level_msg) > 1:
                        potential_severity = level_msg[0].strip().upper()
                        if potential_severity in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                            severity = potential_severity
                            message = level_msg[1].strip()
                        else:
                            message = msg_part
                    else:
                        message = msg_part
                else:
                    message = msg_part
        except ValueError:
            pass # Fallback to default if parsing fails
    
    # If it's a JSON line, parse it directly
    if line.strip().startswith('{') and line.strip().endswith('}'):
        try:
            json_log = json.loads(line)
            return {
                "source": json_log.get("source", source),
                "timestamp": json_log.get("timestamp", timestamp),
                "message": json_log.get("message", line),
                "severity": json_log.get("severity", severity).upper()
            }
        except json.JSONDecodeError:
            pass # Not a valid JSON log, proceed with text parsing

    return {
        "source": source,
        "timestamp": timestamp,
        "message": message,
        "severity": severity
    }

async def async_log_streamer(
    log_file_paths: List[Tuple[str, str]]
) -> AsyncGenerator[str, None]:
    """
    Continuously monitors specified log files and yields new log entries as JSON strings.
    Each log_file_paths item should be a tuple of (filepath, source_name_for_log).
    """
    tail_tasks = []
    # Store the last read positions for each file to handle initial read and re-reads
    file_read_positions = {path: 0 for path, _ in log_file_paths}

    # Initial read of existing content
    for filepath, source_type in log_file_paths:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    for line in f:
                        parsed_log = await _parse_log_line(line.strip(), source_type)
                        json_log = json.dumps(parsed_log)
                        try:
                            await log_buffer.put_nowait(json_log)
                        except asyncio.QueueFull:
                            # Remove oldest item to make space for new
                            await log_buffer.get()
                            await log_buffer.put_nowait(json_log)
            except Exception as e:
                print(f"Error during initial read of {filepath}: {e}")

    # Start tailing tasks for each file
    for filepath, source_type in log_file_paths:
        # Create a task for each file to tail it concurrently
        async def _per_file_tailer(fp, st):
            async for line in _tail_file(fp, st):
                parsed_log = await _parse_log_line(line, st)
                json_log = json.dumps(parsed_log)
                try:
                    await log_buffer.put_nowait(json_log)
                except asyncio.QueueFull:
                    # Remove oldest item to make space for new
                    await log_buffer.get() # Discard oldest
                    await log_buffer.put_nowait(json_log) # Add newest

        tail_tasks.append(asyncio.create_task(_per_file_tailer(filepath, source_type)))

    # Keep a task running to yield from the buffer
    while True:
        # Yield logs from the buffer to any connected clients
        try:
            log_entry = await log_buffer.get()
            yield log_entry
        except Exception as e:
            print(f"Error yielding from log buffer: {e}")
            await asyncio.sleep(1) # Prevent tight loop on error
