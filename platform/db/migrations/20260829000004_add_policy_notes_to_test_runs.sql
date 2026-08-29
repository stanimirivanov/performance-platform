-- ============================================================================
-- Add policy_version and notes to test_runs
-- ============================================================================
--
-- The initial schema omitted these columns, but they are required by the
-- application's Pydantic schemas (RunCreate/RunResponse). This migration
-- aligns the database with the expected model.
-- ============================================================================

ALTER TABLE metadata.test_runs
    ADD COLUMN policy_version TEXT,
    ADD COLUMN notes TEXT;