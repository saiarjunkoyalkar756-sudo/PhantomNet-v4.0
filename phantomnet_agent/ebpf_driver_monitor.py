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
eBPF-based Driver/Kernel Module Monitor

This module provides a monitor for tracking the loading and unloading of
Linux kernel modules using eBPF.

**Dependencies:**
- `bcc`: This module requires the BCC toolkit to be installed on the host system.
- `Linux Kernel Headers`: The appropriate kernel headers must be installed.
"""

import asyncio
import ctypes as ct
from typing import Optional

from utils.logger import get_logger
from phantomnet_core.os_adapter import get_os, OS_LINUX, supports_ebpf

# Conditional import for bcc
try:
    from bcc import BPF
    BCC_AVAILABLE = True
except ImportError:
    BCC_AVAILABLE = False
    print("BCC library not available. eBPF Driver Monitor will be disabled.")

# eBPF C code for monitoring kernel module operations
EBPF_PROGRAM = """
#include <linux/module.h>
#include <linux/sched.h>

struct data_t {
    u32 pid;
    char comm[TASK_COMM_LEN];
    char name[MODULE_NAME_LEN];
};

BPF_PERF_OUTPUT(events);

int trace_module_load(struct pt_regs *ctx, struct module *mod) {
    struct data_t data = {};
    data.pid = bpf_get_current_pid_tgid() >> 32;
    bpf_get_current_comm(&data.comm, sizeof(data.comm));
    bpf_probe_read_kernel(&data.name, sizeof(data.name), mod->name);
    events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}
"""


class EbpfDriverMonitor:
    """
    Monitors kernel module loading/unloading using eBPF.
    """

    def __init__(self):
        self.name = "ebpf_driver_monitor"
        self.logger = get_logger(f"phantomnet_agent.{self.name}")
        self.bpf = None
        self.stop_event = asyncio.Event()
        self._monitor_task: Optional[asyncio.Task] = None
        self.current_os = get_os()
        self.ebpf_supported = supports_ebpf() and BCC_AVAILABLE

    def _init_bpf(self):
        """
        Initializes the eBPF program.
        """
        if not self.ebpf_supported:
            self.logger.warning(
                f"eBPF is not supported on {self.current_os} or BCC is not available. EbpfDriverMonitor will not initialize."
            )
            return

        self.logger.info("Initializing eBPF driver monitor...")
        try:
            self.bpf = BPF(text=EBPF_PROGRAM)
            self.bpf.attach_kprobe(event="do_init_module", fn_name="trace_module_load")
            self.logger.info("eBPF program for driver monitoring initialized and hooks attached.")
        except Exception as e:
            self.logger.error(f"Failed to initialize eBPF for driver monitoring: {e}")
            self.bpf = None
            raise

    def _process_event(self, cpu, data, size):
        """
        Callback for processing events from the eBPF program.
        """
        class Data(ct.Structure):
            _fields_ = [
                ("pid", ct.c_uint32),
                ("comm", ct.c_char * 16),
                ("name", ct.c_char * 56), # MODULE_NAME_LEN
            ]

        event = ct.cast(data, ct.POINTER(Data)).contents
        details = {
            "pid": event.pid,
            "comm": event.comm.decode('utf-8', 'replace'),
            "module_name": event.name.decode('utf-8', 'replace'),
        }

        self.logger.info(
            f"eBPF kernel module load: {details['module_name']} by {details['comm']} (PID: {details['pid']})",
            extra={"event_type": "DRIVER_LOAD_EBPF", **details},
        )

    async def _monitor_loop(self):
        """
        The main event processing loop.
        """
        if not self.ebpf_supported or not self.bpf:
            self.logger.error("eBPF not initialized or not supported, cannot start monitoring.")
            return

        self.bpf["events"].open_perf_buffer(self._process_event)
        self.logger.info("eBPF perf buffer for driver events opened. Monitoring...")

        while not self.stop_event.is_set():
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.bpf.perf_buffer_poll, 100
                )
            except Exception as e:
                self.logger.error(f"Error during eBPF event polling: {e}")
                await asyncio.sleep(1)

    async def start(self):
        """Starts the eBPF driver monitoring background task."""
        if not self.ebpf_supported:
            self.logger.warning("EbpfDriverMonitor cannot start: eBPF not supported or BCC not available.")
            return

        if self._monitor_task is None:
            self.logger.info("EbpfDriverMonitor starting background task.")
            try:
                await asyncio.get_event_loop().run_in_executor(None, self._init_bpf)
                if self.bpf:
                    self._monitor_task = asyncio.create_task(self._monitor_loop())
            except Exception as e:
                self.logger.error(f"eBPF driver monitor startup failed: {e}")

    async def stop(self):
        """Stops the eBPF driver monitoring background task."""
        if not self.ebpf_supported:
            return

        self.logger.info("EbpfDriverMonitor stopping background task.")
        self.stop_event.set()
        if self._monitor_task:
            self._monitor_task.cancel()
            await asyncio.gather(self._monitor_task, return_exceptions=True)
            self._monitor_task = None
        if self.bpf:
            self.bpf.cleanup()
        self.logger.info("EbpfDriverMonitor background task stopped.")
