# PhantomNet v4.0 — Operations Runbook

This operations runbook outlines standard procedures, troubleshooting steps, and maintenance guides for managing the **PhantomNet v4.0** distributed detection and response grid in production.

---

## 1. System Health Monitoring & Diagnostics

### 1.1 Core Health Endpoints
Each microservice in the PhantomNet ecosystem exposes a standard health endpoint `/health` and `/health_detailed`.
- **API Gateway:** `http://<gateway-host>:8000/health`
- **Alert Storage:** `http://<alert-storage-host>:8004/health_detailed`
- **Telemetry Ingestor:** `http://<ingestor-host>:8000/health`

### 1.2 Accessing Diagnostic Logs
All logs are standardized in JSON format and written to the `logs/` directory or stream to `stdout` under Docker Compose/Kubernetes.
- **View Gateway Logs:** `tail -f logs/api_gateway.log`
- **View Agent Logs:** `tail -f logs/agent.log`

---

## 2. Database Maintenance & Scaling

### 2.1 Database Scaling Procedures
- **Indexing optimization:** The primary PostgreSQL schema uses indexes on heavy lookup fields like `action`, `actor_id`, `event_id`, and `timestamp` in `audit_logs`, and `alert_id` in `alerts`.
- **Vertical Scaling:** When average query execution time exceeds 250ms, upgrade the database instance to high-memory instances (e.g. AWS `db.m6g.2xlarge`) to maximize buffer cache pool utilization.
- **Horizontal Read Scaling:** Deploy read-replicas for heavy dashboard queries, keeping write operations exclusively on the primary master.

### 2.2 Backup & Recovery Actions
#### Manual Database Backup:
```bash
docker exec -t phantomnet-postgres pg_dump -U phantomnet -d phantomnet_db -F c -b -v -f /backups/phantomnet_db_$(date +%F).backup
```
#### Database Restore:
```bash
docker exec -t phantomnet-postgres pg_restore -U phantomnet -d phantomnet_db -v "/backups/phantomnet_db_target.backup"
```

---

## 3. Kafka & Redpanda Event Streaming

### 3.1 Troubleshooting Kafka Consumer Lag
If alert processing is delayed, check the consumer group lags:
```bash
rpk group describe alert-storage-group
```
#### Remedy Procedures:
1. **Increase Partition Count:** If consumer lag is rising on the `alerts` topic, increase partition count from the standard default to match the number of active consumer replicas.
2. **Increase Telemetry Ingestor Scaling:** Deploy additional instances of `telemetry-ingestor` in the same consumer group.

---

## 4. Agent Lifecycle Operations

### 4.1 Agent Quarantine Procedures
If an agent exhibits anomalies or is suspected of compromise:
1. Access the API Gateway dashboard or use the CLI:
   ```bash
   curl -X POST http://localhost:8000/api/v1/agents/quarantine/<agent_id> -H "Authorization: Bearer <ADMIN_TOKEN>"
   ```
2. The orchestrator will immediately flag the agent's certificate as revoked in `revoked_certificates` and terminate active web sockets.

### 4.2 Restoring / Un-quarantining an Agent:
```bash
curl -X POST http://localhost:8000/api/v1/agents/restore/<agent_id> -H "Authorization: Bearer <ADMIN_TOKEN>"
```

---

## 5. Incident Response & Troubleshooting

### 5.1 Connection Refused on `/ingest`
- **Symptom:** Telemetry agent logs show connection retries and errors connecting to port `8000`.
- **Checklist:**
  1. Verify the `telemetry-ingestor` container is running: `docker ps | grep telemetry-ingestor`
  2. Verify the API Gateway is properly routing traffic: `curl -I http://localhost:8000/health`
  3. Inspect firewall rules allowing internal network routing on port `8000`.
