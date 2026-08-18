"""Process-wide safety controls for response-capable services."""

from __future__ import annotations

import os


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# Real integrations remain disabled until an operator explicitly sets this to false.
SAFE_MODE = _read_bool("PHANTOMNET_SAFE_MODE", default=True)
