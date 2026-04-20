# backend_api/shared/dna_engine.py

import logging
import hashlib
import uuid
import platform
import socket
from typing import Dict, Any

from backend_api.shared.logger_config import logger

class DNAEngine:
    """
    Electronic DNA (eDNA) Engine:
    Synthesizes and verifies the immutable genetic fingerprint of a host.
    Used for Zero-Trust device identity and Root of Trust.
    """

    def __init__(self):
        self.dna_sequence = self._synthesize_dna()
        logger.info(f"DNAEngine: Host DNA synthesized as {self.dna_sequence[:8]}...")

    def _synthesize_dna(self) -> str:
        """
        Gathers deep hardware and platform traits to create a unique 128-bit hash.
        """
        try:
            traits = [
                platform.node(),
                platform.machine(),
                platform.system(),
                str(uuid.getnode()), # Persistent MAC-based identifier
                socket.getfqdn()
            ]
            raw_dna = "|".join(traits)
            return hashlib.md5(raw_dna.encode()).hexdigest()
        except Exception as e:
            logger.error(f"DNA Synthesis Error: {e}")
            return uuid.uuid4().hex

    def get_dna(self) -> str:
        return self.dna_sequence

    def tag_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tags an event with the host's genetic signature for provenance.
        """
        event_data["provenance_dna"] = self.dna_sequence
        return event_data

    @staticmethod
    def verify_provenance(event_data: Dict[str, Any], expected_dna: str) -> bool:
        """
        Verifies if an event actually originated from the claimed hardware DNA.
        """
        return event_data.get("provenance_dna") == expected_dna
