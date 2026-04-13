# shared/platform_utils.py

import platform
import os
import sys
import logging
import subprocess
from typing import Dict, Any

logger = logging.getLogger(__name__)

# --- Constants for OS types ---
OS_WINDOWS = "windows"
OS_LINUX = "linux"
OS_TERMUX = "termux"
OS_UNKNOWN = "unknown"

# --- Global Capability Flags (populated on import) ---
IS_WINDOWS = False
IS_LINUX = False
IS_TERMUX = False
IS_ROOT = False
HAS_PCAP = False
HAS_EBPF = False
CAN_BIND_LOW_PORTS = False
ARCH = platform.machine().lower()
PLATFORM_INFO = {}

# --- Helper Functions ---
def _detect_os_type() -> str:
    """Detects the operating system type."""
    if os.name == 'nt':
        return OS_WINDOWS
    elif os.name == 'posix':
        if "ANDROID_ROOT" in os.environ or (platform.system() == 'Linux' and 'com.termux' in os.getenv('PREFIX', '')):
            return OS_TERMUX
        return OS_LINUX
    return OS_UNKNOWN

def _is_root_user() -> bool:
    """Checks if the current process is running with root/Administrator privileges."""
    if CURRENT_OS_TYPE == OS_WINDOWS:
        try:
            # Check if current user is admin on Windows
            return os.getuid() == 0  # This will fail on Windows, handled by the except block
        except AttributeError:
            # For Windows, check if process is elevated
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
    else: # Linux/Termux
        return os.geteuid() == 0

def _check_command_exists(command: str) -> bool:
    """Checks if a given command is available in the system's PATH."""
    return bool(subprocess.run(['which', command], capture_output=True, text=True).stdout)

def _detect_system_capabilities() -> Dict[str, Any]:
    """Detects various system capabilities."""
    caps = {
        "os_type": CURRENT_OS_TYPE,
        "os_name": platform.system(),
        "architecture": ARCH,
        "is_root": IS_ROOT,
        "python_version": platform.python_version(),
        "has_pcap": False,
        "has_ebpf": False,
        "can_bind_low_ports": False,
        "has_systemctl": False,
        "has_nssm": False, # Windows service manager
        "has_sc_exe": False, # Windows service manager
        "has_npcap": False, # Windows packet capture driver
        "has_wmi": False, # Windows Management Instrumentation
        "has_pywin32": False, # Python for Windows extensions
        "has_toybox": False, # Termux utility set
        "supports_raw_sockets": False,
        "safe_mode": False, # Default to False, can be overridden by env var or config
    }

    # OS-specific checks
    if CURRENT_OS_TYPE == OS_WINDOWS:
        try:
            import win32serviceutil # pywin32 check
            caps["has_pywin32"] = True
        except ImportError:
            pass
        try:
            import wmi # wmi check
            caps["has_wmi"] = True
        except ImportError:
            pass
        caps["has_sc_exe"] = _check_command_exists("sc.exe")
        # Npcap detection is tricky without actively trying to use it.
        # For now, we assume if Npcap is installed, Scapy can use it.
        # A more robust check might involve checking device drivers.
        caps["has_npcap"] = True # Assume true if Scapy is installed and run with admin
        caps["can_bind_low_ports"] = IS_ROOT # Admin can bind low ports on Windows
        caps["supports_raw_sockets"] = IS_ROOT # Admin typically gets raw socket access
    elif CURRENT_OS_TYPE == OS_LINUX:
        caps["has_systemctl"] = _check_command_exists("systemctl")
        caps["has_pcap"] = _check_command_exists("libpcap") # Placeholder, actual check needs Python pcap binding
        caps["can_bind_low_ports"] = IS_ROOT or os.path.exists("/proc/sys/net/ipv4/ip_unprivileged_port_start") and int(open("/proc/sys/net/ipv4/ip_unprivileged_port_start").read()) <= 1024
        caps["supports_raw_sockets"] = True # Linux generally supports raw sockets, but requires CAP_NET_RAW or root
        # eBPF check - presence of libbpf or bcc tools
        caps["has_ebpf"] = _check_command_exists("bpftool") or _check_command_exists("bcc")
    elif CURRENT_OS_TYPE == OS_TERMUX:
        caps["has_pcap"] = _check_command_exists("libpcap") # Termux has libpcap package
        caps["has_toybox"] = _check_command_exists("toybox")
        # Termux generally restricts raw sockets. We'll assume false for unprivileged users.
        caps["supports_raw_sockets"] = False # Very restricted on Termux
        caps["can_bind_low_ports"] = False # Usually not possible without root/special setup
        caps["has_ebpf"] = False # Not typically supported on Termux kernel

    # Check for SAFE_MODE override
    if os.getenv("PHANTOMNET_SAFE_MODE", "false").lower() == "true":
        caps["safe_mode"] = True
        logger.warning("PHANTOMNET_SAFE_MODE environment variable is set to true. Operating in safe mode.")

    return caps

# --- Initialize Global Variables ---
CURRENT_OS_TYPE = _detect_os_type()
IS_ROOT = _is_root_user()
PLATFORM_INFO = _detect_system_capabilities()

IS_WINDOWS = (CURRENT_OS_TYPE == OS_WINDOWS)
IS_LINUX = (CURRENT_OS_TYPE == OS_LINUX)
IS_TERMUX = (CURRENT_OS_TYPE == OS_TERMUX)

HAS_PCAP = PLATFORM_INFO["has_pcap"]
HAS_EBPF = PLATFORM_INFO["has_ebpf"]
CAN_BIND_LOW_PORTS = PLATFORM_INFO["can_bind_low_ports"]
SUPPORTS_RAW_SOCKETS = PLATFORM_INFO["supports_raw_sockets"]
SAFE_MODE = PLATFORM_INFO["safe_mode"]

def get_platform_details() -> Dict[str, Any]:
    """Returns a comprehensive dictionary of platform details and capabilities."""
    return PLATFORM_INFO

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info(f"Detected OS: {CURRENT_OS_TYPE}")
    logger.info(f"Is Root/Admin: {IS_ROOT}")
    logger.info(f"Architecture: {ARCH}")
    logger.info(f"Platform Capabilities: {get_platform_details()}")
