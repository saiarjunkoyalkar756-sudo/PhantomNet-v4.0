-- infra/postgres/migrations/004_add_forensics_tables.sql
-- Migration: 004 Add Forensics Tables

CREATE TABLE IF NOT EXISTS forensics_jobs (
    id SERIAL PRIMARY KEY,
    job_uuid UUID UNIQUE DEFAULT uuid_generate_v4(),
    agent_id INT REFERENCES agents(id) ON DELETE CASCADE,
    job_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
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

CREATE INDEX IF NOT EXISTS idx_forensics_jobs_uuid ON forensics_jobs(job_uuid);
CREATE INDEX IF NOT EXISTS idx_forensics_evidence_hash ON forensics_evidence(sha256_hash);
