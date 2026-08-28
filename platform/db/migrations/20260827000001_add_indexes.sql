-- ============================================================================
-- Indexes for query performance
-- ============================================================================
--
-- These indexes are applied after the initial schema to improve performance
-- for common query patterns such as filtering by status, environment fingerprint,
-- and joining resource snapshots with runs.
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_test_runs_status_start_time
    ON metadata.test_runs(status, start_time);

CREATE INDEX IF NOT EXISTS idx_environments_fingerprint_run
    ON metadata.environments(fingerprint_hash, run_id);

CREATE INDEX IF NOT EXISTS idx_resource_snapshots_test_phase
    ON metadata.resource_snapshots(test_phase, snapshot_time);

CREATE INDEX IF NOT EXISTS idx_correlation_events_type_phase
    ON metadata.correlation_events(event_type, phase_name);