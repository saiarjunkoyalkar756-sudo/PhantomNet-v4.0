"""Fail-closed coverage for agent-side host isolation boundaries."""

from __future__ import annotations

import pytest

from phantomnet_agent.platform_compatibility.linux_adapter import LinuxAdapter


@pytest.mark.asyncio
async def test_linux_host_isolation_reports_non_enforcement_without_a_verified_provider():
    result = await LinuxAdapter().isolate_system("controlled isolation validation")

    assert result["status"] == "failed"
    assert result["enforced"] is False
    assert result["verified"] is False
    assert result["rollback_available"] is False
    assert "no firewall state was changed" in result["detail"]
