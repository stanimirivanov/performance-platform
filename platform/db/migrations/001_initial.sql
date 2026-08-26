-- Apply schema
\ i platform / db / schema.sql -- 
--
-- Create initial data
INSERT INTO
    metadata.test_runs (
        run_id,
        test_name,
        test_script,
        status,
        created_at,
        trigger_type
    )
VALUES
    (
        '00000000-0000-0000-0000-000000000001',
        'System Initialization',
        'init',
        'completed',
        CURRENT_TIMESTAMP,
        'manual'
    );

-- Create audit schema if not exists
CREATE SCHEMA IF NOT EXISTS audit;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA metadata TO test_user;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA metadata TO test_user;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA audit TO test_user;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA audit TO test_user;

-- Set up default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA metadata GRANT ALL ON TABLES TO test_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT ALL ON TABLES TO test_user;

-- Create database roles if they don't exist
DO $ $ BEGIN IF NOT EXISTS (
    SELECT
        1
    FROM
        pg_roles
    WHERE
        rolname = 'test_user'
) THEN CREATE ROLE test_user WITH LOGIN PASSWORD 'test_password';

END IF;

END $ $;

-- Add comments
COMMENT ON TABLE metadata.test_runs IS 'Main table storing test run metadata';

COMMENT ON TABLE metadata.environment_fingerprints IS 'Environment fingerprints for test correlation';

COMMENT ON TABLE metadata.resource_snapshots IS 'Resource usage snapshots during tests';

COMMENT ON TABLE metadata.data_artifacts IS 'Data artifacts associated with test runs';

COMMENT ON TABLE metadata.correlation_events IS 'Events for phase correlation';