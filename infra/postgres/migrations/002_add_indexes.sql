-- infra/postgres/migrations/002_add_indexes.sql
-- Migration: 002 Add Indexes

CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_session_tokens_jti ON session_tokens(jti);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_uuid ON agents(agent_uuid);
CREATE INDEX IF NOT EXISTS idx_blacklisted_ips_addr ON blacklisted_ips(ip_address);
