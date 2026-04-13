# phantomnet_agent/attestation.py
import hashlib
import logging
import platform
import subprocess
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

def _get_machine_id_linux() -> str:
    """
    Reads the machine-id, which is unique and persistent for a given OS installation.
    """
    try:
        with open("/etc/machine-id", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def _get_machine_guid_windows() -> str:
    """
    Reads the MachineGuid from the Windows Registry.
    """
    try:
        result = subprocess.check_output(
            "reg query HKLM\SOFTWARE\Microsoft\Cryptography /v MachineGuid",
            shell=True,
            stderr=subprocess.PIPE,
        ).decode()
        # Output is in the format: '\r\n<key>\r\n    <name>    <type>    <value>\r\n'
        return result.split()[-1]
    except Exception:
        return ""

def _get_android_id_termux() -> str:
    """
    Gets the ANDROID_ID, a unique identifier for the Android device.
    Requires the Termux:API package to be installed on the device.
    """
    try:
        # This requires the user to have installed termux-api
        result = subprocess.check_output(
            ["termux-telephony-deviceinfo"], stderr=subprocess.PIPE
        ).decode()
        # A more robust implementation would parse the JSON output
        # For now, we'll just use a hash of the full output
        return hashlib.sha256(result.encode()).hexdigest()
    except (FileNotFoundError, subprocess.CalledProcessError):
        # Fallback if termux-api is not installed
        return ""

def get_platform_specific_id() -> str:
    """
    Returns a unique and persistent identifier for the host OS.
    """
    system = platform.system()
    if system == "Linux":
        # Check if it's Termux by looking for a specific environment variable
        if "TERMUX_VERSION" in os.environ:
            return _get_android_id_termux()
        return _get_machine_id_linux()
    elif system == "Windows":
        return _get_machine_guid_windows()
    else:
        # Fallback for other systems (like macOS)
        return ""

def generate_attestation_payload() -> Dict[str, Any]:
    """
    Gathers unique and hard-to-spoof identifiers from the host machine.
    """
    platform_id = get_platform_specific_id()
    
    # Hash the ID to avoid sending raw sensitive identifiers over the wire,
    # even with mTLS. This is a good practice.
    hashed_id = (
        hashlib.sha256(platform_id.encode()).hexdigest() if platform_id else None
    )

    payload = {
        "event_type": "agent_attestation",
        "data": {
            "platform_id_hash": hashed_id,
            "os_type": platform.system(),
            "os_version": platform.release(),
            "agent_version": "3.0.0",  # This would be dynamic in a real build
        },
    }
    logger.info(f"Generated attestation payload with ID hash: {hashed_id}")
    return payload
