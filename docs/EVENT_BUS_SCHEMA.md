# Internal Event Bus Schema and Topics Documentation

This document defines the schema and topics for the core data flows traversing the internal event bus within the PhantomNet microservice architecture. The event bus is designed for asynchronous, decoupled communication between services, facilitating scalability and resilience. Apache Kafka is the chosen technology for the event bus.

---

## 1. Event Bus Topics

The following topics are defined for publishing and consuming events:

*   **`phantomnet.raw_telemetry`**: For raw, unvalidated telemetry data ingested directly from agents.
*   **`phantomnet.processed_telemetry`**: For normalized, enriched, and validated telemetry data ready for AI analysis.
*   **`phantomnet.threat_alerts`**: For identified threat alerts, anomalies, and correlation findings.
*   **`phantomnet.policy_changes`**: For updates to security policies and rules.
*   **`phantomnet.agent_status`**: For lifecycle and health status updates from PhantomNet agents.
*   **`phantomnet.dashboard_alerts`**: For high-priority alerts intended for real-time display on the dashboard.
*   **`phantomnet.soar_triggers`**: For alerts or events specifically intended to trigger SOAR playbooks.

---

## 2. Event Schemas (JSON/Avro-like structure)

All events are expected to adhere to a common envelope structure, but their `data` payload will vary based on the event type and topic.

### 2.1. Raw Telemetry Event Schema (`phantomnet.raw_telemetry`)

*   **Description:** Represents a raw log entry or telemetry data point received directly from a PhantomNet Agent.
*   **Publisher:** `PN_Telemetry_Ingest`
*   **Consumer:** `PN_Data_Processor`
*   **Schema:**
    ```json
    {
        "id": "string (UUID)",
        "timestamp": "float (Unix timestamp)",
        "source": "string (e.g., 'AgentX', 'SyslogCollector')",
        "type": "string (e.g., 'syslog', 'json_log', 'packet_capture')",
        "data": "object (arbitrary JSON structure of parsed raw data)",
        "raw_log": "string (optional, original raw log string if available)"
    }
    ```
*   **Notes:** This schema directly maps to the `RawEvent` Pydantic model found in `backend_api/schemas.py`. The `data` field contains the key-value pairs extracted by the log parsers.

### 2.2. Processed Telemetry Event Schema (`phantomnet.processed_telemetry`)

*   **Description:** Represents telemetry data after normalization, enrichment, and validation by the `PN_Data_Processor`. This is structured for efficient AI analysis.
*   **Publisher:** `PN_Data_Processor`
*   **Consumer:** `PN_AI_Detector`
*   **Schema:**
    ```json
    {
        "event_id": "string (UUID, matches raw_event.id)",
        "timestamp": "float (Unix timestamp)",
        "source": "string (original source of the raw event)",
        "event_type": "string (normalized event type, e.g., 'network_connection', 'process_creation')",
        "raw_data": "string (original raw log or JSON representation of raw data)",
        "metadata": "object (original parsed data, plus enrichment data like asset_info, user_info, geo_ip)",
        "host_name": "string (optional, normalized hostname)",
        "user_name": "string (optional, normalized username)",
        "src_ip": "string (optional, normalized source IP address)",
        "dest_ip": "string (optional, normalized destination IP address)",
        "src_port": "integer (optional)",
        "dest_port": "integer (optional)",
        "process_name": "string (optional)",
        "file_path": "string (optional)"
    }
    ```
*   **Notes:** This schema directly maps to the `NormalizedEvent` Pydantic model found in `backend_api/schemas.py`. Enrichment data is stored within the `metadata` field.

### 2.3. Threat Alert Event Schema (`phantomnet.threat_alerts`)

*   **Description:** Represents a detected security threat or anomaly, potentially correlated from multiple events.
*   **Publisher:** `PN_AI_Detector` (and possibly `PN_Alert_Manager` after further processing)
*   **Consumer:** `PN_Alert_Manager`, `PN_SOAR_Engine`
*   **Schema:**
    ```json
    {
        "id": "string (UUID, can match a raw_event.id or be a new correlation ID)",
        "timestamp": "float (Unix timestamp of alert generation)",
        "source": "string (e.g., 'PN_AI_Detector', 'RuleEngine')",
        "type": "string (e.g., 'brute_force_attempt', 'malware_detection', 'slow_data_exfiltration', 'threat_intelligence_match')",
        "data": "object (event data that triggered the alert)",
        "correlation_id": "string (UUID, links related events or alerts)",
        "related_events": "array of strings (UUIDs of events contributing to this alert)",
        "severity": "string (e.g., 'low', 'medium', 'high', 'critical')",
        "ai_score": "float (0.0-1.0, AI's confidence in the alert)",
        "action_recommendation": "string (optional, suggested response action)",
        "raw_log": "string (optional, raw log if directly relevant)",
        "metadata": "object (any additional contextual info, e.g., UEBA findings, TI match details)"
    }
    ```
*   **Notes:** This schema directly maps to the `CorrelatedEvent` Pydantic model found in `backend_api/schemas.py`.

### 2.4. Policy Change Event Schema (`phantomnet.policy_changes`)

*   **Description:** Notifies services about updates, additions, or deletions of security policies or configuration rules.
*   **Publisher:** `PN_Policy_Engine`
*   **Consumer:** `PN_Agent_Manager`, `PN_AI_Detector`
*   **Schema:**
    ```json
    {
        "id": "string (UUID)",
        "timestamp": "float (Unix timestamp)",
        "policy_id": "string (ID of the policy changed)",
        "change_type": "string (e.g., 'created', 'updated', 'deleted')",
        "policy_type": "string (e.g., 'agent_behavior', 'detection_rule', 'soar_playbook')",
        "details": "object (specific changes or new policy content)"
    }
    ```

### 2.5. Agent Status Update Event Schema (`phantomnet.agent_status`)

*   **Description:** Communicates the current operational status, health, and metadata of a PhantomNet Agent.
*   **Publisher:** `PN_Agent_Manager` (based on agent heartbeats or direct registration)
*   **Consumer:** `PN_Dashboard_Backend`
*   **Schema:**
    ```json
    {
        "id": "string (UUID of the agent)",
        "timestamp": "float (Unix timestamp)",
        "status": "string (e.g., 'online', 'offline', 'degraded')",
        "hostname": "string (agent's reported hostname)",
        "ip_address": "string (agent's primary IP address)",
        "version": "string (agent software version)",
        "health_metrics": "object (e.g., {'cpu_util': 0.15, 'mem_util': 0.60})",
        "last_seen": "float (Unix timestamp of last communication)"
    }
    ```

### 2.6. High-Priority Dashboard Alert Event Schema (`phantomnet.dashboard_alerts`)

*   **Description:** A subset of `phantomnet.threat_alerts` or other critical events specifically formatted for immediate display and real-time updates on the `PN_Dashboard_Frontend`.
*   **Publisher:** `PN_Alert_Manager`
*   **Consumer:** `PN_Dashboard_Backend` (which then broadcasts via WebSocket to Frontend)
*   **Schema:**
    ```json
    {
        "alert_id": "string (UUID, matches corresponding threat_alert id)",
        "timestamp": "float (Unix timestamp)",
        "title": "string (brief, human-readable alert title)",
        "description": "string (short summary of the alert)",
        "severity": "string (e.g., 'high', 'critical')",
        "type": "string (alert type, e.g., 'brute_force_attempt')",
        "source": "string (originating service/component)",
        "entity_impacted": "string (optional, e.g., 'host:server_1', 'user:admin')",
        "link_to_details": "string (URL to dashboard view for full alert details)"
    }
    ```
*   **Notes:** This schema is typically a distilled version of `Threat Alert Event` for UI efficiency.

### 2.7. SOAR Trigger Event Schema (`phantomnet.soar_triggers`)

*   **Description:** Events specifically designed to trigger playbooks in the `PN_SOAR_Engine`. These often originate from `PN_Alert_Manager` for automated responses or from manual user actions.
*   **Publisher:** `PN_Alert_Manager`, `PN_SOAR_Engine` (for internal playbook chaining), `PN_Dashboard_Backend` (for manual triggers).
*   **Consumer:** `PN_SOAR_Engine`
*   **Schema:**
    ```json
    {
        "trigger_id": "string (UUID)",
        "timestamp": "float (Unix timestamp)",
        "playbook_name": "string (name of the playbook to trigger)",
        "event_data": "object (contextual data for the playbook, e.g., the alert that triggered it)",
        "source_service": "string (e.g., 'PN_Alert_Manager', 'PN_Dashboard_Frontend')",
        "priority": "string (e.g., 'high', 'medium')",
        "metadata": "object (additional metadata for SOAR execution)"
    }
    ```
*   **Notes:** This schema closely aligns with the expected input for `PN_SOAR_Engine`'s `callback` function.

---

## 3. Serialization Format

All event messages will be serialized using **JSON (JavaScript Object Notation)** due to its wide compatibility, human-readability, and efficient parsing across various programming languages and platforms. While Avro or Protobuf might offer more strict schema evolution, JSON provides greater flexibility for the MVP.

---

## 4. Schema Evolution

Schemas will evolve over time. Changes will be managed through:
*   **Additive-only changes:** New fields can be added, but existing fields should not be removed or have their types drastically changed.
*   **Versioning:** Major changes might necessitate new topic versions (e.g., `phantomnet.raw_telemetry.v2`).
*   **Documentation:** All changes to schemas and topics will be reflected in this document.
