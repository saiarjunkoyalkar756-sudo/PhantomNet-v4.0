from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS_PAGE = ROOT / "dashboard_frontend/src/pages/AgentsManagementPage.jsx"
AGENTS_TABLE = ROOT / "dashboard_frontend/src/features/agents/components/AgentsTable.jsx"
ACTION_MENU = ROOT / "dashboard_frontend/src/features/agents/components/ActionMenu.jsx"
SELF_HEALING_CONSOLE = ROOT / "dashboard_frontend/src/pages/SelfHealingConsolePage.jsx"


def test_dashboard_agent_management_page_states_the_governed_integration_boundary():
    source = AGENTS_PAGE.read_text(encoding="utf-8")

    assert "Legacy agent enrollment and lifecycle controls are retired" in source
    assert "ADD NEW AGENT" not in source
    assert "PlusCircle" not in source


def test_dashboard_agent_table_does_not_retain_fixture_fleet_data_or_simulated_actions():
    source = AGENTS_TABLE.read_text(encoding="utf-8")

    for unsafe_component in (
        "initialAgents",
        "Endpoint Sentinel Alpha",
        "handleAction",
        "onApprove",
        "onRevoke",
        "onQuarantine",
        "certificateValid",
        "lastHeartbeat",
        "/api/agents",
    ):
        assert unsafe_component not in source

    assert "Governed Endpoint Integration Pending" in source
    assert "human-approved, auditable, verified, and rollback-capable" in source


def test_dashboard_agent_action_menu_cannot_reintroduce_simulated_lifecycle_controls():
    source = ACTION_MENU.read_text(encoding="utf-8")

    assert "=> null" in source
    for unsafe_component in ("Approve", "Revoke", "Quarantine", "DropdownMenu"):
        assert unsafe_component not in source


def test_self_healing_console_does_not_retain_legacy_agent_polling_or_placeholder_actions():
    source = SELF_HEALING_CONSOLE.read_text(encoding="utf-8")

    for unsafe_component in (
        "fetchAgentStatus",
        "/api/agents/",
        "setInterval",
        "handleManualOverride",
        "Trigger Repair",
        "Request Patch",
        "Initiate Recovery",
        "Disable Self-Healing",
        "Enable SAFE_MODE",
    ):
        assert unsafe_component not in source

    assert "Governed Response Integration Pending" in source
    assert "human-approved for high-impact actions" in source
