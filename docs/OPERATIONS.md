# PhantomNet Platform Operations Guide

This document provides essential operational guidance for deploying, monitoring, and maintaining the PhantomNet Autonomous Cyber Defense Platform. It covers monitoring strategies, log management, and Service Level Objectives (SLOs).

## 1. Monitoring

Effective monitoring is crucial for ensuring the health, performance, and security of the PhantomNet platform.

### 1.1 Key Metrics to Monitor

*   **Agent Health:**
    *   **Agent Status:** Online/Offline, Quarantined.
    *   **Last Seen:** Timestamp of the last heartbeat from each agent.
    *   **Self-Healing Status:** `self_healing_enabled`, `safe_mode_active`.
    *   **OS & Capabilities:** Track agent OS and reported capabilities.
    *   **Component Health:** Status of individual collectors and modules (e.g., Network Sensor, Process Monitor).
    *   **Resource Utilization:** CPU, Memory, Disk usage reported by agents.
*   **Backend Service Health:**
    *   **Service Uptime:** Ensure all FastAPI microservices (Gateway, PNQL Engine, etc.) are running.
    *   **Resource Utilization:** CPU, Memory, Network I/O of backend containers/processes.
    *   **API Latency & Error Rates:** Monitor response times and errors for critical API endpoints.
    *   **Queue Depths:** Monitor RabbitMQ/Kafka queue sizes for backlogs.
    *   **Database Performance:** Latency and error rates for PostgreSQL, Redis, Neo4j.
*   **Security Metrics:**
    *   **Alert Volume:** Number of security alerts generated per hour/day.
    *   **False Positive Rate:** Monitor and tune detection mechanisms.
    *   **Remediation Success Rate:** Percentage of automatically remediated issues.
    *   **Patch Application Rate:** Track successful patch deployments across agents.
    *   **Threat Detections:** Number and type of threats detected.

### 1.2 Monitoring Tools

*   **Prometheus & Grafana:** For collecting, storing, and visualizing time-series metrics from both agents and backend services. PhantomNet services can expose `/metrics` endpoints.
*   **Centralized Logging (ELK Stack/Splunk):** For aggregating and analyzing logs from all components.
*   **Cloud Provider Monitoring:** For cloud-deployed components (e.g., AWS CloudWatch, Azure Monitor).

## 2. Log Management

Logs are critical for troubleshooting, auditing, and security investigations.

### 2.1 Log Locations

*   **PhantomNet Agent:**
    *   **Linux:** `journalctl -u phantomnet-agent.service` (for service logs), or `/var/log/phantomnet-agent/` (for application logs if configured).
    *   **Windows:** `phantomnet_agent\logs\phantomnet_agent_service_wrapper.log` and `backend_api\logs\phantomnet_backend_service_wrapper.log`.
    *   **Termux:** `phantomnet_agent/logs/agent_stdout.log`, `phantomnet_agent/logs/agent_stderr.log`.
*   **PhantomNet Backend Services:**
    *   Logs are typically directed to `stdout`/`stderr` of the Docker containers or systemd services. Use `docker compose logs` or `journalctl -u phantomnet-backend.service`.
    *   Individual microservices (`backend_api/event_stream_processor`, etc.) also generate their own internal logs.

### 2.2 Log Levels

Logs can be configured with different verbosity levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
Adjust log levels in configuration files (`config/agent.yml`, backend service environment variables) as needed for troubleshooting vs. production.

### 2.3 Centralized Logging

For production environments, it is highly recommended to integrate all PhantomNet logs with a centralized logging solution (e.g., ELK Stack, Splunk, Graylog). The agent's `LogForwarder` can push logs to a backend endpoint.

## 3. Service Level Objectives (SLOs)

These are example SLOs. Actual values should be defined based on business requirements and observed performance.

### 3.1 Availability

*   **Agent Availability:** 99.9% of registered agents reporting a healthy status (online, self-healing enabled) to the backend over a 7-day period.
*   **Backend API Availability:** 99.99% of requests to critical API endpoints (e.g., `/health`, `/agents/heartbeat`, `/alerts`) returning a successful response within a 30-day period.

### 3.2 Latency

*   **Agent Heartbeat Latency:** Median latency for agents to report heartbeats to the backend should be less than 5 seconds. 99th percentile less than 15 seconds.
*   **Alert Processing Latency:** Critical security alerts should be processed and available for viewing/action within 60 seconds from agent detection.

### 3.3 Throughput

*   **Telemetry Ingestion Rate:** The backend should be able to ingest and process at least 1000 raw events per second without significant queue backlogs.

### 3.4 Reliability

*   **Data Freshness:** Telemetry data from agents should be no older than 30 seconds from the last reported timestamp.
*   **Remediation Success Rate:** 95% of automatically remediated `SEV3` or lower issues should be successfully resolved without manual intervention.

## 4. On-Call Procedures / Runbooks

*   **Alerts Triggered:**
    *   **Agent Offline:** Investigate agent connectivity, host status, and agent service logs. Attempt remote restart if possible.
    *   **Backend Service Down:** Check `docker compose logs` or `journalctl` for backend services. Restart affected services.
    *   **High Alert Volume:** Investigate root cause (e.g., actual attack, misconfiguration, sensor malfunction).
    *   **Remediation Failure:** Review self-healing logs (agent-side), investigate why auto-fix failed. Escalate for manual intervention.
*   **Deployment & Upgrades:**
    *   Follow documented installation/upgrade procedures for each platform.
    *   Perform upgrades in a staged manner (dev -> staging -> production).
    *   Monitor key metrics closely after upgrades.
*   **Disaster Recovery:**
    *   Ensure regular backups of all critical data (PostgreSQL, Neo4j, Redis persistence).
    *   Have a documented recovery plan for restoring services in case of a major outage.
