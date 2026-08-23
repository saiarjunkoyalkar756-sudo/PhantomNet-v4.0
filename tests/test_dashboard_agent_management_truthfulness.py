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
SIEM_PAGE = ROOT / "dashboard_frontend/src/pages/SIEMPage.jsx"
LEGACY_LOG_SEARCH = ROOT / "dashboard_frontend/src/components/LogSearch.jsx"
LEGACY_SIEM_SERVICE = ROOT / "dashboard_frontend/src/services/siem.service.js"
THREAT_INTEL_OSINT_PAGE = ROOT / "dashboard_frontend/src/pages/ThreatIntelOSINTPage.jsx"
SIMULATED_OSINT_SEARCH = ROOT / "dashboard_frontend/src/features/threat-intel/components/SearchBar.jsx"
SIMULATED_OSINT_CARDS = ROOT / "dashboard_frontend/src/features/threat-intel/components/IntelCards.jsx"
NETWORK_THREATS_PAGE = ROOT / "dashboard_frontend/src/pages/network/NetworkThreatsPage.jsx"
NETWORK_SEGMENTATION_PAGE = ROOT / "dashboard_frontend/src/pages/network/NetworkSegmentationPage.jsx"
NETWORK_GRAPH = ROOT / "dashboard_frontend/src/components/network/NetworkGraph.jsx"
WORLD_ATTACK_MAP = ROOT / "dashboard_frontend/src/features/dashboard/WorldAttackMap.jsx"
CASE_MANAGEMENT_PAGE = ROOT / "dashboard_frontend/src/pages/CaseManagementPage.jsx"
GRAPH_INVESTIGATION_PAGE = ROOT / "dashboard_frontend/src/pages/GraphInvestigationPage.jsx"
LOG_VIEWER_PAGE = ROOT / "dashboard_frontend/src/pages/LogViewer.jsx"
LEGACY_LOG_FORMAT_SWITCH = ROOT / "dashboard_frontend/src/features/log-viewer/components/FormatSwitch.jsx"
LEGACY_LOG_ACTION_BAR = ROOT / "dashboard_frontend/src/features/log-viewer/components/ActionBar.jsx"
LEGACY_LOG_STREAM_VIEWER = ROOT / "dashboard_frontend/src/features/log-viewer/components/LogStreamViewer.jsx"
ALERTS_PAGE = ROOT / "dashboard_frontend/src/pages/AlertsPage.jsx"
NETWORK_OVERVIEW_PAGE = ROOT / "dashboard_frontend/src/pages/network/NetworkOverviewPage.jsx"
DASHBOARD_PAGE = ROOT / "dashboard_frontend/src/pages/Dashboard.jsx"
ADMIN_DASHBOARD_PAGE = ROOT / "dashboard_frontend/src/pages/AdminDashboard.jsx"
TERMINAL_CHAT = ROOT / "dashboard_frontend/src/features/ai-console/components/TerminalChat.jsx"


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


def test_siem_page_retires_direct_legacy_phantomql_search_client():
    source = SIEM_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "LogSearch",
        "phantomql-engine",
        "localhost:8001",
        "query_string",
        "<table",
    ):
        assert unsafe_component not in source

    assert not LEGACY_LOG_SEARCH.exists()
    assert not LEGACY_SIEM_SERVICE.exists()
    assert "Governed Log-Search Integration Pending" in source
    assert "tenant scope and analyst authorization" in source
    assert "deterministic auditability" in source


def test_threat_intel_osint_page_retires_randomized_fixture_enrichment_views():
    source = THREAT_INTEL_OSINT_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "handleIpSearch",
        "Math.random",
        "ipQueryResult",
        "Reputation Score",
        "Malicious Reports",
        "GEOIP LOCATION",
        "IOC LIST VIEWER",
        "OSINT EVIDENCE TIMELINE",
        "SearchBar",
        "IntelCard",
    ):
        assert unsafe_component not in source

    assert not SIMULATED_OSINT_SEARCH.exists()
    assert not SIMULATED_OSINT_CARDS.exists()
    assert "Governed Advisory-Enrichment Integration Pending" in source
    assert "analyst authorization" in source
    assert "remain advisory-only with no response authority" in source


def test_network_threats_page_retires_unsupported_raw_threat_feed():
    source = NETWORK_THREATS_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "useEffect",
        "useState",
        "fetch('/api/v1/network/threats')",
        "setThreats",
        "Recent Threats",
        "Source IP",
        "threat.source",
        "threat.timestamp",
        "<Table",
    ):
        assert unsafe_component not in source

    assert "Governed Network-Threat Evidence Integration Pending" in source
    assert "tenant-scoped, provenance-linked evidence" in source
    assert "must not imply active network control" in source


def test_network_segmentation_page_retires_unsupported_topology_and_violation_views():
    source = NETWORK_SEGMENTATION_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "useEffect",
        "useState",
        "fetch('/api/v1/network/violations')",
        "fetch('/api/v1/network/topology')",
        "NetworkGraph",
        "Segmentation Map",
        "Segmentation Violations",
        "source_ip",
        "destination_ip",
        "<Table",
    ):
        assert unsafe_component not in source

    assert not NETWORK_GRAPH.exists()
    assert "Governed Segmentation-Evidence Integration Pending" in source
    assert "tenant-scoped, provenance-linked evidence" in source
    assert "must not imply live topology accuracy" in source


def test_world_attack_map_retires_mock_global_attack_visualization():
    source = WORLD_ATTACK_MAP.read_text(encoding="utf-8")

    for unsafe_component in (
        "const hotspots",
        "const attacks",
        "const backgroundDots",
        "LIVE GLOBAL THREAT MAP",
        "North America",
        "East Asia",
        "LATENCY:",
        "ACTIVE THREATS:",
        "1,204",
        "42MS",
        "MotionPath",
    ):
        assert unsafe_component not in source

    assert "Governed Global-Evidence Visualization Integration Pending" in source
    assert "tenant-scoped, provenance-linked and minimized evidence" in source
    assert "remain read-only, advisory, and non-enforcing" in source


def test_case_management_page_retires_direct_legacy_case_and_playbook_controls():
    source = CASE_MANAGEMENT_PAGE.read_text(encoding="utf-8")

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


def test_graph_investigation_page_retires_arbitrary_raw_graph_query_controls():
    source = GRAPH_INVESTIGATION_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "/api/graph-intelligence/graph",
        "cypherQuery",
        "executeQuery",
        "Execute Cypher",
        "MATCH (p:Process)",
        "setResults",
        "Object.keys(results[0])",
        "JSON.stringify(value)",
    ):
        assert unsafe_component not in source

    assert "Governed Graph-Investigation Integration Pending" in source
    assert "tenant-scoped, authorization-checked, provenance-linked results" in source
    assert "remain non-enforcing with no containment or response authority" in source


def test_log_viewer_page_retires_fixture_stream_and_local_disclosure_controls():
    source = LOG_VIEWER_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "mockLogs",
        "setInterval(",
        "logIndexRef",
        "User login successful",
        "Agent heartbeat received",
        "Malicious payload detected and quarantined.",
        "handleCopy",
        "handleExport",
        "handleClear",
        "FormatSwitch",
        "ActionBar",
        "LogStreamViewer",
        "ADVANCED SEARCH",
    ):
        assert unsafe_component not in source

    assert not LEGACY_LOG_FORMAT_SWITCH.exists()
    assert not LEGACY_LOG_ACTION_BAR.exists()
    assert not LEGACY_LOG_STREAM_VIEWER.exists()
    assert "Governed Log-Evidence Integration Pending" in source
    assert "authorization-checked, provenance-linked, minimized results" in source
    assert "must not imply live ingestion" in source


def test_alerts_page_retires_unsupported_raw_alert_polling_and_disclosure():
    source = ALERTS_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "axios",
        "VITE_API_BASE_URL",
        "/api/v1/alerts",
        "fetchAlerts",
        "setInterval(",
        "alert.alert_id",
        "alert.rule_name",
        "alert.agent_id",
        "alert.severity",
        "alert.triggered_at",
        "alert.details",
        "<Table",
    ):
        assert unsafe_component not in source

    assert "Governed Alert-Evidence Integration Pending" in source
    assert "tenant-scoped, authorization-checked, provenance-linked alert evidence" in source
    assert "remain non-enforcing with no containment or response authority" in source


def test_network_overview_page_retires_unscoped_stream_and_metric_claims():
    source = NETWORK_OVERVIEW_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "WebSocket(",
        "/ws/network",
        "packet_metadata",
        "network_graph",
        "setTraffic",
        "setConnections",
        "setThreats",
        "Real-Time Traffic",
        "Active Connections",
        "Blocked Threats",
    ):
        assert unsafe_component not in source

    assert "Governed Network-Evidence Integration Pending" in source
    assert "authorization-checked, provenance-linked, validated and minimized observations" in source
    assert "remain read-only and non-enforcing" in source


def test_dashboard_page_preserves_governed_summary_without_autonomous_product_claims():
    source = DASHBOARD_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "GLOBAL THREAT COMMAND",
        "Real-time autonomous security orchestration overview.",
        "ZEN DEFENSE ACTIVE",
        "NEW INVESTIGATION",
        "LIVE PROPAGATION FEED",
        "450 automated remediations successful",
        "PHANTOM SENTINEL",
        "No manual intervention required.",
        "Chat with Sentinel (AI)",
    ):
        assert unsafe_component not in source

    assert "THREAT-HUNTING EVIDENCE SUMMARY" in source
    assert "fetchHuntDashboardSummary" in source
    assert "Read-only governed summary" in source
    assert "does not establish global visibility" in source


def test_admin_dashboard_retires_unsupported_polling_and_operational_claims():
    source = ADMIN_DASHBOARD_PAGE.read_text(encoding="utf-8")

    for unsafe_component in (
        "axios",
        "/api/v1/alerts",
        "setInterval(",
        "Active Agents",
        "Total Users",
        "Operational",
        "All services running",
        "View All Alerts",
        "Go to Agents",
    ):
        assert unsafe_component not in source

    assert "Governed Administration Integration Pending" in source
    assert "authenticated role and tenant scope" in source
    assert "approval, audit, verification, and rollback lifecycles" in source


def test_terminal_chat_retires_unsupported_copilot_and_action_claims():
    source = TERMINAL_CHAT.read_text(encoding="utf-8")

    for unsafe_component in (
        "copilotService",
        "handleSendMessage",
        "getExplanation",
        "Show me active threats",
        "Check agent status",
        "Run playbook Alpha",
        "Ask PhantomNet AI",
    ):
        assert unsafe_component not in source

    assert "Governed Advisory AI Integration Pending" in source
    assert "evidence-minimized, tenant-scoped, provenance-linked inputs" in source
    assert "policy-gated and non-executing" in source
