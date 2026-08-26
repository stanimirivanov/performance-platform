-- Main schema file for the metadata database
--
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS metadata;

CREATE SCHEMA IF NOT EXISTS audit;

-- Set search path
SET
    search_path TO metadata,
    public;

-- =============================================
-- ENUM TYPES
-- =============================================
CREATE TYPE test_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'cancelled',
    'timeout'
);

CREATE TYPE resource_type AS ENUM (
    'cpu',
    'memory',
    'disk',
    'network',
    'gpu'
);

CREATE TYPE data_type AS ENUM (
    'baseline',
    'current',
    'historical',
    'comparison'
);

CREATE TYPE test_phase AS ENUM (
    'setup',
    'warmup',
    'ramp_up',
    'steady',
    'ramp_down',
    'cooldown'
);

-- =============================================
-- CORE TABLES
-- =============================================
-- Test runs table - main metadata for each test execution
CREATE TABLE IF NOT EXISTS test_runs (
    run_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_name VARCHAR(255) NOT NULL,
    test_script VARCHAR(500),
    test_profile VARCHAR(100),
    status test_status NOT NULL DEFAULT 'pending',
    -- Timestamps
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Test parameters
    thresholds JSONB,
    parameters JSONB,
    tags TEXT [],
    -- Metadata
    triggered_by VARCHAR(100),
    trigger_type VARCHAR(50),
    -- 'manual', 'scheduled', 'ci_cd'
    ci_build_id VARCHAR(255),
    ci_job_id VARCHAR(255),
    -- Performance summary
    success_rate FLOAT,
    average_response_time_ms FLOAT,
    percentiles JSONB,
    error_count INTEGER DEFAULT 0,
    total_requests INTEGER DEFAULT 0,
    -- Constraints
    CONSTRAINT valid_duration CHECK (duration_seconds >= 0)
);

-- Environment fingerprints table
CREATE TABLE IF NOT EXISTS environment_fingerprints (
    fingerprint_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES test_runs(run_id) ON DELETE CASCADE,
    -- Cluster info
    cluster_name VARCHAR(255),
    cluster_type VARCHAR(50),
    -- 'k8s', 'openshift', 'docker'
    kubernetes_version VARCHAR(50),
    cloud_provider VARCHAR(50),
    cloud_region VARCHAR(50),
    cloud_zone VARCHAR(50),
    -- Node info
    node_count INTEGER,
    node_os VARCHAR(100),
    node_kernel VARCHAR(100),
    node_architecture VARCHAR(50),
    node_resource_capacity JSONB,
    -- Environment hash (for correlation)
    fingerprint_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Unique constraint
    CONSTRAINT unique_fingerprint UNIQUE (fingerprint_hash, run_id)
);

-- Resource usage tables
CREATE TABLE IF NOT EXISTS resource_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES test_runs(run_id) ON DELETE CASCADE,
    resource_type resource_type NOT NULL,
    node_name VARCHAR(255),
    namespace VARCHAR(255),
    pod_name VARCHAR(255),
    container_name VARCHAR(255),
    -- Resource values
    value_min FLOAT,
    value_max FLOAT,
    value_avg FLOAT,
    value_current FLOAT,
    unit VARCHAR(20),
    -- Timing
    snapshot_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    test_phase test_phase,
    time_elapsed_seconds INTEGER,
    -- Additional metadata
    metadata JSONB,
    -- Indexes for performance
    INDEX idx_resource_snapshot_run_time (run_id, snapshot_time)
);

-- Data artifacts table
CREATE TABLE IF NOT EXISTS data_artifacts (
    artifact_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES test_runs(run_id) ON DELETE CASCADE,
    artifact_type VARCHAR(50),
    -- 'baseline', 'profile', 'raw_data', 'processed_data'
    data_type data_type NOT NULL,
    -- Storage location
    storage_path VARCHAR(500),
    storage_uri VARCHAR(1000),
    storage_backend VARCHAR(50),
    -- 's3', 'gcs', 'local', 'database'
    -- Data metadata
    data_size_bytes BIGINT,
    checksum VARCHAR(64),
    file_format VARCHAR(20),
    -- 'json', 'csv', 'parquet', 'prometheus'
    -- Descriptors
    description TEXT,
    tags TEXT [],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Correlation events table (for phase correlation)
CREATE TABLE IF NOT EXISTS correlation_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL REFERENCES test_runs(run_id) ON DELETE CASCADE,
    event_type VARCHAR(50),
    -- 'phase_start', 'phase_end', 'milestone', 'error'
    phase_name test_phase,
    event_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Context
    description TEXT,
    tags TEXT [],
    metadata JSONB,
    -- Correlation
    sequence_number INTEGER,
    parent_event_id UUID REFERENCES correlation_events(event_id)
);

-- =============================================
-- AUDIT TABLES
-- =============================================
CREATE TABLE IF NOT EXISTS audit.logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID REFERENCES metadata.test_runs(run_id),
    user_id VARCHAR(100),
    action VARCHAR(100),
    resource_type VARCHAR(50),
    resource_id UUID,
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- INDEXES FOR PERFORMANCE
-- =============================================
CREATE INDEX idx_test_runs_status ON test_runs(status);

CREATE INDEX idx_test_runs_start_time ON test_runs(start_time);

CREATE INDEX idx_test_runs_created_at ON test_runs(created_at);

CREATE INDEX idx_resource_snapshots_type ON resource_snapshots(resource_type);

CREATE INDEX idx_data_artifacts_type ON data_artifacts(data_type);

CREATE INDEX idx_correlation_events_time ON correlation_events(event_time);

-- =============================================
-- VIEWS
-- =============================================
-- View for complete run details
CREATE
OR REPLACE VIEW metadata.v_run_details AS
SELECT
    r.*,
    e.fingerprint_hash,
    e.cluster_name,
    e.kubernetes_version,
    e.cloud_provider,
    COUNT(DISTINCT rs.snapshot_id) as snapshot_count,
    COUNT(DISTINCT da.artifact_id) as artifact_count,
    (
        SELECT
            COUNT(*)
        FROM
            metadata.correlation_events ce
        WHERE
            ce.run_id = r.run_id
    ) as event_count
FROM
    metadata.test_runs r
    LEFT JOIN metadata.environment_fingerprints e ON r.run_id = e.run_id
    LEFT JOIN metadata.resource_snapshots rs ON r.run_id = rs.run_id
    LEFT JOIN metadata.data_artifacts da ON r.run_id = da.run_id
GROUP BY
    r.run_id,
    e.fingerprint_hash,
    e.cluster_name,
    e.kubernetes_version,
    e.cloud_provider;

-- View for run summary statistics
CREATE
OR REPLACE VIEW metadata.v_run_summary AS
SELECT
    r.run_id,
    r.test_name,
    r.status,
    r.start_time,
    r.end_time,
    r.duration_seconds,
    r.total_requests,
    r.success_rate,
    r.average_response_time_ms,
    e.cluster_name,
    e.fingerprint_hash,
    COUNT(rs.snapshot_id) as resource_samples,
    MAX(rs.snapshot_time) as last_resource_sample
FROM
    metadata.test_runs r
    LEFT JOIN metadata.environment_fingerprints e ON r.run_id = e.run_id
    LEFT JOIN metadata.resource_snapshots rs ON r.run_id = rs.run_id
GROUP BY
    r.run_id,
    e.cluster_name,
    e.fingerprint_hash;

-- =============================================
-- FUNCTIONS
-- =============================================
-- Function to update run status and timing
CREATE
OR REPLACE FUNCTION metadata.update_run_status(
    p_run_id UUID,
    p_status metadata.test_status,
    p_end_time TIMESTAMP WITH TIME ZONE DEFAULT NULL
) RETURNS VOID AS $ $ BEGIN
UPDATE
    metadata.test_runs
SET
    status = p_status,
    end_time = COALESCE(p_end_time, CURRENT_TIMESTAMP),
    duration_seconds = EXTRACT(
        EPOCH
        FROM
            (
                COALESCE(p_end_time, CURRENT_TIMESTAMP) - start_time
            )
    ),
    updated_at = CURRENT_TIMESTAMP
WHERE
    run_id = p_run_id;

END;

$ $ LANGUAGE plpgsql;

-- Function to generate environment fingerprint hash
CREATE
OR REPLACE FUNCTION metadata.generate_fingerprint_hash(
    p_cluster_name VARCHAR,
    p_kubernetes_version VARCHAR,
    p_cloud_provider VARCHAR,
    p_node_os VARCHAR
) RETURNS VARCHAR AS $ $ BEGIN RETURN ENCODE(
    SHA256(
        CONCAT(
            COALESCE(p_cluster_name, ''),
            COALESCE(p_kubernetes_version, ''),
            COALESCE(p_cloud_provider, ''),
            COALESCE(p_node_os, '')
        ) :: BYTEA
    ),
    'hex'
);

END;

$ $ LANGUAGE plpgsql;

-- =============================================
-- TRIGGERS
-- =============================================
-- Trigger to automatically update updated_at
CREATE
OR REPLACE FUNCTION metadata.update_updated_at_column() RETURNS TRIGGER AS $ $ BEGIN NEW.updated_at = CURRENT_TIMESTAMP;

RETURN NEW;

END;

$ $ LANGUAGE plpgsql;

CREATE TRIGGER update_test_runs_updated_at BEFORE
UPDATE
    ON metadata.test_runs FOR EACH ROW EXECUTE FUNCTION metadata.update_updated_at_column();

-- Trigger to validate fingerprint uniqueness per run
CREATE
OR REPLACE FUNCTION metadata.validate_fingerprint_uniqueness() RETURNS TRIGGER AS $ $ BEGIN IF EXISTS (
    SELECT
        1
    FROM
        metadata.environment_fingerprints
    WHERE
        fingerprint_hash = NEW.fingerprint_hash
        AND run_id = NEW.run_id
        AND fingerprint_id != NEW.fingerprint_id
) THEN RAISE EXCEPTION 'Duplicate fingerprint for the same run';

END IF;

RETURN NEW;

END;

$ $ LANGUAGE plpgsql;

CREATE TRIGGER ensure_unique_fingerprint BEFORE
INSERT
    OR
UPDATE
    ON metadata.environment_fingerprints FOR EACH ROW EXECUTE FUNCTION metadata.validate_fingerprint_uniqueness();