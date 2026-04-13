import asyncio
import psutil
from typing import Set, Dict, Any, Optional
from utils.logger import get_logger
from phantomnet_core.os_adapter import get_os, OS_LINUX, OS_WINDOWS, OS_TERMUX

class ProcessMonitor:
    """
    Monitors for new process creation and termination events.
    """
    def __init__(self, interval_seconds: int = 2):
        self.name = "process_monitor" # Name for self-healing to identify
        self.interval_seconds = interval_seconds
        self.logger = get_logger(f"phantomnet_agent.{self.name}")
        self.stop_event = asyncio.Event()
        self._monitor_task: Optional[asyncio.Task] = None
        self._known_pids: Set[int] = set()
        self._running: bool = False # Internal flag to track if the monitor is active
        self.current_os = get_os()
        self.monitor_method = ""
        if self.current_os == OS_WINDOWS:
            self.monitor_method = "psutil (Windows API)"
        elif self.current_os == OS_LINUX:
            self.monitor_method = "psutil (/proc filesystem)"
        elif self.current_os == OS_TERMUX:
            self.monitor_method = "psutil (/proc filesystem) + (Toybox if available)" # Toybox is an external dependency
        else:
            self.monitor_method = "psutil (generic)"
        self.logger.info(f"ProcessMonitor initialized for {self.current_os} using method: {self.monitor_method}")


    @property
    def running(self) -> bool:
        return self._running and self._monitor_task is not None and not self._monitor_task.done()

    @property
    def status(self) -> str:
        if self.running:
            return "running"
        elif self._monitor_task is not None and self._monitor_task.done():
            if self._monitor_task.exception():
                return f"failed ({self._monitor_task.exception().__class__.__name__})"
            return "stopped (completed)"
        return "stopped"

    def _get_process_details(self, pid: int) -> Dict[str, Any]:
        """Safely gets details for a given process ID."""
        try:
            p = psutil.Process(pid)
            return {
                "pid": p.pid,
                "name": p.name(),
                "cmdline": " ".join(p.cmdline()),
                "username": p.username(),
                "create_time": p.create_time()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {"pid": pid, "name": "unknown", "error": "Process disappeared or access denied"}

    async def _initialize_baseline(self):
        """Initializes the set of known PIDs at startup."""
        self.logger.info("Initializing process baseline...")
        self._known_pids = set(psutil.pids())
        self.logger.info(f"Initial baseline established with {len(self._known_pids)} processes.")

    async def _monitor_processes(self):
        """
        Periodically checks the process list and reports changes.
        """
        await self._initialize_baseline()

        while not self.stop_event.is_set():
            await asyncio.sleep(self.interval_seconds)
            try:
                current_pids = set(psutil.pids())

                new_pids = current_pids - self._known_pids
                terminated_pids = self._known_pids - current_pids

                for pid in new_pids:
                    details = self._get_process_details(pid)
                    self.logger.info(
                        f"New process created: {details.get('name')} (PID: {pid})",
                        extra={"event_type": "PROCESS_CREATE", **details}
                    )

                for pid in terminated_pids:
                    # For terminated processes, we can't get details anymore.
                    # A more advanced agent might cache details.
                    details = {"pid": pid}
                    self.logger.info(
                        f"Process terminated (PID: {pid})",
                        extra={"event_type": "PROCESS_TERMINATE", **details}
                    )

                self._known_pids = current_pids

            except Exception as e:
                self.logger.error(f"Error during process monitoring scan: {e}", exc_info=True)


    async def start(self):
        """Starts the process monitoring background task."""
        if self._monitor_task is None:
            self.logger.info("ProcessMonitor starting background task.")
            self._running = True # Set running flag before starting task
            self._monitor_task = asyncio.create_task(self._monitor_processes())

    async def stop(self):
        """Stops the process monitoring background task."""
        self.logger.info("ProcessMonitor stopping background task.")
        self.stop_event.set()
        if self._monitor_task:
            self._monitor_task.cancel()
            await asyncio.gather(self._monitor_task, return_exceptions=True)
            self._monitor_task = None
        self._running = False # Clear running flag after stopping task
        self.logger.info("ProcessMonitor background task stopped.")
