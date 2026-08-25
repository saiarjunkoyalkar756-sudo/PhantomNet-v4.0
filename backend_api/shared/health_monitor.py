"""Side-effect-free gateway readiness monitoring.

The gateway starts this background task for observational readiness reporting only. It
never selects agents, writes audit or identity state, dispatches commands, or probes
hard-coded endpoints.
"""
from __future__ import annotations

import asyncio

from loguru import logger

from backend_api.shared.control_plane_contracts import GATEWAY_REQUIRED_DEPENDENCIES
from backend_api.shared.health import run_standard_health_check


async def monitor_health(interval: int = 60) -> None:
    """Periodically record structured gateway readiness without taking any action."""
    if interval <= 0:
        raise ValueError("health-monitor interval must be positive")

    while True:
        readiness = await run_standard_health_check(GATEWAY_REQUIRED_DEPENDENCIES)
        logger.info(
            "Gateway readiness monitor completed",
            readiness=readiness["readiness"],
            mode=readiness["mode"],
        )
        await asyncio.sleep(interval)
