# Metadata Collection & Storage Flow

## Overview

The metadata collection and storage system captures comprehensive information about test runs, including environment details, resource usage, and correlation data. This document describes the end-to-end flow of metadata through the system.

## Architecture

```text
┌─────────────────┐ ┌──────────────────┐ ┌─────────────────┐
│ Test Runner │────▶│ Metadata │────▶│ PostgreSQL │
│ (Collects) │ │ Collector │ │ Database │
└─────────────────┘ └──────────────────┘ └─────────────────┘
│ │
▼ ▼
┌──────────────────┐ ┌─────────────────┐
│ API Service │◀────│ Query │
│ (Storage) │ │ Interface │
└──────────────────┘ └─────────────────┘
```


## Data Collection Flow

### 1. Test Initialization Phase

```text
Test Runner starts
│
▼
Initialize MetadataCollector
│
▼
Collect Environment Information
├── Cluster detection (K8s/Docker)
├── Node information (OS, resources)
├── Cloud provider detection
└── Generate fingerprint hash
│
▼
Create Test Run Record (status: pending)
├── Test parameters
├── Thresholds
├── Tags
└── Trigger information
│
▼
Store initial metadata
│
▼
Test begins execution
```

### 2. Test Execution Phase

```text
Test execution starts
│
▼
Update Test Run Status (status: running)
│
▼
Collect Resource Snapshots (periodic)
├── CPU usage
├── Memory usage
├── Disk I/O
└── Network metrics
│
▼
Record Correlation Events
├── Phase changes
├── Milestones
└── Errors
│
▼
Add Data Artifacts
├── Baseline data
├── Raw metrics
└── Processed results
```

### 3. Test Completion Phase

```text
Test execution completes
│
▼
Update Test Run Status (status: completed/failed)
│
▼
Update Performance Metrics
├── Success rate
├── Response times
├── Percentiles
└── Error counts
│
▼
Calculate Duration
│
▼
Finalize Run Record
│
▼
Store Complete Metadata
```


## Data Models

### Test Run Core
- **Purpose**: Main record of a test execution
- **Key fields**: run_id, test_name, status, start_time, end_time, duration
- **Relationship**: One-to-many with all other tables

### Environment Fingerprint
- **Purpose**: Capture and correlate execution environment
- **Key fields**: fingerprint_hash, cluster_name, K8s version, cloud provider
- **Use**: Compare across runs, identify environment differences

### Resource Snapshots
- **Purpose**: Periodic capture of resource usage
- **Key fields**: resource_type, values (min/max/avg/current), snapshot_time
- **Use**: Performance analysis, bottleneck identification

### Correlation Events
- **Purpose**: Track test phases and milestones
- **Key fields**: event_type, phase_name, sequence_number
- **Use**: Phase correlation, timeline analysis

### Data Artifacts
- **Purpose**: Reference to external data
- **Key fields**: artifact_type, storage_location, checksum
- **Use**: Data provenance, re-analysis

## Storage Flow

```text
Metadata Collector
│
▼ (HTTP/REST API)
API Service
│
▼ (SQL)
PostgreSQL Database
├── metadata schema
├── audit schema
└── Views & functions
│
▼ (Backup/Retention)
Storage Management
├── Data retention policies
├── Cleanup jobs
└── Archival process
```


## Query Interface

### Basic Queries

1. **Get run by ID**: Complete run details
2. **List runs**: Filter by status, name, date range, tags
3. **Get resource usage**: Time-series data for a run

### Advanced Queries

1. **Environment correlation**: Find runs with similar fingerprints
2. **Performance trends**: Analyze over time
3. **Phase analysis**: Correlate phase events with metrics

## Retention Policy

- Default retention: 90 days for test runs
- Configurable per table
- Automated cleanup scheduled weekly
- Orphan record cleanup
- Storage statistics monitoring

## Security Considerations

- Database user with minimal privileges
- API authentication required (future)
- Audit logging for all operations
- Encrypted connections (SSL/TLS)

## Extensibility

The system is designed to be extensible:
1. **New metric types**: Add to resource snapshots
2. **Additional metadata**: Extend test_runs table
3. **Custom events**: Use correlation_events with attributes JSON
4. **New backends**: Support different storage backends

## Deployment

### Local Development
1. Start PostgreSQL: `docker-compose up postgres`
2. Run migrations: `python migrate.py`
3. Start API service: `uvicorn api.metadata_service:app`

### Kubernetes Production
1. Deploy PostgreSQL: `kubectl apply -f infra/local/postgres.yaml`
2. Deploy API service: `kubectl apply -f infra/api/metadata-api.yaml`
3. Configure retention: Update config map

## Monitoring

- API health endpoint: `/api/v1/health`
- Storage statistics via retention service
- Audit logs for all operations
- Metrics for: test runs, storage size, retention effectiveness

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
    - Check PostgreSQL status
    - Verify connection string
    - Ensure network policies allow access

2. **Missing Fingerprint Hash**
    - Ensure all required fields populated
    - Check fingerprint generation logic

3. **Slow Query Performance**
    - Check indexes on time-based columns
    - Review query execution plans
    - Consider partitioning by date

### Debugging

```sql
-- Check recent runs
SELECT run_id, test_name, status, start_time
FROM metadata.test_runs
ORDER BY start_time DESC
LIMIT 10;

-- View environment details
SELECT * FROM metadata.v_run_details
WHERE run_id = 'your-run-id';

-- Check storage statistics
SELECT * FROM metadata.get_storage_stats();

-- View retention applied
SELECT * FROM metadata.retention_audit_log
ORDER BY run_time DESC
LIMIT 10;
```

