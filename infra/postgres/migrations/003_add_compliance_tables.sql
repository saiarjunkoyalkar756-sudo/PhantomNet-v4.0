-- infra/postgres/migrations/003_add_compliance_tables.sql
-- Migration: 003 Add Compliance Tables

CREATE TABLE IF NOT EXISTS compliance_findings (
    id SERIAL PRIMARY KEY,
    standard VARCHAR(100) NOT NULL,
    section VARCHAR(100) NOT NULL,
    finding_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'non_compliant',
    description TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

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

CREATE INDEX IF NOT EXISTS idx_compliance_standard ON compliance_findings(standard);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_cve ON vulnerabilities(cve_id);
