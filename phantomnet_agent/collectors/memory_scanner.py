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
Memory Scanner using YARA engine.

This module provides a collector that scans the memory of running processes
against a set of YARA rules to identify malicious patterns.

**Dependencies:**
- `yara-python`: The Python bindings for YARA.
- `psutil`: To iterate through running processes.
"""

import asyncio
import psutil
from typing import Dict, Any, Optional

from collectors.base import Collector
from bus.base import Transport
from utils.logger import get_logger
from phantomnet_core.os_adapter import get_os, OS_LINUX, OS_WINDOWS, OS_TERMUX

# Conditional import for yara-python
try:
    import yara
    YARA_AVAILABLE = True
except ImportError:
    YARA_AVAILABLE = False
    print("YARA Python library not available. Memory scanner will operate in limited mode or be disabled.")


class MemoryScanner(Collector):
    """
    Scans process memory with YARA rules.
    """

    def __init__(self, transport: Transport, config: Dict[str, Any]):
        super().__init__(transport, config)
        self.logger = get_logger("phantomnet_agent.memory_scanner")
        self.rules: Optional[yara.Rules] = None
        self.rule_path = self.config.get("rule_path", "yara_rules.yar")
        self.current_os = get_os()
        self.scanner_method = ""

        if self.current_os == OS_WINDOWS:
            self.scanner_method = "YARA (Windows WMI/pywin32 for memory access - theoretical)"
        elif self.current_os == OS_LINUX:
            self.scanner_method = "YARA (Volatility framework / direct process memory access)"
        elif self.current_os == OS_TERMUX:
            self.scanner_method = "Limited Mode (polling /proc/pid/maps - no YARA)"
        else:
            self.scanner_method = "Disabled (unsupported OS)"
        self.logger.info(f"MemoryScanner initialized for {self.current_os} using method: {self.scanner_method}")

    def _load_rules(self):
        """
        Loads YARA rules from the specified path.
        """
        if not YARA_AVAILABLE:
            self.logger.warning("YARA Python library not available, cannot load rules.")
            self.rules = None
            return

        try:
            self.logger.info(f"Loading YARA rules from {self.rule_path}")
            self.rules = yara.compile(filepath=self.rule_path)
            self.logger.info("YARA rules loaded successfully.")
        except yara.Error as e:
            self.logger.error(f"Failed to load YARA rules: {e}")
            self.rules = None

    async def _scan_process(self, pid: int):
        """
        Scans a single process.
        """
        if not YARA_AVAILABLE or not self.rules:
            self.logger.debug(f"YARA scanner not active, skipping scan for PID {pid}")
            return

        try:
            proc = psutil.Process(pid)
            matches = self.rules.match(pid=pid)

            for match in matches:
                details = {
                    "pid": pid,
                    "process_name": proc.name(),
                    "rule": match.rule,
                    "tags": match.tags,
                    "meta": match.meta,
                }
                self.logger.warning(
                    f"YARA match found in PID {pid} ({proc.name()}): {match.rule}",
                    extra={"event_type": "YARA_MATCH", **details},
                )
        except psutil.NoSuchProcess:
            pass  # Process might have terminated
        except psutil.AccessDenied:
            self.logger.debug(f"Access denied to process PID {pid}")
        except yara.Error as e:
            self.logger.error(f"Yara error scanning PID {pid}: {e}")
        except Exception as e:
            self.logger.error(f"Error scanning PID {pid}: {e}")

    async def _limited_scan(self):
        """
        Placeholder for limited memory scanning on platforms like Termux.
        """
        self.logger.info("Performing limited memory scan (placeholder)...")
        while self.running:
            # In a real scenario, this might involve parsing /proc/pid/maps
            # or looking for known suspicious strings in readable memory regions
            # if permitted by OS/privileges.
            if self.event_queue:
                self.event_queue.put_nowait({
                    "type": "memory_scan_limited",
                    "data": {
                        "timestamp": asyncio.get_event_loop().time(),
                        "message": "Simulated limited memory scan activity."
                    }
                })
            await asyncio.sleep(self.config.get("interval_seconds", 300))

    async def run(self):
        """
        Main loop for the collector.
        """
        self.logger.info("Memory Scanner started.")
        self._load_rules()

        if self.current_os == OS_TERMUX or not YARA_AVAILABLE:
            await self._limited_scan()
        else:
            if not self.rules:
                self.logger.error("No YARA rules loaded, Memory Scanner will not run in full mode.")
                return

            while self.running:
                for proc in psutil.process_iter(['pid']):
                    await self._scan_process(proc.info['pid'])
                
                interval = self.config.get("interval_seconds", 300)
                await asyncio.sleep(interval)

    async def stop(self):
        """
        Stops the collector.
        """
        self.running = False
        self.logger.info("Memory Scanner stopped.")
