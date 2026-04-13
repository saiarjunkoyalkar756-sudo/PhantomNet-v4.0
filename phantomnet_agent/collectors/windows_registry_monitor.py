# Copyright 2025 PhantomNet
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Windows Registry Monitor

This module provides a collector for monitoring changes to the Windows Registry.
This is a placeholder and is not yet implemented.

**Dependencies:**
- `pywin32`: This module will require the pywin32 library.
"""

import asyncio
from typing import Dict, Any

from collectors.base import Collector
from bus.base import Transport
from utils.logger import get_logger
from phantomnet_core.os_adapter import get_os, OS_WINDOWS


class WindowsRegistryMonitor(Collector):
    """
    Monitors Windows Registry for changes.
    """

    def __init__(self, transport: Transport, config: Dict[str, Any]):
        super().__init__(transport, config)
        self.logger = get_logger("phantomnet_agent.windows_registry_monitor")
        self.current_os = get_os()

    async def run(self):
        """
        Main loop for the collector.
        """
        if self.current_os != OS_WINDOWS:
            self.logger.warning(
                f"Windows Registry Monitor can only run on Windows (current OS: {self.current_os}). Collector will not start."
            )
            return

        self.logger.info("Windows Registry Monitor started.")
        # NOT IMPLEMENTED
        while self.running:
            self.logger.debug("Windows Registry Monitor is running (not implemented).")
            await asyncio.sleep(60)

    async def stop(self):
        """
        Stops the collector.
        """
        self.running = False
        self.logger.info("Windows Registry Monitor stopped.")
