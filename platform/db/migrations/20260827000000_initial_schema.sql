-- ============================================================================
-- Run Metadata – Initial Schema
-- ============================================================================
--
-- This migration creates the core tables for storing performance test run
-- metadata, environment fingerprints, resource snapshots, and correlation events.
--
-- Tables are placed in the `metadata` schema to separate them from other
-- application schemas.
--
-- All tables use UUID primary keys with default generation via `gen_random_uuid()`.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- Schema setup
-- ----------------------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS metadata;
SET search_path TO metadata, public;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ----------------------------------------------------------------------------
-- 1. test_runs – Core run identity and summary
-- ----------------------------------------------------------------------------
--
-- Each row represents a single performance test run.
--
-- The `run_id` is the stable identifier used everywhere else. It is generated
-- by the application and stored here as a UUID to avoid collision and allow
-- distributed generation.
--
-- Fields `start_time`, `end_time`, and `duration_seconds` are set by the test
-- runner. The status enum tracks the run's progress through the test pipeline.
--
-- Thresholds and parameters are stored as JSONB because their structure varies
-- by test type and profile.
-- ============================================================================

CREATE TYPE metadata.test_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'cancelled',
    'timeout'
);

CREATE TABLE metadata.test_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    test_name TEXT NOT NULL,                            -- e.g. "checkout-api"
    test_script TEXT,                                   -- path or identifier
    test_profile TEXT,                                  -- e.g. "regression", "smoke"
    status metadata.test_status NOT NULL DEFAULT 'pending',

    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    duration_seconds INTEGER CHECK (duration_seconds >= 0),

    thresholds JSONB,                                   -- e.g. {"p95": 100, "p99": 200}
    parameters JSONB,                                   -- arbitrary test parameters
    tags TEXT[],                                        -- array of tags for filtering

    -- Trigger information
    triggered_by TEXT,                                  -- user or system that started the run
    trigger_type TEXT,                                  -- 'manual', 'ci', 'schedule', etc.
    ci_build_id TEXT,
    ci_job_id TEXT,

    -- Performance summary (populated after test completes)
    success_rate FLOAT,                                 -- 0.0 .. 1.0
    average_response_time_ms FLOAT,
    percentiles JSONB,                                  -- e.g. {"p50": 50, "p95": 95, "p99": 99}
    error_count INTEGER DEFAULT 0,
    total_requests INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_test_runs_status ON metadata.test_runs(status);
CREATE INDEX idx_test_runs_start_time ON metadata.test_runs(start_time);
CREATE INDEX idx_test_runs_created_at ON metadata.test_runs(created_at);


-- ----------------------------------------------------------------------------
-- 2. environments – Canonical environment fingerprints
-- ----------------------------------------------------------------------------
--
-- This table stores the environment signature for each run. The `fingerprint`
-- is a SHA256 hash of a canonical set of environment characteristics (cluster
-- name, Kubernetes version, node OS, container runtime, etc.).
--
-- The fingerprint allows grouping runs that ran on identical (or sufficiently
-- similar) environments, which is crucial for comparing performance metrics.
-- ============================================================================

CREATE TABLE metadata.environments (
    environment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES metadata.test_runs(run_id) ON DELETE CASCADE,

    cluster_name TEXT,
    cluster_type TEXT,                                  -- 'k8s', 'openshift', 'docker', 'local'
    kubernetes_version TEXT,
    cloud_provider TEXT,
    cloud_region TEXT,
    cloud_zone TEXT,

    node_count INTEGER,
    node_os TEXT,
    node_kernel TEXT,
    node_architecture TEXT,
    node_resource_capacity JSONB,                       -- e.g. {"cpu_cores": 8, "memory_gb": 32}

    fingerprint_hash TEXT NOT NULL,                     -- SHA256 hex string
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (run_id, fingerprint_hash)                   -- a run has exactly one environment
);

CREATE INDEX idx_environments_fingerprint ON metadata.environments(fingerprint_hash);
CREATE INDEX idx_environments_run_id ON metadata.environments(run_id);


-- ----------------------------------------------------------------------------
-- 3. resource_snapshots – Dynamic resource usage during test execution
-- ----------------------------------------------------------------------------
--
-- A time‑series table capturing resource consumption (CPU, memory, disk, network)
-- at regular intervals during the test run.
--
-- The `test_phase` column links the snapshot to a specific phase of the test
-- (warmup, steady state, ramp‑down, etc.) for correlation with test phases.
-- ============================================================================

CREATE TYPE metadata.resource_type AS ENUM (
    'cpu',
    'memory',
    'disk',
    'network',
    'gpu'
);

CREATE TYPE metadata.test_phase AS ENUM (
    'setup',
    'warmup',
    'ramp_up',
    'steady',
    'ramp_down',
    'cooldown'
);

CREATE TABLE metadata.resource_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES metadata.test_runs(run_id) ON DELETE CASCADE,

    resource_type metadata.resource_type NOT NULL,
    node_name TEXT,
    namespace TEXT,
    pod_name TEXT,
    container_name TEXT,

    value_min FLOAT,
    value_max FLOAT,
    value_avg FLOAT,
    value_current FLOAT,
    unit TEXT,                                          -- e.g. 'percent', 'MiB', 'MB/s'

    snapshot_time TIMESTAMPTZ NOT NULL DEFAULT now(),
    test_phase metadata.test_phase,
    time_elapsed_seconds INTEGER,                       -- seconds since run start

    metadata JSONB                                      -- extra fields (labels, annotations, etc.)
);

CREATE INDEX idx_resource_snapshots_run_time ON metadata.resource_snapshots(run_id, snapshot_time);
CREATE INDEX idx_resource_snapshots_type ON metadata.resource_snapshots(resource_type);


-- ----------------------------------------------------------------------------
-- 4. correlation_events – Test phase and milestone tracking
-- ----------------------------------------------------------------------------
--
-- Records significant events during the test, such as phase transitions,
-- errors, or custom milestones. This allows reconstructing the exact timeline
-- of the test and correlating metrics with specific events.
-- ============================================================================

CREATE TABLE metadata.correlation_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES metadata.test_runs(run_id) ON DELETE CASCADE,

    event_type TEXT,                                    -- 'phase_start', 'phase_end', 'milestone', 'error'
    phase_name metadata.test_phase,
    event_time TIMESTAMPTZ NOT NULL DEFAULT now(),

    description TEXT,
    tags TEXT[],
    metadata JSONB,

    sequence_number INTEGER,                            -- ordering within the run
    parent_event_id UUID REFERENCES metadata.correlation_events(event_id)  -- for hierarchical events
);

CREATE INDEX idx_correlation_events_run_time ON metadata.correlation_events(run_id, event_time);


-- ----------------------------------------------------------------------------
-- 5. data_artifacts – References to externally stored test data
-- ----------------------------------------------------------------------------
--
-- Links to files (e.g., raw k6 output, logs, processed metrics) stored outside
-- the database (object storage, local file system, etc.).
-- ============================================================================

CREATE TYPE metadata.data_type AS ENUM (
    'baseline',
    'current',
    'historical',
    'comparison'
);

CREATE TABLE metadata.data_artifacts (
    artifact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES metadata.test_runs(run_id) ON DELETE CASCADE,

    artifact_type TEXT,                                 -- e.g. 'raw_data', 'processed_data', 'baseline'
    data_type metadata.data_type NOT NULL,

    storage_path TEXT,                                  -- relative path inside the storage backend
    storage_uri TEXT,                                   -- full URI (s3://, gs://, file://)
    storage_backend TEXT,                               -- 's3', 'gcs', 'local', 'database'

    data_size_bytes BIGINT,
    checksum TEXT,                                      -- SHA256 hex
    file_format TEXT,                                   -- 'json', 'csv', 'parquet', etc.

    description TEXT,
    tags TEXT[],

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_data_artifacts_run ON metadata.data_artifacts(run_id);
CREATE INDEX idx_data_artifacts_type ON metadata.data_artifacts(data_type);