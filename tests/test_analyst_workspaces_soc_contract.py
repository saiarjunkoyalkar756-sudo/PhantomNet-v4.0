"""Source contracts for the evidence-first analyst-workspace rebuild."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVENT_WORKSPACE = ROOT / "dashboard_frontend/src/pages/EventStreamViewer.jsx"
CASE_WORKSPACE = ROOT / "dashboard_frontend/src/pages/CaseManagementPage.jsx"


def test_event_workspace_remains_tenant_scoped_read_only_and_without_a_live_client():
    source = EVENT_WORKSPACE.read_text(encoding="utf-8")

    for unsafe_component in (
        "socket.io-client",
        "VITE_WS_BASE_URL",
        "/ws/events",
        "useStore",
        "LiveFeedList",
        "EventDetailDrawer",
        "FilterToolbar",
        "Real-time security event feed",
    ):
        assert unsafe_component not in source

    assert "Governed Event-Evidence Integration Pending" in source
    assert "authorization-checked, provenance-linked, validated and minimized observations" in source
    assert "No authorized event evidence is available" in source
    assert "read-only and non-enforcing" in source
    assert "no containment or response authority" in source


def test_case_workspace_preserves_governed_lifecycle_and_non_execution_boundary():
    source = CASE_WORKSPACE.read_text(encoding="utf-8")

    for unsafe_component in (
        "/api/case-management/cases",
        "fetchCases",
        "handleCreateCase",
        "handleUpdateCase",
        "handleAddNote",
        "handleExecutePlaybook",
        "Create New Case",
        "Execute Default Playbook",
        "playbook_name: 'default_playbook'",
        "selectedCase.notes",
        "selectedCase.timeline",
    ):
        assert unsafe_component not in source

    assert "Governed Case-Lifecycle Integration Pending" in source
    assert "authenticated tenant-owned alerts" in source
    assert "playbook runs approval-bound and non-executing" in source
    assert "HMAC-signed audit" in source
    assert "No governed cases are available in this view" in source
    assert "This page does not assign cases, change status, trigger playbooks, or execute containment actions." in source
