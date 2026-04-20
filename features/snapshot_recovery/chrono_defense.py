import os
import shutil
import datetime
import json
import logging
from typing import List, Optional, Dict

logger = logging.getLogger("snapshot_recovery")

class ChronoDefense:
    """
    ChronoDefense Layer:
    Implements temporal rollback for compromised systems.
    Capable of state-snapshotting and automated recovery of configuration/critical data.
    """

    def __init__(self, snapshot_dir="snapshots", history_limit=10):
        self.snapshot_dir = os.path.join(os.getcwd(), snapshot_dir)
        self.history_limit = history_limit
        if not os.path.exists(self.snapshot_dir):
            os.makedirs(self.snapshot_dir)
        
        self.registry_file = os.path.join(self.snapshot_dir, "chrono_registry.json")
        self.registry = self._load_registry()
        logger.info(f"ChronoDefense initialized. History limit: {history_limit}")

    def _load_registry(self) -> Dict:
        if os.path.exists(self.registry_file):
            with open(self.registry_file, "r") as f:
                return json.load(f)
        return {"snapshots": [], "last_rollback": None}

    def _save_registry(self):
        with open(self.registry_file, "w") as f:
            json.dump(self.registry, f, indent=4)

    def create_snapshot(self, target_path: str, reason: str = "Automated") -> Optional[str]:
        """
        Creates an immutable, timestamped snapshot of a critical configuration or file.
        """
        if not os.path.exists(target_path):
            logger.error(f"Snapshot Failed: Path {target_path} missing.")
            return None

        snapshot_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        basename = os.path.basename(target_path)
        snapshot_filename = f"{basename}_{snapshot_id}.pnbackup"
        snapshot_full_path = os.path.join(self.snapshot_dir, snapshot_filename)

        try:
            if os.path.isdir(target_path):
                shutil.copytree(target_path, snapshot_full_path)
            else:
                shutil.copy2(target_path, snapshot_full_path)
            
            entry = {
                "id": snapshot_id,
                "target": target_path,
                "path": snapshot_full_path,
                "timestamp": datetime.datetime.now().isoformat(),
                "reason": reason,
                "type": "directory" if os.path.isdir(target_path) else "file"
            }
            self.registry["snapshots"].append(entry)
            self._rotate_snapshots(target_path)
            self._save_registry()
            
            logger.info(f"Snapshot Created: {snapshot_id} for {target_path}")
            return snapshot_id
        except Exception as e:
            logger.error(f"Snapshot Error: {e}")
            return None

    def _rotate_snapshots(self, target_path: str):
        """Maintains the history limit per target path."""
        target_snapshots = [s for s in self.registry["snapshots"] if s["target"] == target_path]
        if len(target_snapshots) > self.history_limit:
            to_remove = sorted(target_snapshots, key=lambda x: x["timestamp"])[:len(target_snapshots) - self.history_limit]
            for entry in to_remove:
                try:
                    if entry["type"] == "directory":
                        shutil.rmtree(entry["path"])
                    else:
                        os.remove(entry["path"])
                    self.registry["snapshots"].remove(entry)
                    logger.info(f"Rotated old snapshot: {entry['id']}")
                except Exception as e:
                    logger.warning(f"Failed to delete rotated snapshot {entry['id']}: {e}")

    def rollback_to_latest(self, target_path: str) -> bool:
        """
        Rolls back a target to its most recent stable state in the Chrono registry.
        """
        target_snapshots = [s for s in self.registry["snapshots"] if s["target"] == target_path]
        if not target_snapshots:
            logger.warning(f"Rollback Failed: No snapshots for {target_path}")
            return False

        latest = sorted(target_snapshots, key=lambda x: x["timestamp"])[-1]
        return self.rollback_to_id(latest["id"])

    def rollback_to_id(self, snapshot_id: str) -> bool:
        """
        Performs the temporal rollback to a specific point-in-time.
        """
        entry = next((s for s in self.registry["snapshots"] if s["id"] == snapshot_id), None)
        if not entry:
            return False

        target = entry["target"]
        source = entry["path"]

        try:
            # 1. Clear current state
            if os.path.exists(target):
                if os.path.isdir(target):
                    shutil.rmtree(target)
                else:
                    os.remove(target)

            # 2. Restore from snapshot
            if entry["type"] == "directory":
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)

            self.registry["last_rollback"] = {
                "snapshot_id": snapshot_id,
                "timestamp": datetime.datetime.now().isoformat()
            }
            self._save_registry()
            logger.info(f"System Rolled Back Successfully to {snapshot_id}")
            return True
        except Exception as e:
            logger.error(f"Rollback CRITICAL ERROR: {e}")
            return False

    def list_checkpoints(self, target_path: str = None) -> List[Dict]:
        if target_path:
            return [s for s in self.registry["snapshots"] if s["target"] == target_path]
        return self.registry["snapshots"]
