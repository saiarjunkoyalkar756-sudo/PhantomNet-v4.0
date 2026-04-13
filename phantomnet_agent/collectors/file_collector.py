import asyncio
import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from pathlib import Path
import hashlib

if TYPE_CHECKING:
    from orchestrator import Orchestrator

# Requires watchdog for real-time monitoring, but for simplicity, we'll do periodic scans
# pip install watchdog
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logging.warning("watchdog library not found. File changes will be detected by periodic scanning instead of real-time monitoring.")

from collectors.base import Collector
from schemas.events import FileEvent

logger = logging.getLogger(__name__)

class FileCollector(Collector):
    """
    Collects information about file system changes (creation, modification, deletion).
    Can use watchdog for real-time monitoring or fall back to periodic scanning.
    """
    def __init__(self, orchestrator: "Orchestrator", adapter: Any, config: Dict[str, Any]):
        super().__init__(orchestrator, adapter, config)
        self.paths: List[Path] = [Path(p).resolve() for p in self.config.get("paths", [])]
        self.interval_seconds = self.config.get("interval_seconds", 60)
        self.known_files: Dict[Path, Dict[str, Any]] = {}
        self.observer: Optional[Observer] = None

        if WATCHDOG_AVAILABLE:
            self.event_handler = FileSystemEventHandler()
            self.event_handler.on_created = self._on_file_event("created")
            self.event_handler.on_deleted = self._on_file_event("deleted")
            self.event_handler.on_modified = self._on_file_event("modified")
            self.event_handler.on_moved = self._on_file_event("moved")

    async def run(self):
        logger.info(f"Starting FileCollector for paths: {self.paths}")
        if not self.paths:
            logger.warning("No paths configured for FileCollector. It will not run.")
            return

        if WATCHDOG_AVAILABLE:
            self.observer = Observer()
            for path in self.paths:
                if path.is_dir():
                    self.observer.schedule(self.event_handler, str(path), recursive=True)
            self.observer.start()
            logger.info("FileCollector using watchdog for real-time monitoring.")
        else:
            logger.info("FileCollector using periodic scanning.")
            # Initial scan to populate known_files
            await self._periodic_scan()

        while self.running:
            if not WATCHDOG_AVAILABLE:
                await self._periodic_scan()
            await asyncio.sleep(self.interval_seconds)

    async def stop(self):
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
        logger.info("FileCollector stopped.")

    def _on_file_event(self, operation: str):
        """Helper to create event handlers for watchdog."""
        async def handler(event):
            # Watchdog events don't provide all file details, so we fetch them
            # This can be tricky for deleted files, where path might not exist
            path = Path(event.src_path)
            file_info = self._get_file_info(path)
            if not file_info: # File might have been deleted before we could get info
                file_info = {"path": str(path), "file_type": "unknown", "size": 0, "hash": "N/A"}

            event_payload = {
                "agent_id": "agent-id-placeholder",
                "timestamp": asyncio.get_event_loop().time(),
                "payload": {
                    "path": str(path),
                    "operation": operation,
                    "file_type": file_info.get("file_type"),
                    "size": file_info.get("size"),
                    "hash": file_info.get("hash")
                }
            }
            file_event = FileEvent(**event_payload)
            await self.orchestrator.ingest_event(file_event.dict())
            logger.debug(f"File event ({operation}): {path}")
        return handler

    async def _periodic_scan(self):
        """Performs a periodic scan of configured directories."""
        current_files = {}
        for base_path in self.paths:
            if not base_path.is_dir():
                continue
            for path in base_path.rglob("*"): # Recursive glob
                if path.is_file():
                    file_info = self._get_file_info(path)
                    if file_info:
                        current_files[path] = file_info

        # Detect changes
        # Created/Modified
        for path, info in current_files.items():
            if path not in self.known_files:
                await self._send_file_event("created", path, info)
            elif info["hash"] != self.known_files[path]["hash"] or info["size"] != self.known_files[path]["size"]:
                await self._send_file_event("modified", path, info)
        
        # Deleted
        for path in self.known_files:
            if path not in current_files:
                await self._send_file_event("deleted", path, {"path": str(path), "file_type": "unknown"})

        self.known_files = current_files
        logger.debug(f"Completed periodic file scan. {len(self.known_files)} files known.")


    def _get_file_info(self, path: Path) -> Optional[Dict[str, Any]]:
        """Gets metadata and hash for a given file."""
        try:
            stat = path.stat()
            file_type = "file"
            if path.is_symlink(): file_type = "symlink"
            elif path.is_dir(): file_type = "directory" # Should not happen with rglob("*") filter
            
            # Calculate hash for files
            file_hash = "N/A"
            if path.is_file():
                hasher = hashlib.sha256()
                with open(path, 'rb') as f:
                    # Read in chunks to handle large files
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
                file_hash = hasher.hexdigest()

            return {
                "path": str(path),
                "file_type": file_type,
                "size": stat.st_size,
                "hash": file_hash
            }
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error getting file info for {path}: {e}")
            return None

    async def _send_file_event(self, operation: str, path: Path, file_info: Dict[str, Any]):
        """Sends a FileEvent via the orchestrator."""
        event_payload = {
            "agent_id": "agent-id-placeholder",
            "timestamp": asyncio.get_event_loop().time(),
            "payload": {
                "path": str(path),
                "operation": operation,
                "file_type": file_info.get("file_type", "unknown"),
                "size": file_info.get("size"),
                "hash": file_info.get("hash")
            }
        }
        file_event = FileEvent(**event_payload)
        await self.orchestrator.ingest_event(file_event.dict())


if __name__ == '__main__':
    async def run_example():
        logging.basicConfig(level=logging.DEBUG)
        
        class MockTransport(Transport):
            async def send_event(self, topic: str, payload: Dict[str, Any]) -> None:
                # print(f"MockTransport: Sending event to {topic}: {payload['event_type']}")
                # print(FileEvent(**payload).json(indent=2)) # Validate and print
                pass
            async def receive_commands(self, topic: str):
                yield

        mock_transport = MockTransport(endpoint="http://mock-endpoint") # endpoint is not used by MockTransport

        # Create a temporary directory for testing
        test_dir = Path("./temp_file_collector_test")
        test_dir.mkdir(exist_ok=True)
        (test_dir / "test_file_1.txt").write_text("initial content")
        (test_dir / "subdir").mkdir(exist_ok=True)
        (test_dir / "subdir" / "test_file_2.txt").write_text("initial content 2")

        config = {"enabled": True, "interval_seconds": 5, "paths": [str(test_dir)]}
        collector = FileCollector(mock_transport, config)

        try:
            await collector.start()
            print("FileCollector started. Waiting for changes...")
            await asyncio.sleep(1) # Give it a moment to do initial scan

            print("\nModifying test_file_1.txt...")
            (test_dir / "test_file_1.txt").write_text("new content")
            await asyncio.sleep(2) # Give watchdog/scanner time to detect

            print("\nCreating new_file.log...")
            (test_dir / "new_file.log").write_text("log entry 1")
            await asyncio.sleep(2)

            print("\nDeleting test_file_2.txt...")
            (test_dir / "subdir" / "test_file_2.txt").unlink()
            await asyncio.sleep(2)

            print("\nStopping collector...")

        finally:
            await collector.stop()
            # Clean up temporary directory
            import shutil
            shutil.rmtree(test_dir)
            print("Test directory cleaned up.")

    try:
        asyncio.run(run_example())
    except ImportError:
        print("\nERROR: 'watchdog' is not installed. Please install it: pip install watchdog")
    except Exception as e:
        print(f"\nAn error occurred during FileCollector example execution: {e}")

