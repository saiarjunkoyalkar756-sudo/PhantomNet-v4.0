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
eBPF-based Process Monitor for Kernel-Level Visibility

This module provides a process monitor that leverages eBPF (Extended Berkeley
Packet Filter) to gain deep, kernel-level insights into process creation
and execution. It is designed for modern Linux systems and provides a
highly efficient and low-overhead way to monitor system activity.

**Dependencies:**
- `bcc`: This module requires the BCC toolkit to be installed on the host system.
  This is more than a `pip install`. Please refer to the BCC installation guide
  for your Linux distribution.
- `Linux Kernel Headers`: The appropriate kernel headers must be installed for
  BCC to compile the eBPF programs.

**Note:** This monitor will not run without the above dependencies.
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
    print("BCC library not available. eBPF Process Monitor will be disabled.")


# eBPF C code for monitoring process execution
EBPF_PROGRAM = """
#include <linux/sched.h>

// Data structure to be sent from kernel to user space
struct data_t {
    u32 pid;
    u32 tgid;
    int retval;
    char comm[TASK_COMM_LEN];
    char filename[128];
};

// Perf output channel
BPF_PERF_OUTPUT(events);

// Hook into the execve syscall
int syscall__execve(struct pt_regs *ctx,
                   const char __user *filename,
                   const char __user *const __user *__argv,
                   const char __user *const __user *__envp)
{
    struct data_t data = {};
    struct task_struct *task;

    task = (struct task_struct *)bpf_get_current_task();
    data.pid = task->pid;
    data.tgid = task->tgid;

    bpf_probe_read_user_str(&data.comm, sizeof(data.comm), task->comm);
    bpf_probe_read_user_str(&data.filename, sizeof(data.filename), filename);

    // We can't get the return value here, so we trace the exit
    // of the syscall instead.

    return 0;
}

// Hook into the return of the execve syscall
int ret_syscall__execve(struct pt_regs *ctx)
{
    struct data_t data = {};
    struct task_struct *task;

    // We have to re-read the data here as we are in a new context
    task = (struct task_struct *)bpf_get_current_task();
    data.pid = task->pid;
    data.tgid = task->tgid;
    data.retval = PT_REGS_RC(ctx);

    bpf_probe_read_user_str(&data.comm, sizeof(data.comm), task->comm);
    // The filename is not available in the return context, so we can't log it here.
    // A more advanced implementation might store it in a map.

    events.perf_submit(ctx, &data, sizeof(data));

    return 0;
}
"""


class EbpfProcessMonitor:
    """
    Monitors process execution using eBPF.
    """

    def __init__(self):
        self.name = "ebpf_process_monitor"
        self.logger = get_logger(f"phantomnet_agent.{self.name}")
        self.bpf = None
        self.stop_event = asyncio.Event()
        self._monitor_task: Optional[asyncio.Task] = None
        self.current_os = get_os()
        self.ebpf_supported = supports_ebpf() and BCC_AVAILABLE

    def _init_bpf(self):
        """
        Initializes the eBPF program.
        This is a blocking operation and should be run in an executor.
        """
        if not self.ebpf_supported:
            self.logger.warning(
                f"eBPF is not supported on {self.current_os} or BCC is not available. EbpfProcessMonitor will not initialize."
            )
            return

        self.logger.info("Initializing eBPF process monitor...")
        try:
            self.bpf = BPF(text=EBPF_PROGRAM)
            execve_fnname = self.bpf.get_syscall_fnname("execve")
            self.bpf.attach_kprobe(event=execve_fnname, fn_name="syscall__execve")
            self.bpf.attach_kretprobe(event=execve_fnname, fn_name="ret_syscall__execve")
            self.logger.info("eBPF program initialized and hooks attached.")
        except Exception as e:
            self.logger.error(f"Failed to initialize eBPF: {e}")
            self.logger.error(
                "Please ensure that the BCC toolkit and kernel headers are installed."
            )
            self.bpf = None
            raise

    def _process_event(self, cpu, data, size):
        """
        Callback for processing events from the eBPF program.
        """
        # The data structure in Python must match the C struct
        class Data(ct.Structure):
            _fields_ = [
                ("pid", ct.c_uint32),
                ("tgid", ct.c_uint32),
                ("retval", ct.c_int),
                ("comm", ct.c_char * 16), # TASK_COMM_LEN
                ("filename", ct.c_char * 128),
            ]

        event = ct.cast(data, ct.POINTER(Data)).contents
        details = {
            "pid": event.pid,
            "tgid": event.tgid,
            "comm": event.comm.decode('utf-8', 'replace'),
            "filename": event.filename.decode('utf-8', 'replace'),
            "retval": event.retval,
        }

        self.logger.info(
            f"eBPF process exec: {details['comm']} (PID: {details['pid']})",
            extra={"event_type": "PROCESS_EXEC_EBPF", **details},
        )

    async def _monitor_loop(self):
        """
        The main event processing loop.
        """
        if not self.ebpf_supported or not self.bpf:
            self.logger.error("eBPF not initialized or not supported, cannot start monitoring.")
            return

        self.bpf["events"].open_perf_buffer(self._process_event)
        self.logger.info("eBPF perf buffer opened. Monitoring for events...")

        while not self.stop_event.is_set():
            try:
                # Poll for events. This is a blocking call, so we run it in an
                # executor to avoid blocking the asyncio event loop.
                await asyncio.get_event_loop().run_in_executor(
                    None, self.bpf.perf_buffer_poll, 100
                )
            except Exception as e:
                self.logger.error(f"Error during eBPF event polling: {e}")
                await asyncio.sleep(1) # Avoid tight loop on error

    async def start(self):
        """Starts the eBPF process monitoring background task."""
        if not self.ebpf_supported:
            self.logger.warning("EbpfProcessMonitor cannot start: eBPF not supported or BCC not available.")
            return

        if self._monitor_task is None:
            self.logger.info("EbpfProcessMonitor starting background task.")
            try:
                # Initialization is blocking, run it in an executor
                await asyncio.get_event_loop().run_in_executor(None, self._init_bpf)
                if self.bpf:
                    self._monitor_task = asyncio.create_task(self._monitor_loop())
            except Exception as e:
                self.logger.error(f"eBPF startup failed: {e}")


    async def stop(self):
        """Stops the eBPF process monitoring background task."""
        if not self.ebpf_supported:
            return

        self.logger.info("EbpfProcessMonitor stopping background task.")
        self.stop_event.set()
        if self._monitor_task:
            self._monitor_task.cancel()
            await asyncio.gather(self._monitor_task, return_exceptions=True)
            self._monitor_task = None
        if self.bpf:
            self.bpf.cleanup()
        self.logger.info("EbpfProcessMonitor background task stopped.")

