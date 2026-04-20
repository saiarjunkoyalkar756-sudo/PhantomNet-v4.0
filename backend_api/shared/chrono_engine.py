# backend_api/shared/chrono_engine.py

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from backend_api.shared.logger_config import logger

class ChronoEngine:
    """
    ChronoDefense Engine:
    Manages temporal forensic snapshots and autonomous rollback state recovery.
    Enables 'Temporal Countermeasures' by reverting compromised states.
    """

    def __init__(self, retention_window_hours: int = 24):
        self.retention_window = timedelta(hours=retention_window_hours)
        self.snapshots: Dict[str, List[Dict[str, Any]]] = {} # Map host_id to state history
        logger.info(f"ChronoEngine: Initialized with {retention_window_hours} hour retention window.")

    async def capture_snapshot(self, host_id: str, state_data: Dict[str, Any]):
        """
        Captures a point-in-time micro-snapshot of system/asset state.
        """
        timestamp = datetime.now()
        snapshot = {
            "timestamp": timestamp.isoformat(),
            "state": state_data,
            "id": f"snap-{int(timestamp.timestamp())}"
        }
        
        if host_id not in self.snapshots:
            self.snapshots[host_id] = []
        
        self.snapshots[host_id].append(snapshot)
        
        # Prune old snapshots
        cutoff = timestamp - self.retention_window
        self.snapshots[host_id] = [
            s for s in self.snapshots[host_id] 
            if datetime.fromisoformat(s["timestamp"]) > cutoff
        ]
        
        logger.debug(f"ChronoEngine: Captured snapshot for {host_id}. History depth: {len(self.snapshots[host_id])}")

    async def propose_rollback(self, host_id: str, threat_discovery_time: datetime) -> Optional[Dict[str, Any]]:
        """
        Identifies the last known-good state prior to the threat discovery.
        """
        if host_id not in self.snapshots or not self.snapshots[host_id]:
            logger.warning(f"ChronoEngine: No snapshots found for {host_id}. Cannot propose rollback.")
            return None

        # Sort snapshots by timestamp descending
        valid_snapshots = [
            s for s in self.snapshots[host_id]
            if datetime.fromisoformat(s["timestamp"]) < threat_discovery_time
        ]

        if not valid_snapshots:
            logger.error(f"ChronoEngine: No snapshots exist prior to threat discovery for {host_id}.")
            return None

        # Return the most recent snapshot before the threat
        last_good = valid_snapshots[-1]
        logger.info(f"ChronoEngine: Rollback proposed for {host_id} to state {last_good['id']} (Time: {last_good['timestamp']})")
        return last_good

    async def execute_temporal_reset(self, host_id: str, snapshot_id: str):
        """
        Conceptual hook to trigger the physical rollback (e.g., via snap-diff apply or container restart).
        """
        logger.warning(f"ChronoEngine: TRIGGERING TEMPORAL RESET on {host_id} to snapshot {snapshot_id}!!")
        # In production, this would send an 'ACTIVATE_ROLLBACK' command to the agent/orchestrator
        await asyncio.sleep(0.5)
        return True
