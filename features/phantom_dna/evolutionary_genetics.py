"""Deterministic local identity material for Phantom OS feature experiments."""

from __future__ import annotations

from hashlib import sha256
import platform
import socket


class PhantomDNA:
    """Derive a stable, non-secret fingerprint from caller-supplied or local platform metadata."""

    def __init__(self, identity_material: str | None = None) -> None:
        self._identity_material = identity_material or "|".join(
            (socket.gethostname(), platform.system(), platform.machine())
        )

    def get_system_dna(self) -> str:
        return sha256(self._identity_material.encode("utf-8")).hexdigest()
