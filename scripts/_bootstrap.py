"""Runtime import bootstrap for standalone repository scripts.

Running ``python scripts/<script>.py`` places only ``scripts/`` on ``sys.path``.
This helper adds the repository root and the endpoint-agent package directory explicitly,
without requiring callers to provide ``PYTHONPATH``.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
AGENT_PACKAGE_ROOT = REPOSITORY_ROOT / "phantomnet_agent"


def configure_script_imports() -> None:
    """Make PhantomNet's local import roots available to directly executed scripts."""
    for import_root in (REPOSITORY_ROOT, AGENT_PACKAGE_ROOT):
        value = str(import_root)
        if value not in sys.path:
            sys.path.insert(0, value)
