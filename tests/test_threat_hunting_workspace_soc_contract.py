"""Source contract for the evidence-first threat-hunting workspace rebuild."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "dashboard_frontend/src/pages/ThreatHuntingPage.jsx"
SERVICE = ROOT / "dashboard_frontend/src/services/threatHunting.service.js"


def test_threat_hunting_workspace_retains_supported_governed_client_operations():
    source = WORKSPACE.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")

    for client_operation in (
        "executeHunt",
        "fetchSavedHunts",
        "saveHunt",
        "executeSavedHunt",
        "fetchAutomatedHunts",
        "fetchHuntDashboardSummary",
        "refreshAttackGraph",
        "analyzeAttackPath",
    ):
        assert client_operation in source

    assert "fetchHuntDashboardSummary" in service
    assert "localhost:8001" not in service
    assert "THREAT HUNTING · Tenant-scoped analyst workspace" in source
    assert "Structured, allowlisted hunts" in source
    assert "Read-only hunt mode" in source
    assert "A hunt cannot dispatch containment or a response action." in source


def test_threat_hunting_workspace_refuses_to_present_unsupported_actions_or_global_claims():
    source = WORKSPACE.read_text(encoding="utf-8")

    for unsupported_claim in (
        "Autonomous remediation",
        "Execute containment",
        "Global threat command",
        "Real-time global visibility",
        "Run arbitrary query",
        "automatic enforcement",
    ):
        assert unsupported_claim not in source

    assert "No raw query language is accepted." in source
    assert "No alert count is shown without summary evidence." in source
    assert "This chart appears only when the governed summary includes MITRE-linked tenant evidence." in source
    assert "This bounded graph analysis does not execute a response or containment action." in source
    assert "No hunt evidence selected" in source
