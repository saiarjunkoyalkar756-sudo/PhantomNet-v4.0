# phantomnet_core/os_adapter.py
from shared.platform_utils import (
    CURRENT_OS_TYPE,
    OS_WINDOWS,
    OS_LINUX,
    OS_TERMUX,
    OS_UNKNOWN,
    HAS_EBPF,
    SUPPORTS_RAW_SOCKETS
)

def get_os() -> str:
    return CURRENT_OS_TYPE

def supports_ebpf() -> bool:
    return HAS_EBPF

def supports_raw_sockets() -> bool:
    return SUPPORTS_RAW_SOCKETS
