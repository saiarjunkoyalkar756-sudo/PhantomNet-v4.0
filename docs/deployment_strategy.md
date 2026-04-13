# Production Deployment Strategy for PhantomNet Platform

This document outlines a strategy for deploying the PhantomNet platform into a production environment, leveraging Docker for containerization and Kubernetes (K8s) for orchestration. The focus is on achieving high availability, scalability, security, and maintainability.

---

### 1. Core Principles

*   **Containerization:** All services are packaged as immutable Docker images.
*   **Orchestration:** Kubernetes is the chosen platform for managing containerized applications.
*   **Infrastructure as Code (IaC):** All infrastructure (Kubernetes manifests, cloud resources) should be defined as code using tools like Helm, Kustomize, or Terraform.
*   **Automation:** Continuous Integration/Continuous Deployment (CI/CD) pipelines are essential for reliable and rapid deployments.
*   **Observability:** Comprehensive monitoring, logging, and alerting are critical for operational excellence.
*   **Security by Design:** Security considerations are integrated at every layer, from network policies to secrets management.
*   **Scalability & High Availability:** Design for horizontal scaling and redundancy to ensure uninterrupted service.

---

### 2. Deployment Architecture (Kubernetes-centric)

```
+-------------------------------------------------------------------------------------------------------+
|                                        Cloud Provider (AWS, GCP, Azure)                               |
|                                                                                                       |
|  +-------------------------------------------------------------------------------------------------+  |
|  |                                        Kubernetes Cluster                                       |  |
|  |                                                                                                 |  |
|  |  +-------------------------------------------------------------------------------------------+  |  |
|  |  |                                        Ingress Controller (Nginx, Traefik)                |  |  |
|  |  |    (HTTPS)                                                                                |  |  |
|  |  +-------------------------------------------------------------------------------------------+  |  |
|  |       |                                                                                       ^  |  |
|  |       |                                                                                       |  |  |
|  |  +----v-------------------------------------------------------------------------------------+  |  |
|  |  |                                        API Gateway (FastAPI Service)                     |  |  |
|  |  |    - External API (HTTP/S)                                                              |  |  |
|  |  |    - WebSocket Entrypoint (WS/S)                                                        |  |  |
|  |  +------------------------------------------------------------------------------------------+  |  |
|  |       | (Internal gRPC/HTTP/S)                                                             |  |  |
|  |  +----v-------------------------------------------------------------------------------------+  |  |
|  |  |                                        Backend Microservices (Pods/Deployments)          |  |  |
|  |  |  [IAM-Service] [Alert-Storage] [Telemetry-Ingestor] [Event-Normalizer] [AI-Behavioral] [...] |  |  |
|  |  |                                                                                           |  |  |
|  |  +-------------------------------------------------------------------------------------------+  |  |
|  |       |                                                                                       ^  |  |
|  |       | (Kafka Protocol)                                                                      |  |  |
|  |  +----v-------------------------------------------------------------------------------------+  |  |
|  |  |                                        Kafka / Redpanda Cluster (StatefulSet)            |  |  |
|  |  |    - Event Bus for inter-service communication                                            |  |  |
|  |  +------------------------------------------------------------------------------------------+  |  |
|  |       |                                                                                       ^  |  |
|  |       | (PostgreSQL Protocol)                                                                 |  |  |
|  |  +----v-------------------------------------------------------------------------------------+  |  |
|  |  |                                        PostgreSQL (StatefulSet / Cloud SQL)              |  |  |
|  |  |    - Persistent Data Store (Alerts, Users, Tenants)                                       |  |  |
|  |  +------------------------------------------------------------------------------------------+  |  |
|  |                                                                                                 |  |
|  +-------------------------------------------------------------------------------------------------+  |
|                                                                                                       |
+-------------------------------------------------------------------------------------------------------+
          ^                                                                             ^
          | (HTTPS/WSS)                                                               | (Telemetry/Command)
+------------------------+                                                     +------------------------+
| Dashboard Frontend (Web) |                                                     | PhantomNet Agent       |
+------------------------+                                                     +------------------------+
```

---

### 3. Key Components & Considerations

#### 3.1. Container Images
*   **Build Process:** Use multi-stage Docker builds to create lean and secure images.
*   **Registry:** Store images in a private, secure container registry (e.g., Docker Hub private repos, AWS ECR, GCP GCR).
*   **Tagging:** Implement clear image tagging strategies (e.g., `git-sha`, `version`, `latest`).

#### 3.2. Kubernetes Configuration
*   **Namespaces:** Deploy services into dedicated namespaces for logical separation (e.g., `phantomnet-backend`, `phantomnet-data`).
*   **Deployments:** Use Kubernetes `Deployments` for stateless microservices to manage replica sets and rolling updates.
*   **StatefulSets:** Use `StatefulSets` for stateful components like Kafka/Redpanda, PostgreSQL, Redis, and Neo4j to ensure stable network identities and persistent storage. Alternatively, leverage managed cloud services (e.g., AWS RDS, GCP Cloud SQL, Azure Database for PostgreSQL).
*   **Services:** Define Kubernetes `Services` (ClusterIP, NodePort, LoadBalancer) to expose applications within and outside the cluster.
*   **ConfigMaps & Secrets:** Manage configuration (e.g., Kafka topics, database connection strings) using `ConfigMaps` and sensitive data (e.g., database passwords, JWT secret keys) using Kubernetes `Secrets`. External secrets management (e.g., HashiCorp Vault) is recommended for production.
*   **Resource Limits:** Define CPU and memory requests/limits for all containers to ensure resource fairness and prevent noisy neighbors.

#### 3.3. Networking & Security
*   **Ingress:** Use an Ingress Controller (e.g., Nginx Ingress, Traefik, AWS ALB Ingress Controller) to route external traffic to the API Gateway.
*   **TLS/SSL:** Enforce HTTPS/WSS for all external communication. Terminate TLS at the Ingress Controller or API Gateway. Use cert-manager for automated certificate provisioning.
*   **Network Policies:** Implement Kubernetes `NetworkPolicies` to restrict communication between pods to only what is strictly necessary (least privilege).
*   **Service Mesh (Optional):** Consider a service mesh (e.g., Istio, Linkerd) for advanced traffic management (routing, retries), mTLS between services, and enhanced observability.
*   **Zero Trust:** Implement mTLS between all microservices for strong authentication and encryption of internal traffic. Integrate agent identity with certificate-based authentication.

#### 3.4. Storage
*   **PersistentVolumeClaims (PVCs):** Use PVCs with appropriate StorageClasses for stateful components to ensure data persistence across pod restarts and rescheduling.
*   **Backup & Restore:** Implement a robust strategy for backing up and restoring all persistent data (e.g., PostgreSQL, Neo4j, Kafka logs).

#### 3.5. Observability Stack
*   **Logging:** Centralized structured logging (JSON format) from all containers. Collect logs using Fluentd/Fluent Bit and store them in a log aggregation system (e.g., Elasticsearch/OpenSearch, Loki).
*   **Metrics:** Prometheus for time-series metrics collection from all services (via `prometheus_client` exporters or native K8s metrics).
*   **Monitoring:** Grafana for dashboarding and visualization of metrics and logs.
*   **Alerting:** Alertmanager for routing alerts from Prometheus to appropriate notification channels.
*   **Distributed Tracing (Optional):** Jaeger/OpenTelemetry for end-to-end transaction tracing across microservices.

#### 3.6. Scalability & High Availability
*   **Horizontal Pod Autoscalers (HPAs):** Configure HPAs to automatically scale microservices based on CPU utilization or custom metrics.
*   **Node Autoscaling:** Enable cluster autoscaling to dynamically adjust the number of worker nodes based on demand.
*   **Pod Disruption Budgets (PDBs):** Define PDBs to ensure a minimum number of replicas are available during voluntary disruptions.
*   **Anti-Affinity:** Use pod anti-affinity to schedule replicas of critical services on different nodes for high availability.

#### 3.7. CI/CD & Automation
*   **GitOps:** Implement a GitOps workflow (e.g., using Argo CD, Flux CD) where all infrastructure and application deployments are managed via Git repositories.
*   **Pipelines:** Automate build, test, and deploy processes using tools like Jenkins, GitLab CI, GitHub Actions.

---

### 4. Agent Deployment

*   **Platform Specific:** Agents will have platform-specific installers (Windows, Linux, macOS).
*   **Secure Registration:** Agents will bootstrap using a secure, time-limited token and register with the backend to receive a signed certificate for mTLS and receive its `tenant_id`.
*   **Update Mechanism:** Implement an over-the-air (OTA) update mechanism for agents to securely push new versions or configuration.
*   **Fleet Management:** Backend services will provide APIs for managing agent fleets, their configurations, and their current status.

---
