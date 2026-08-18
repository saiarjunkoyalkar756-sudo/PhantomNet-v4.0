"""Read-only Wazuh-compatible endpoint telemetry normalization boundary."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from phantomnet_core.contracts import HostAssetRecord, IntegrityObservation


class WazuhReadOnlyAdapter:
    """Normalize Wazuh alert payloads without using Wazuh active-response APIs."""

    automatic_enforcement = False
    supported_actions: tuple[str, ...] = ()

    @staticmethod
    def _timestamp(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, str):
            normalized = value.replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(normalized)
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return datetime.now(timezone.utc)

    @staticmethod
    def _severity(rule: Mapping[str, Any]) -> str:
        try:
            level = int(rule.get("level", 0))
        except (TypeError, ValueError):
            level = 0
        if level >= 12:
            return "critical"
        if level >= 8:
            return "high"
        if level >= 5:
            return "medium"
        if level >= 3:
            return "low"
        return "informational"

    @staticmethod
    def _integrity_status(syscheck: Mapping[str, Any]) -> str:
        event = str(syscheck.get("event", syscheck.get("changed", "modified"))).lower()
        if any(marker in event for marker in ("delete", "removed", "missing")):
            return "missing"
        if any(marker in event for marker in ("error", "fail")):
            return "error"
        if any(marker in event for marker in ("baseline", "match", "unchanged")):
            return "baseline_match"
        return "modified"

    @staticmethod
    def _check_type(syscheck: Mapping[str, Any]) -> str:
        path = str(syscheck.get("path", syscheck.get("registry", ""))).lower()
        if "registry" in syscheck or path.startswith("hkey_"):
            return "registry"
        return "file"

    def normalize(self, tenant_id: str, alert: Mapping[str, Any]) -> tuple[HostAssetRecord, IntegrityObservation | None]:
        """Convert one Wazuh alert into asset evidence and optional integrity evidence.

        The caller owns persistence; this adapter performs no outbound call and no endpoint action.
        """
        agent = alert.get("agent") if isinstance(alert.get("agent"), Mapping) else {}
        rule = alert.get("rule") if isinstance(alert.get("rule"), Mapping) else {}
        syscheck = alert.get("syscheck") if isinstance(alert.get("syscheck"), Mapping) else {}
        data = alert.get("data") if isinstance(alert.get("data"), Mapping) else {}
        agent_id = str(agent.get("id") or alert.get("agent_id") or "unknown-agent")
        hostname = str(agent.get("name") or alert.get("location") or agent_id)
        timestamp = self._timestamp(alert.get("timestamp"))
        asset = HostAssetRecord(
            tenant_id=tenant_id,
            agent_id=agent_id,
            hostname=hostname,
            platform=str(agent.get("os", {}).get("name", "unknown")) if isinstance(agent.get("os"), Mapping) else "unknown",
            os_version=(str(agent.get("os", {}).get("version")) if isinstance(agent.get("os"), Mapping) and agent.get("os", {}).get("version") else None),
            ip_addresses=[str(agent["ip"])] if agent.get("ip") else [],
            software=[],
            tags=["wazuh", *(str(group) for group in rule.get("groups", []) if isinstance(group, str))][:64],
            source="wazuh",
            last_seen=timestamp,
            evidence={
                "wazuh_rule_id": str(rule.get("id", "unknown")),
                "wazuh_rule_description": str(rule.get("description", "")),
                "decoder": alert.get("decoder", {}),
                "read_only": True,
            },
        )
        if not syscheck:
            return asset, None
        source_event_id = str(alert.get("id") or alert.get("event_id") or f"wazuh:{agent_id}:{timestamp.isoformat()}")
        integrity = IntegrityObservation(
            tenant_id=tenant_id,
            asset_id=asset.asset_id,
            agent_id=agent_id,
            source_event_id=source_event_id,
            source="wazuh",
            check_type=self._check_type(syscheck),
            status=self._integrity_status(syscheck),
            severity=self._severity(rule),
            observed_at=timestamp,
            path=(str(syscheck.get("path") or syscheck.get("registry")) if syscheck.get("path") or syscheck.get("registry") else None),
            observed_hash=(str(syscheck.get("sha256_after") or syscheck.get("md5_after")) if syscheck.get("sha256_after") or syscheck.get("md5_after") else None),
            expected_hash=(str(syscheck.get("sha256_before") or syscheck.get("md5_before")) if syscheck.get("sha256_before") or syscheck.get("md5_before") else None),
            evidence={
                "wazuh_rule_id": str(rule.get("id", "unknown")),
                "wazuh_rule_description": str(rule.get("description", "")),
                "syscheck": dict(syscheck),
                "data": dict(data),
                "read_only": True,
            },
            automatic_enforcement=False,
        )
        return asset, integrity

    async def request_containment(self, *_args: Any, **_kwargs: Any) -> None:
        """Explicitly refuse active response; SOAR provider boundaries own containment."""
        raise PermissionError("The Wazuh-compatible adapter is read-only and cannot request containment.")
