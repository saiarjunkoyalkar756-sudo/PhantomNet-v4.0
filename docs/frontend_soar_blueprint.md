# Frontend UI Blueprints for Autonomous SOAR 2.0

This document outlines conceptual new UI pages and components to be developed within the `dashboard_frontend/` to support the Autonomous SOAR 2.0 capabilities.

---

## 1. Playbook Management (`/playbooks`)

**Objective:** Allow users to create, edit, manage, and AI-generate SOAR playbooks.

**Key Components & Features:**

*   **Playbook List View:**
    *   Table/Card view of all loaded playbooks (Name, Description, Trigger, Version, Last Updated).
    *   Actions: View Details, Edit, Duplicate, Delete, Run Manually.
    *   Search/Filter capabilities.
*   **Playbook Detail/Editor View:**
    *   **Basic Info:** Playbook Name, Description, Trigger Configuration (event type, conditions).
    *   **Step Editor (Flow-based Visual Builder - Conceptual):**
        *   Drag-and-drop interface for adding, reordering, and configuring playbook steps.
        *   Each step block represents a `PlaybookStep` with fields for:
            *   `action` (dropdown of `RemediationAction` enum).
            *   `tool_name` (dropdown of available external tools like EDR, Firewall, ThreatIntel).
            *   `parameters` (dynamic form based on selected action/tool, supporting context variable injection like `{incident.source_ip}`).
            *   `condition` (text input for JINJA2-like expression).
            *   `requires_approval` (toggle).
            *   `description`.
            *   `output_to`.
        *   Visual representation of flow, including conditional branches.
    *   **AI Playbook Generation Button:**
        *   A button/modal to prompt the AI (e.g., "Generate playbook for phishing incident") which calls `/soar/playbooks/generate`.
        *   Displays the AI-generated playbook for review and saving.
    *   **Version Control (Conceptual):** Basic versioning or history of playbook changes.

---

## 2. Incident Response Console (`/incidents/{incident_id}/soar-timeline`)

**Objective:** Visualize the execution of a playbook for a specific incident, including approval requests.

**Key Components & Features:**

*   **Playbook Run Timeline:**
    *   Chronological display of `PlaybookExecutionLog` entries for a specific `PlaybookRun`.
    *   Each log entry shows: Step Description, Timestamp, Status (Pending, In Progress, Completed, Failed, Skipped, Requires Approval, Approved, Rejected), Output/Details.
    *   Visual indicators for step status (colors, icons).
*   **Approval Request Widget:**
    *   If a step has `PlaybookStatus.REQUIRES_APPROVAL`, a prominent widget appears.
    *   Displays `ApprovalRequest` details: Step Description, Context Snapshot (key incident details, parameters of the pending step), Who requested, When.
    *   Buttons: "Approve" (`POST /soar/approvals/{request_id}/approve`), "Reject" (`POST /soar/approvals/{request_id}/reject`).
    *   Text field for adding a reason/comment.
*   **Context Viewer:** Displays the evolving `current_context` of the `PlaybookRun`.

---

## 3. Automated Actions Log (`/automated-actions`)

**Objective:** Provide a centralized view of all automated actions performed by the SOAR engine.

**Key Components & Features:**

*   **Table View:**
    *   List all `PlaybookRun` instances, potentially aggregated by incident.
    *   Columns: Run ID, Playbook Name, Triggered By (incident ID/event type), Start Time, End Time, Final Status.
    *   Search/Filter by status, playbook name, incident ID.
    *   Clickable Run ID to navigate to the detailed Incident Response Console.
*   **Statistics/Overview:**
    *   Charts showing: Number of playbooks executed, success rate, most frequent playbooks, average execution time.
    *   Breakdown by remediation action types.

---

## Technical Considerations for Frontend Developers:

*   **API Endpoints:** Frontend will interact with `/soar/playbooks`, `/soar/playbooks/{name}/execute`, `/soar/playbook_runs/{run_id}`, `/soar/approvals`, etc., as exposed by the Gateway.
*   **Real-time Updates:** Consider using WebSockets for live updates on `PlaybookRun` status changes and new approval requests.
*   **Context Variable Resolution:** The frontend editor for playbook steps should offer a way to inject and validate context variables (e.g., `{incident.source_ip}`).
*   **Security:** Ensure proper RBAC is enforced for playbook creation/editing/execution and approval actions.
