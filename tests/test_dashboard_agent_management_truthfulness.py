from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS_PAGE = ROOT / "dashboard_frontend/src/pages/AgentsManagementPage.jsx"
AGENTS_TABLE = ROOT / "dashboard_frontend/src/features/agents/components/AgentsTable.jsx"
ACTION_MENU = ROOT / "dashboard_frontend/src/features/agents/components/ActionMenu.jsx"
SELF_HEALING_CONSOLE = ROOT / "dashboard_frontend/src/pages/SelfHealingConsolePage.jsx"
SANDBOX_PAGE = ROOT / "dashboard_frontend/src/pages/SandboxPage.jsx"
SIEM_INTEGRATION_PAGE = ROOT / "dashboard_frontend/src/pages/SiemIntegrationPage.jsx"
VULNERABILITY_SCANNER_PAGE = ROOT / "dashboard_frontend/src/pages/VulnerabilityScannerPage.jsx"
VULNERABILITY_MANAGEMENT_PAGE = ROOT / "dashboard_frontend/src/pages/VulnerabilityManagementPage.jsx"
MARKETPLACE_PAGE = ROOT / "dashboard_frontend/src/pages/Marketplace.jsx"
MARKETPLACE_GRID = ROOT / "dashboard_frontend/src/features/marketplace/components/MarketplaceGrid.jsx"
COMPLIANCE_REPORTING_PAGE = ROOT / "dashboard_frontend/src/pages/ComplianceReportingPage.jsx"
FORENSICS_PAGE = ROOT / "dashboard_frontend/src/pages/ForensicsPage.jsx"
CLOUD_SECURITY_PAGE = ROOT / "dashboard_frontend/src/pages/CloudSecurityPage.jsx"
SOAR_PAGE = ROOT / "dashboard_frontend/src/pages/SOARPage.jsx"
GRAPH_CANVAS = ROOT / "dashboard_frontend/src/features/threat-graph/components/GraphCanvas.jsx"
AI_DECISION_LOG_PAGE = ROOT / "dashboard_frontend/src/pages/AIDecisionLogPage.jsx"
ATTACK_GRAPH_PAGE = ROOT / "dashboard_frontend/src/pages/AttackGraphPage.jsx"


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


def test_sandbox_page_does_not_retain_retired_upload_or_analysis_result_controls():
    source = SANDBOX_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "FormData",
        "/api/sandbox/analyze",
        "handleAnalyzeFile",
        "handleFileChange",
        "type=\"file\"",
        "Analyze File",
        "analysisResult",
        "raw_output",
        "MALICIOUS",
        "CLEAN",
        "dropped_artifacts",
    ):
        assert unsafe_component not in source

    assert "Governed Malware Analysis Integration Pending" in source
    assert "isolated execution, authorization, evidence, retention" in source


def test_siem_integration_page_does_not_retain_retired_connection_or_event_controls():
    source = SIEM_INTEGRATION_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "/api/siem-integration/",
        "fetchConnections",
        "handleAddConnection",
        "handleSendTestEvent",
        "Add Connection",
        "Send Test Event",
        "Existing SIEM Connections",
        "configJson",
        "testEventData",
    ):
        assert unsafe_component not in source

    assert "Governed SIEM Integration Pending" in source
    assert "tenant-scoped configuration custody, provider authorization" in source


def test_vulnerability_scanner_page_does_not_retain_retired_target_or_finding_controls():
    source = VULNERABILITY_SCANNER_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "/api/vulnerability-scanner/",
        "handlePortScan",
        "handleCveScan",
        "handleConfigCheck",
        "Port Scan",
        "CVE Scan",
        "Check Configuration",
        "portScanResults",
        "cveResults",
        "configAlerts",
        "Target (IP or Hostname)",
    ):
        assert unsafe_component not in source

    assert "Governed Vulnerability Assessment Integration Pending" in source
    assert "target authorization, tenant-scoped evidence handling" in source


def test_vulnerability_management_page_does_not_retain_fixture_findings_or_remote_patch_controls():
    source = VULNERABILITY_MANAGEMENT_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "FALLBACK_ASSETS",
        "FALLBACK_VULNERABILITIES",
        "triggerScanner",
        "LAUNCH RAPID SCAN",
        "EXECUTE REMOTE PATCH",
        "AI Remediation Plan",
        "CVE-2024-3094",
        "risk_score",
        "vulnerabilityService",
        "scanProgress",
    ):
        assert unsafe_component not in source

    assert "Governed Vulnerability Management Integration Pending" in source
    assert "human-approved change control for remediation" in source


def test_marketplace_does_not_retain_fixture_plugins_or_simulated_extension_lifecycle_controls():
    page_source = MARKETPLACE_PAGE.read_text(encoding="utf-8")
    grid_source = MARKETPLACE_GRID.read_text(encoding="utf-8")

    assert "BROWSE CATEGORIES" not in page_source
    assert "Fixture extension catalogues and simulated enablement controls are retired" in page_source

    for unsafe_component in (
        "initialPlugins",
        "Advanced XDR Integration",
        "Decoy Honeypot Network",
        "AI Threat Hunter",
        "Blockchain Traceability Module",
        "signatureValid",
        "handleToggleEnable",
        "PluginCard",
        "ModalInspector",
    ):
        assert unsafe_component not in grid_source

    assert "Governed Extension Lifecycle Pending" in grid_source
    assert "trusted provenance, tenant-scoped configuration" in grid_source


def test_compliance_reporting_page_does_not_retain_retired_artifact_or_audit_controls():
    source = COMPLIANCE_REPORTING_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "/compliance-reporting/reports",
        "fetchReports",
        "handleGenerateReport",
        "handleViewReportDetails",
        "handleDownloadPDF",
        "Generate PDF Report",
        "Recent Reports",
        "Download PDF Artifact",
        "Compliance Score",
        "Security Controls Verified",
    ):
        assert unsafe_component not in source

    assert "Governed Compliance Evidence Integration Pending" in source
    assert "tenant-scoped evidence provenance, report authorization" in source


def test_forensics_page_does_not_retain_fixture_acquisition_or_evidence_controls():
    source = FORENSICS_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "runningJobs",
        "forensicsTimeline",
        "evidenceVault",
        "launchForensicJob",
        "LAUNCH DYNAMIC ACQUISITION",
        "CRYPTOGRAPHIC CUSTODY VAULT",
        "EXPORT FORENSIC REPORT",
        "Live RAM dump extraction",
        "Custody Integrity",
    ):
        assert unsafe_component not in source

    assert "Governed Forensics Integration Pending" in source
    assert "authorized collection targets, tenant-scoped evidence" in source


def test_cloud_security_page_does_not_retain_caller_credentials_or_retired_cloud_checks():
    source = CLOUD_SECURITY_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "aws_access_key_id",
        "aws_secret_access_key",
        "/api/cloud-security/",
        "handleAwsMisconfiguration",
        "handleIamAbuseDetection",
        "handleS3ExposureAlerts",
        "Check Misconfigurations",
        "Detect IAM Abuse",
        "S3 Exposure Alerts",
        "setMisconfigurations",
        "setIamAlerts",
        "setS3Exposure",
    ):
        assert unsafe_component not in source

    assert "Governed Cloud Security Integration Pending" in source
    assert "authorized credentials held outside the client" in source


def test_soar_page_does_not_retain_fixture_playbooks_or_simulated_containment_controls():
    source = SOAR_PAGE.read_text(encoding="utf-8")

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
    ):
        assert unsafe_component not in source

    assert "Governed Containment Dashboard Integration Pending" in source
    assert "HMAC-signed audit evidence" in source
    assert "High-impact containment must never become automatic through the client" in source


def test_graph_canvas_does_not_retain_placeholder_visualization_or_inert_controls():
    source = GRAPH_CANVAS.read_text(encoding="utf-8")

    for unsafe_component in (
        "ATTACK PATH INTELLIGENCE MAP",
        "Interactive Graph Visualization",
        "Zoom In",
        "Zoom Out",
        "Array.from({ length: 100 })",
        "placeholder for a complex graph visualization",
    ):
        assert unsafe_component not in source

    assert "Governed Attack-Path Visualization Integration Pending" in source
    assert "tenant-scoped, authorized, provenance-linked results" in source


def test_ai_decision_log_page_does_not_retain_unsupported_autonomous_decision_views():
    source = AI_DECISION_LOG_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "/api/ai/decision_logs",
        "fetchAIDecisionLogs",
        "setInterval(",
        "decisionLogs",
        "Execution Trace",
        "Confidence",
        "Review autonomous decisions",
        "JSON.stringify(log.details",
    ):
        assert unsafe_component not in source

    assert "Governed Advisory Evidence-Log Integration Pending" in source
    assert "policy-gated and non-executing" in source
    assert "approval-bound containment" in source


def test_attack_graph_page_does_not_retain_fixture_topology_or_simulated_containment():
    source = ATTACK_GRAPH_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "segmentationViolations",
        "triggerNodeIsolation",
        "Containment complete. Node ISOLATED.",
        "NEO4J LATERAL MOVEMENT MAPPING",
        "CRITICAL PATH DETECTED",
        "THREAT BLAST RADIUS IMPACT",
        "CONTAIN NODE",
        "DMZ Web Server",
        "Active Directory DC",
    ):
        assert unsafe_component not in source

    assert "Governed Attack-Path and Containment Integration Pending" in source
    assert "HMAC-signed audit" in source
    assert "without automatic high-impact containment" in source
