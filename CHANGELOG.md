# Changelog

## [Unreleased] - 2025-12-12

### Added

-   **Backend Microservices:**
    -   **Autonomous SOAR 2.0:** Added `soar_playbook_engine`, `playbook_flow_builder`, and `auto_response_engine` for advanced SOAR capabilities.
    -   **Autonomous Vulnerability Management:** Added `vulnerability_management_service`, `cve_resolver`, and `patch_recommendation_ai` for asset and vulnerability management.
    -   **SIEM Layer:** Added `siem_ingest_service`, `log_normalizer`, and `phantomql_engine` for log ingestion, normalization, and querying.
    -   **PhantomNet SOC AI Copilot:** Added `soc_copilot_service` with a `context_builder` for AI-powered assistance.
    -   **Lateral Movement & Attack Path Mapping:** Added `attack_graph_engine` and `lateral_movement_detector` for graph-based analysis.
    -   **Automated Forensics Engine:** Added `forensics_engine` with `timeline_builder` and `evidence_collector` for automated investigations.
    -   **Compliance & Audit Module:** Added `compliance_service` and `audit_log_collector` for compliance management.
-   **Frontend:**
    -   Created placeholder pages and routes for all new feature blocks.
    -   Implemented basic UI components for SOAR, Vulnerability Management, and SIEM.
-   **Agent:**
    -   Added a `SoftwareCollector` for gathering software inventory.
-   **Deployment:**
    -   Added `Dockerfile`s for all new backend services.
    -   Updated `docker-compose.yml` to include all new services.
    -   Created `install_backend.sh` and `install_agent.sh` for easier installation.
    -   Provided installation notes for Windows and Termux.
-   **Documentation:**
    -   Created a central `DOCUMENTATION.md` hub.
    -   Added `ARCHITECTURE.md`, `API_DOCUMENTATION.md`, and `DEPLOYMENT_GUIDE.md`.

### Fixed

-   **Backend:**
    -   Refactored the logging system to use `loguru` with a thread-safe async queue.
    -   Implemented `SAFE_MODE` for `threat-intelligence-service` and `ai-behavioral-engine` to handle missing dependencies (Redis, Kafka, ML models).
    -   Added a robust WebSocket log broadcaster with a polling fallback.
-   **Frontend:**
    -   Fixed the API endpoint URL in the Login page.
    -   Corrected the `VITE_API_URL` in the `.env` file.
    -   Replaced simulated AI responses in `TerminalChat` with real API calls.
-   **Agent:**
    -   The `network_collector` now gracefully handles non-root environments by providing a `scapy` fallback.

### Changed

-   The main backend application (`gateway_service/main.py`) has been updated to include routers for all new services.
-   The agent's main entry point (`phantomnet_agent/main.py`) has been updated to include the new `SoftwareCollector`.
