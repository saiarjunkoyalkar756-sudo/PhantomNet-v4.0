# phantomnet_agent/platform_compatibility/os_detector.py

import logging
from typing import Union, Optional

from utils.logger import get_logger
from shared.platform_utils import IS_LINUX, IS_WINDOWS, IS_TERMUX

# Import adapters
from .base_adapter import BaseAdapter
from .linux_adapter import LinuxAdapter
from .windows_adapter import WindowsAdapter
from .termux_adapter import TermuxAdapter

logger = get_logger(__name__)

class OSDetector:
    """
    Detects the operating system and loads the appropriate platform adapter.
    """
    def __init__(self):
        self._adapter: Optional[BaseAdapter] = None
        self._load_adapter()

    def _load_adapter(self):
        """Loads the correct adapter based on the detected OS."""
        if IS_LINUX:
            self._adapter = LinuxAdapter()
            logger.info("Loaded LinuxAdapter.")
        elif IS_WINDOWS:
            self._adapter = WindowsAdapter()
            logger.info("Loaded WindowsAdapter.")
        elif IS_TERMUX:
            self._adapter = TermuxAdapter()
            logger.info("Loaded TermuxAdapter.")
        else:
            logger.error("Unsupported operating system. No platform adapter loaded.")
            self._adapter = None

    def get_adapter(self) -> Optional[BaseAdapter]:
        """Returns the loaded platform adapter."""
        return self._adapter

# For direct testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running OSDetector example...")
    
    detector = OSDetector()
    adapter = detector.get_adapter()

    if adapter:
        logger.info(f"Active Adapter: {type(adapter).__name__}")
        # You can then call adapter-specific methods
        # Example (conceptual):
        # if isinstance(adapter, LinuxAdapter):
        #     asyncio.run(adapter.get_journal_logs("phantomnet-agent"))
        # elif isinstance(adapter, WindowsAdapter):
        #     asyncio.run(adapter.get_windows_event_logs("System", 5))
        # elif isinstance(adapter, TermuxAdapter):
        #     asyncio.run(adapter.get_netstat_info())
    else:
        logger.error("No adapter could be loaded.")
