# Multi-Tenancy Upgrade Plan

This document outlines the multi-tenancy model implemented in PhantomNet, enabling the platform to securely serve multiple independent organizations (tenants) from a shared infrastructure. It details the current implementation and proposes future enhancements for a robust enterprise solution.

---

### 1. Multi-Tenancy Model: Tenant-Isolated Data

PhantomNet employs a tenant-isolated data model, primarily using a shared database (PostgreSQL) and shared Kafka/Redpanda clusters, with strict `tenant_id` filtering at the application layer.

#### 1.1. Tenant Identification & Propagation

*   **Tenant Definition:** A `Tenant` entity is introduced in the shared database (PostgreSQL) with a unique `UUID` as its primary identifier.
*   **User Association:** Every `User` is explicitly linked to a `Tenant` via a `tenant_id` foreign key in the `users` table.
*   **Agent Association:** In future iterations, each PhantomNet Agent will be associated with a `tenant_id` during its registration process. For now, agents default to a hardcoded `DEFAULT_TENANT_ID` (0000...).
*   **JWT Propagation:** Upon successful user login (`iam-service`), the user's `tenant_id` is embedded into the JSON Web Token (JWT) payload. This `tenant_id` is then extracted by API endpoints (e.g., `gateway-service`) to enforce data isolation.
*   **Event Propagation:** All events (telemetry, normalized, alerts, commands) flowing through the Kafka/Redpanda event stream are tagged with a `tenant_id`.

#### 1.2. Data Isolation in PostgreSQL

*   **Row-Level Filtering:** For all tenant-sensitive data tables (e.g., `alerts`), a `tenant_id` column has been added.
*   **Application Layer Enforcement:** API endpoints (e.g., `/api/v1/alerts` in `gateway-service`) now explicitly filter query results based on the `tenant_id` extracted from the authenticated user's JWT. A user can only view or manage data belonging to their associated tenant.
*   **Foreign Key Constraints:** `tenant_id` is enforced as a `NOT NULL` field and a foreign key, ensuring referential integrity and preventing orphaned data.

#### 1.3. Data Isolation in Kafka/Redpanda Event Stream

*   **Event Tagging:** All event types (`TelemetryEvent`, `NormalizedEvent`, `Alert`, `AgentCommandPayload`) now include a `tenant_id` field.
*   **Producer Enforcement:** Producers (e.g., `telemetry-ingestor`, `event-normalizer`, `ai-behavioral-engine`) inject the `tenant_id` into the message payload.
*   **Consumer Filtering:** Consumers are designed to process only messages relevant to their context. Agents listen for commands specifically for their `agent_id` AND `tenant_id`. Backend services processing events would typically group or filter by `tenant_id`.

---

### 2. Current Implementation Status

*   **Database Schema:** `tenants` table added; `tenant_id` added to `users` and `alerts` tables.
*   **IAM Service:** User registration assigns `DEFAULT_TENANT_ID`; JWTs contain `tenant_id`.
*   **API Gateway:** Alert retrieval (`/api/v1/alerts`) filters by user's `tenant_id`; Agent command endpoint (`/api/v1/agents/{agent_id}/command`) includes `tenant_id` in Kafka message.
*   **Telemetry Ingestor:** `TelemetryEvent` includes `tenant_id` (defaulted).
*   **Event Normalizer:** Propagates `tenant_id` from raw events to normalized events.
*   **AI Behavioral Engine:** Processes `tenant_id` in normalized events and includes it in generated alerts.
*   **Alert Storage:** Stores `tenant_id` with alerts in PostgreSQL.
*   **WebSocket Manager:** Broadcasts alerts that contain `tenant_id`. Frontend clients are responsible for filtering for their tenant's alerts.

---

### 3. Future Enhancements & Considerations

*   **Dynamic Tenant Provisioning:** Implement an administrative API/UI for creating and managing new tenants, rather than relying on hardcoded `DEFAULT_TENANT_ID`. This includes:
    *   Tenant creation with unique `tenant_id`.
    *   Association of new users/agents with specific tenants during their respective registration flows.
*   **Tenant-Specific Kafka Topics:** For higher isolation and clearer separation, consider dynamic creation or allocation of tenant-specific Kafka topics (e.g., `telemetry-events-<tenant_id>`). This would require more advanced Kafka administration and dynamic configuration of consumers/producers.
*   **Agent Tenant Assignment:** Integrate `tenant_id` into the agent registration process so agents report their actual tenant affiliation, replacing the hardcoded default.
*   **User/Agent Management APIs:** Develop comprehensive APIs for administrators to manage users (roles, 2FA, tenant assignment) and agents (enrollment, configuration, approval) within specific tenants.
*   **Tenant-Aware Resource Limits:** Implement per-tenant resource quotas (e.g., data storage, event volume, agent count).
*   **Frontend Filtering:** Enhance frontend components to explicitly filter received WebSocket events and API responses by the currently logged-in user's `tenant_id`, providing client-side assurance of data isolation.
*   **Policy & Configuration:** Implement tenant-specific security policies and agent configurations that can be managed by tenant administrators.
*   **Cross-Tenant Auditability:** Develop mechanisms for a super-admin role to audit activities across tenants (e.g., for compliance or support purposes), while strictly maintaining tenant data isolation for regular operations.
