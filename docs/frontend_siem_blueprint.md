# Frontend UI Blueprints for SIEM Layer

This document outlines conceptual new UI pages and components to be developed within the `dashboard_frontend/` to support the SIEM Layer capabilities.

---

## 1. Log Search & PhantomQL Query Interface (`/siem/search`)

**Objective:** Provide a powerful interface for SOC analysts to search, filter, and analyze normalized log data using PhantomQL.

**Key Components & Features:**

*   **PhantomQL Query Editor:**
    *   Large text area for entering PhantomQL queries.
    *   Syntax highlighting (conceptual).
    *   Autocomplete suggestions for fields and operators (conceptual).
    *   Time range selector (e.g., last 15 minutes, last 24 hours, custom range).
    *   "Run Query" button.
*   **Query Results Display:**
    *   Table view of `NormalizedLog` entries matching the query.
    *   Configurable columns (users can select which fields to display).
    *   Pagination and sorting.
    *   Drill-down capability: Click on a log entry to view full `full_data` in JSON format.
*   **Log Details Panel:**
    *   Displays all fields of a selected `NormalizedLog` entry.
    *   Contextual actions:
        *   "Enrich Indicator" (if `source_ip`, `destination_ip`, etc., are present, call `/threat-intel/lookup`).
        *   "Trigger Playbook" (if a rule is identified, suggest relevant playbooks from `/soar/playbooks`).
        *   "View Asset" (if `host_id` is present).
*   **Saved Queries:** Users can save, load, and share frequently used PhantomQL queries.

---

## 2. SIEM Dashboard & Analytics (`/siem/dashboard`)

**Objective:** Provide customizable dashboards with visualizations of aggregated log data for security monitoring and insights.

**Key Components & Features:**

*   **Dashboard Builder:**
    *   Drag-and-drop interface for adding, resizing, and arranging dashboard widgets.
    *   Widget library:
        *   Various chart types (line, bar, pie, scatter).
        *   Metric displays (single value).
        *   Table widgets.
        *   Geographical maps (for IP-based events).
    *   Each widget is configured with a PhantomQL query and visualization options (e.g., group by `event_type`, aggregate `count()`, time series data).
*   **Pre-built Dashboards:**
    *   Default dashboards for common use cases (e.g., "Login Activity", "Network Traffic Overview", "Endpoint Activity").
    *   Threat overview, showing high-severity events and trending threats.
*   **Drill-down & Interactivity:** Click on a chart element to filter the dashboard or drill down to log search.

---

## 3. Multi-Tenant Workspaces (`/settings/workspaces`)

**Objective:** Allow administrators to manage isolated workspaces for different tenants or departments.

**Key Components & Features:**

*   **Workspace List:**
    *   Table view of all configured `Workspace` objects.
    *   Columns: Workspace ID, Name, Description, Owner.
    *   Actions: Create New, Edit, Delete.
*   **Workspace Detail/Editor:**
    *   Form for creating/editing a `Workspace`.
    *   Fields for Name, Description, Owner.
    *   User/Role assignment to the workspace (RBAC integration conceptual).
*   **Workspace Selector:**
    *   A prominent UI element (e.g., dropdown in the header) allowing users to switch between accessible workspaces, ensuring data isolation.

---

## Technical Considerations for Frontend Developers:

*   **API Endpoints:** Frontend will interact with `/siem/ingest`, `/siem/query`, `/siem/workspaces`, etc.
*   **Real-time Updates:** Consider WebSockets for live updates on dashboards or query results, especially for high-volume environments.
*   **Security:** Enforce RBAC and multi-tenancy rules rigorously. Users should only see data and workspaces they are authorized for.
*   **Performance:** Queries against large log datasets require optimized backend queries and potentially lazy loading/server-side pagination for frontend tables.
