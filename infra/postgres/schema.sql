-- infra/postgres/schema.sql
-- Consolidated PostgreSQL Database Schema for PhantomNet v4.0

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Tenants Table
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ NULL
);

-- 2. Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    role VARCHAR(50) DEFAULT 'analyst', -- admin, analyst, responder
    twofa_secret VARCHAR(100) NULL,
    is_twofa_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ NULL
);

-- 3. Session Tokens Table
CREATE TABLE IF NOT EXISTS session_tokens (
    id SERIAL PRIMARY KEY,
    jti VARCHAR(255) UNIQUE NOT NULL,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    is_valid BOOLEAN DEFAULT TRUE,
    revoked_at TIMESTAMPTZ NULL
);

-- 4. Password Reset Tokens
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    token_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    issued_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ NULL,
    ip_request VARCHAR(45) NOT NULL
);

-- 5. Blacklisted IPs Table
CREATE TABLE IF NOT EXISTS blacklisted_ips (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) UNIQUE NOT NULL,
    reason TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 6. Attack Logs Table
CREATE TABLE IF NOT EXISTS attack_logs (
    id SERIAL PRIMARY KEY,
    ip VARCHAR(45) NOT NULL,
    port INT NOT NULL,
    data TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Agents Table
CREATE TABLE IF NOT EXISTS agents (
    id SERIAL PRIMARY KEY,
    agent_uuid UUID UNIQUE DEFAULT uuid_generate_v4(),
    hostname VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    version VARCHAR(50) NOT NULL,
    location VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'offline',
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    quarantined BOOLEAN DEFAULT FALSE,
    configuration JSONB DEFAULT '{}'::jsonb,
    os VARCHAR(100) NULL,
    capabilities JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 8. Agent Keys Table
CREATE TABLE IF NOT EXISTS agent_keys (
    id SERIAL PRIMARY KEY,
    agent_id INT REFERENCES agents(id) ON DELETE CASCADE,
    public_key_pem TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    rotated_at TIMESTAMPTZ NULL,
    revoked_at TIMESTAMPTZ NULL
);

-- 9. Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    alert_id VARCHAR(255) UNIQUE NOT NULL,
    rule_id VARCHAR(255) NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    triggered_at TIMESTAMPTZ NOT NULL,
    severity VARCHAR(50) NOT NULL,
    details TEXT,
    raw_event JSONB,
    received_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 10. Normalized Events Table
CREATE TABLE IF NOT EXISTS normalized_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    source VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. Forensic Records Table
CREATE TABLE IF NOT EXISTS forensic_records (
    id SERIAL PRIMARY KEY,
    record_id VARCHAR(255) UNIQUE NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    results JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 12. Blockchain Transactions (conceptual ledger)
CREATE TABLE IF NOT EXISTS blockchain_transactions (
    id SERIAL PRIMARY KEY,
    alert_id INT REFERENCES alerts(id) ON DELETE SET NULL,
    normalized_event_id INT REFERENCES normalized_events(id) ON DELETE SET NULL,
    forensic_record_id INT REFERENCES forensic_records(id) ON DELETE SET NULL,
    data_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    transaction_hash VARCHAR(255) UNIQUE NOT NULL
);

-- 13. Case Incident Management Table
CREATE TABLE IF NOT EXISTS cases (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'new', -- new, in_progress, resolved, closed
    severity VARCHAR(50) DEFAULT 'medium', -- low, medium, high, critical
    assigned_to VARCHAR(150),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    timeline JSONB DEFAULT '[]'::jsonb,
    notes JSONB DEFAULT '[]'::jsonb,
    playbook_status JSONB DEFAULT '{}'::jsonb,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 14. Compliance Findings Table
CREATE TABLE IF NOT EXISTS compliance_findings (
    id SERIAL PRIMARY KEY,
    standard VARCHAR(100) NOT NULL, -- NIST, ISO27001, PCI-DSS
    section VARCHAR(100) NOT NULL,
    finding_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'non_compliant', -- compliant, non_compliant, manual_check
    description TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 15. Forensics Jobs & Evidence Tables
CREATE TABLE IF NOT EXISTS forensics_jobs (
    id SERIAL PRIMARY KEY,
    job_uuid UUID UNIQUE DEFAULT uuid_generate_v4(),
    agent_id INT REFERENCES agents(id) ON DELETE CASCADE,
    job_type VARCHAR(100) NOT NULL, -- memory_dump, disk_forensics, logs
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS forensics_evidence (
    id SERIAL PRIMARY KEY,
    job_id INT REFERENCES forensics_jobs(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    sha256_hash VARCHAR(64) NOT NULL,
    collected_at TIMESTAMPTZ DEFAULT NOW()
);

-- 16. Vulnerabilities & CVE Table
CREATE TABLE IF NOT EXISTS vulnerabilities (
    id SERIAL PRIMARY KEY,
    cve_id VARCHAR(50) UNIQUE NOT NULL,
    severity VARCHAR(50) NOT NULL,
    cvss_score FLOAT NOT NULL,
    description TEXT NOT NULL,
    remediation_status VARCHAR(100) DEFAULT 'unpatched',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 17. SOAR Playbooks & Runs Tables
CREATE TABLE IF NOT EXISTS soar_playbooks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    trigger JSONB NOT NULL,
    steps JSONB NOT NULL,
    context JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS soar_playbook_runs (
    id VARCHAR(255) PRIMARY KEY,
    playbook_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL, -- pending, running, completed, failed, requires_approval
    triggered_by JSONB NOT NULL,
    start_time TIMESTAMPTZ DEFAULT NOW(),
    end_time TIMESTAMPTZ NULL,
    current_context JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS soar_playbook_execution_logs (
    id SERIAL PRIMARY KEY,
    playbook_run_id VARCHAR(255) REFERENCES soar_playbook_runs(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    step_action VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    output JSONB DEFAULT '{}'::jsonb
);

-- Indexes for performance tuning
CREATE INDEX IF NOT EXISTS idx_alerts_tenant_id ON alerts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_agent_id ON alerts(agent_id);
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_session_tokens_jti ON session_tokens(jti);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_normalized_events_type ON normalized_events(event_type);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
