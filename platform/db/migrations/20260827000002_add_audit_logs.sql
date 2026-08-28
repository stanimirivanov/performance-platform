-- ============================================================================
-- Audit log table
-- ============================================================================
--
-- Tracks changes to run metadata for compliance and debugging.
--
-- This table is append‑only. Rows are never updated or deleted.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS audit;

CREATE TABLE audit.logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES metadata.test_runs(run_id),

    user_id TEXT,                                       -- who performed the action
    action TEXT,                                        -- e.g. 'update_status', 'create_run'
    resource_type TEXT,
    resource_id UUID,
    changes JSONB,                                      -- old/new values
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_logs_run ON audit.logs(run_id);
CREATE INDEX idx_audit_logs_action ON audit.logs(action);