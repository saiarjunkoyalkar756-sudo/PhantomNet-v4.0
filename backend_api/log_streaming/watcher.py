import asyncio
from .transport import ws_transport
from loguru import logger
import aiofiles
import os
from datetime import datetime, timezone

class FileWatcher:
    """
    Asynchronously watches a file for new lines and sends them to a transport.
    """
    def __init__(self, filepath: str, transport):
        self.filepath = filepath
        self.transport = transport

    async def watch(self):
        """
        Starts watching the file for new lines.
        """
        logger.info(f"Starting to watch file: {self.filepath}")
        try:
            async with aiofiles.open(self.filepath, mode='r') as f:
                # Go to the end of the file
                await f.seek(0, 2)
                while True:
                    line = await f.readline()
                    if not line:
                        await asyncio.sleep(0.5)
                        continue
                    
                    # Create a mock log record to send to the transport
                    mock_record = {
                        "time": datetime.now(timezone.utc),
                        "level": {"name": "INFO"},
                        "message": line.strip(),
                        "name": f"filewatcher:{os.path.basename(self.filepath)}",
                        "extra": {},
                    }
                    await self.transport.send(mock_record)

        except FileNotFoundError:
            logger.warning(f"File not found for watching: {self.filepath}. The watcher will not start.")
        except Exception as e:
            logger.error(f"Error while watching file {self.filepath}: {e}")

async def start_watchers():
    """
    Initializes and starts watchers for specified log files.
    """
    # In a real application, these paths would come from a configuration file.
    log_files_to_watch = [
        "backend.log", # The main backend log file
        # Add paths to agent logs here if they are accessible
    ]

    watchers = [FileWatcher(filepath, ws_transport) for filepath in log_files_to_watch]
    tasks = [asyncio.create_task(watcher.watch()) for watcher in watchers]
    
    # This will run the watchers indefinitely. In a real app, you might
    # want to manage these tasks more carefully.
    await asyncio.gather(*tasks)
