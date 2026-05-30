# PhantomNet v4.0 — API Reference

This document serves as the REST API reference for **PhantomNet v4.0** API Gateway and its corresponding internal microservices.

---

## 1. Authentication & Security

### 1.1 User Login
Authenticates users and returns a JWT access token.
- **Endpoint:** `POST /api/v1/auth/login`
- **Content-Type:** `application/json`
- **Request Body:**
  ```json
  {
    "username": "admin",
    "password": "admin-password"
  }
  ```
- **Success Response (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```

---

## 2. Agent Management API

### 2.1 Generate Agent Bootstrap Token
Generates a unique agent onboarding token. Must be called by an authenticated Admin user.
- **Endpoint:** `POST /api/v1/agents/bootstrap-token`
- **Headers:** `Authorization: Bearer <ADMIN_TOKEN>`
- **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "bootstrap_token": "boot-token-abc-123"
    }
  }
  ```

### 2.2 Register Telemetry Agent
Registers a new agent instance using a valid bootstrap token.
- **Endpoint:** `POST /api/v1/agents/register`
- **Content-Type:** `application/json`
- **Request Body:**
  ```json
  {
    "public_key": "key-agent-01-uuid",
    "bootstrap_token": "boot-token-abc-123",
    "os": "linux",
    "version": "4.0.0",
    "location": "prod-datacenter-us-east"
  }
  ```
- **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "agent_id": "agent-uuid-7729-aa"
    }
  }
  ```

---

## 3. SOAR Execution Engine

### 3.1 Execute SOAR Playbook
Triggers execution of an automated threat mitigation playbook.
- **Endpoint:** `POST /api/v1/soar/playbooks/{playbook_name}/execute`
- **Headers:** `Authorization: Bearer <ADMIN_TOKEN>`
- **Request Body:**
  ```json
  {
    "hostname": "prod_web_server_01",
    "source_ip": "192.168.4.15",
    "process_name": "encryptor.exe",
    "alert_id": "ALERT-RANSOMWARE-998"
  }
  ```
- **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "run_id": "run-uuid-8832-bc",
      "status": "completed"
    }
  }
  ```

---

## 4. Digital Forensics & Artifacts

### 4.1 Trigger Forensics Evidence Collection
Initiates target server forensic memory dumps and system log archives.
- **Endpoint:** `POST /api/v1/forensics/evidence/collect/`
- **Headers:** `Authorization: Bearer <ADMIN_TOKEN>`
- **Request Body:**
  ```json
  {
    "asset_id": "prod_web_server_01",
    "job_id": "JOB-FORENSICS-8839-2A",
    "artifact_types": ["memory_dump", "system_logs"],
    "collection_parameters": {
      "pcap_seconds": 60,
      "log_sources": ["auth.log", "syslog"]
    }
  }
  ```
- **Success Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "job_id": "JOB-FORENSICS-8839-2A",
      "status": "completed"
    }
  }
  ```
