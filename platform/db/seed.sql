-- ============================================================================
-- Seed data for local development
-- ============================================================================
--
-- This script inserts an example run and associated environment to facilitate
-- manual testing and UI development.
-- ============================================================================

INSERT INTO metadata.test_runs (
    run_id,
    test_name,
    test_script,
    test_profile,
    status,
    start_time,
    end_time,
    duration_seconds,
    thresholds,
    parameters,
    tags,
    triggered_by,
    trigger_type,
    ci_build_id,
    ci_job_id,
    success_rate,
    average_response_time_ms,
    percentiles,
    error_count,
    total_requests
) VALUES (
    '11111111-1111-1111-1111-111111111111',
    'checkout-api',
    'checkout-flow.js',
    'regression',
    'completed',
    '2024-01-15T14:30:22Z',
    '2024-01-15T14:45:22Z',
    900,
    '{"p95": 100, "p99": 200}',
    '{"users": 50, "duration": 60}',
    ARRAY['production', 'checkout'],
    'jenkins',
    'ci',
    'build-123',
    'job-456',
    0.99,
    45.2,
    '{"p50": 40, "p95": 80, "p99": 120}',
    2,
    10000
);

INSERT INTO metadata.environments (
    run_id,
    cluster_name,
    cluster_type,
    kubernetes_version,
    cloud_provider,
    cloud_region,
    cloud_zone,
    node_count,
    node_os,
    node_kernel,
    node_architecture,
    node_resource_capacity,
    fingerprint_hash
) VALUES (
    '11111111-1111-1111-1111-111111111111',
    'perf-k8s-01',
    'k8s',
    'v1.28.0',
    'aws',
    'us-west-2',
    'us-west-2a',
    3,
    'linux',
    '5.10.0',
    'amd64',
    '{"cpu_cores": 8, "memory_gb": 32, "disk_gb": 100}',
    '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef'
);