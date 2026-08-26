"""Source contract for the governed response and advisory-triage workspace."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "dashboard_frontend/src/pages/SOARPage.jsx"
SERVICE = ROOT / "dashboard_frontend/src/services/governedResponse.service.js"


def test_governed_response_workspace_uses_only_supported_control_plane_operations():
    source = WORKSPACE.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")

    for operation in (
        "fetchContainmentRequests",
        "createContainmentRequest",
        "fetchContainmentPreflight",
        "decideContainmentRequest",
        "executeContainmentRequest",
        "rollbackContainmentRequest",
        "verifyContainmentAudit",
        "fetchDefensePolicies",
        "fetchDefenseDecisions",
        "evaluateDefenseDetection",
    ):
        assert operation in source
        assert operation in service

    assert "VITE_SOAR_API_URL" in service
    assert "/governed-containment" in service
    assert "Create an approval-bound response request" in source
    assert "No adapter is called during request creation." in source
    assert "HMAC-signed audit evidence is required for high-impact response." in source
    assert "High-impact containment must never become automatic through the client." in source


def test_governed_response_workspace_does_not_restore_fixture_or_autonomous_controls():
    source = WORKSPACE.read_text(encoding="utf-8")

    for unsafe_component in (
        "FALLBACK_PLAYBOOKS",
        "pendingApprovals",
        "activeExecutions",
        "recentRuns",
        "blockedIps",
        "handleTriggerPlaybook",
        "DEPLOY MITIGATION",
        "AUTHORIZE",
        "UNBAN",
        "EXECUTE REMOTE PATCH",
        "Blockchain Ledgers",
        "LAUNCH DYNAMIC ACQUISITION",
        "Automatic containment enabled",
        "Execute without approval",
    ):
        assert unsafe_component not in source

    assert "Governed Containment Dashboard Integration Pending" in source
    assert "This form cannot mark a request approved or send an adapter command." in source
    assert "The client does not create confidence scores, evidence, or outcomes locally." in source
    assert "it never executes an adapter." in source
    assert "No governed response requests are available" in source
