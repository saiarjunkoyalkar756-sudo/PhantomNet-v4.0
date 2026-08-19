"""Local immutable-style snapshot helper for controlled recovery workflows.

This module copies only explicit regular files supplied by the caller. It does not discover files,
execute commands, or modify anything until a caller explicitly requests a rollback.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import shutil


class ChronoDefense:
    """Create content-preserving file snapshots and explicitly restore a selected snapshot."""

    def __init__(self, snapshot_dir: str | Path) -> None:
        self.snapshot_dir = Path(snapshot_dir).expanduser().resolve()
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _target_path(target_file: str | Path) -> Path:
        target = Path(target_file).expanduser().resolve()
        if not target.is_file():
            raise FileNotFoundError(f"Snapshot target is not a regular file: {target}")
        return target

    @staticmethod
    def _target_prefix(target: Path) -> str:
        target_hash = sha256(str(target).encode("utf-8")).hexdigest()[:16]
        return f"{target.name}.{target_hash}."

    def create_snapshot(self, target_file: str | Path) -> str:
        target = self._target_path(target_file)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        snapshot = self.snapshot_dir / f"{self._target_prefix(target)}{timestamp}.snapshot"
        shutil.copy2(target, snapshot)
        return str(snapshot)

    def get_latest_snapshot(self, target_file: str | Path) -> str | None:
        target = self._target_path(target_file)
        candidates = sorted(
            self.snapshot_dir.glob(f"{self._target_prefix(target)}*.snapshot"),
            key=lambda candidate: candidate.stat().st_mtime_ns,
        )
        return str(candidates[-1]) if candidates else None

    def rollback_to_snapshot(self, target_file: str | Path, snapshot_path: str | Path) -> bool:
        target = self._target_path(target_file)
        snapshot = Path(snapshot_path).expanduser().resolve()
        if not snapshot.is_file() or snapshot.parent != self.snapshot_dir:
            return False
        if not snapshot.name.startswith(self._target_prefix(target)):
            return False
        shutil.copy2(snapshot, target)
        return True
