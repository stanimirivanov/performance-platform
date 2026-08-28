-- ============================================================================
-- Add unique constraint on environments.run_id
-- ============================================================================
--
-- Enforce a one-to-one relationship between test_runs and environments.
-- The initial schema allowed multiple environment rows per run (unique on
-- run_id, fingerprint_hash). This migration makes run_id unique, matching the
-- intended design where each run has at most one environment snapshot.
--
-- IMPORTANT:
--   Before running this migration, ensure that no duplicate run_id values
--   exist in metadata.environments. If duplicates are present, the ALTER
--   statement will fail with a unique violation. Clean up any duplicates
--   manually (e.g., by keeping only the most recent or canonical row) before
--   applying this change.
-- ============================================================================

ALTER TABLE metadata.environments
    ADD CONSTRAINT unique_run_id UNIQUE (run_id);
