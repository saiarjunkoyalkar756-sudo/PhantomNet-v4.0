# backend_api/honeypot_service/event_normalizer.py
from typing import Dict, Any, Optional
import hashlib

def normalize_event(raw_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes a raw honeypot event into a standard platform event schema.

    Args:
        raw_event: The raw event dictionary from a honeypot.

    Returns:
        A dictionary representing the normalized event.
    """
    normalized: Dict[str, Any] = {
        "event_id": str(raw_event.get("session_id")), # Using session_id as event_id for now
        "timestamp": raw_event.get("timestamp"),
        "honeypot_id": raw_event.get("honeypot_id"),
        "source_ip": raw_event.get("src_ip"),
        "source_port": raw_event.get("src_port"),
        "destination_port": raw_event.get("dst_port"),
        "protocol": raw_event.get("protocol"),
        "event_type": raw_event.get("event_type"),
        "payload": raw_event.get("payload"),
        "payload_hash": raw_event.get("payload_hash"),
        "file_hashes": raw_event.get("file_hashes", []), # Placeholder for file hashes
        "pcap_link": raw_event.get("pcap_link", None), # Placeholder for pcap link
        "metadata": { # Additional metadata not covered by standard fields
            "honeypot_type": raw_event.get("honeypot_type"), # Added by manager
            # Add other custom fields if necessary
        }
    }

    # Ensure required fields are present or set to None/default
    if not normalized.get("event_id"):
        normalized["event_id"] = hashlib.sha256(str(raw_event).encode()).hexdigest() # Fallback

    return normalized

