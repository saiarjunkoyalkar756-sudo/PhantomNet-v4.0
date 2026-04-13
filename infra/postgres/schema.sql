CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,
    alert_id VARCHAR(255) UNIQUE NOT NULL,
    rule_id VARCHAR(255) NOT NULL,
    rule_name VARCHAR(255),
    agent_id VARCHAR(255) NOT NULL,
    triggered_at TIMESTAMPTZ NOT NULL,
    severity VARCHAR(50),
    details TEXT,
    raw_event JSONB, -- Optional: to store the event that triggered the alert
    received_at TIMESTAMPTZ DEFAULT NOW()
);
