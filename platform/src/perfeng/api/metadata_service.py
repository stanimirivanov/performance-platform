# platform/api/metadata_service.py
"""
Metadata storage service with REST API endpoints.
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import asyncpg
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import UUID4, BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================
# Pydantic Models
# =============================================


class EnvironmentInfo(BaseModel):
    cluster_name: str
    cluster_type: str
    kubernetes_version: str | None
    cloud_provider: str | None
    cloud_region: str | None
    cloud_zone: str | None
    node_count: int
    node_os: str
    node_kernel: str
    node_architecture: str
    node_resource_capacity: dict[str, Any]
    fingerprint_hash: str


class TestRunCreate(BaseModel):
    test_name: str
    test_script: str | None
    test_profile: str | None
    status: str = "pending"
    thresholds: dict[str, Any] = {}
    parameters: dict[str, Any] = {}
    tags: list[str] = []
    triggered_by: str | None
    trigger_type: str = "manual"
    ci_build_id: str | None
    ci_job_id: str | None
    environment: EnvironmentInfo


class TestRunUpdate(BaseModel):
    status: str | None
    end_time: datetime | None
    duration_seconds: int | None
    success_rate: float | None
    average_response_time_ms: float | None
    percentiles: dict[str, float] | None
    error_count: int | None
    total_requests: int | None


class ResourceSnapshotCreate(BaseModel):
    resource_type: str
    node_name: str | None
    namespace: str | None
    pod_name: str | None
    container_name: str | None
    value_min: float | None
    value_max: float | None
    value_avg: float | None
    value_current: float | None
    unit: str | None
    test_phase: str | None
    time_elapsed_seconds: int | None
    metadata: dict[str, Any] = {}


class CorrelationEventCreate(BaseModel):
    event_type: str
    phase_name: str | None
    description: str | None
    tags: list[str] = []
    metadata: dict[str, Any] = {}
    sequence_number: int | None
    parent_event_id: UUID4 | None


class DataArtifactCreate(BaseModel):
    artifact_type: str
    data_type: str
    storage_path: str | None
    storage_uri: str | None
    storage_backend: str = "local"
    data_size_bytes: int | None
    checksum: str | None
    file_format: str | None
    description: str | None
    tags: list[str] = []


# =============================================
# Database Service
# =============================================


class MetadataDatabase:
    def __init__(self):
        self.pool = None
        self.dsn = os.environ.get(
            "DATABASE_URL", "postgresql://test_user:test_password@localhost:5432/metadata"
        )

    async def connect(self):
        """Create connection pool."""
        self.pool = await asyncpg.create_pool(self.dsn, min_size=5, max_size=20, command_timeout=60)
        logger.info("Connected to PostgreSQL database")

    async def disconnect(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from PostgreSQL database")

    async def create_test_run(self, run_data: TestRunCreate) -> str:
        """Create a new test run record."""
        async with self.pool.acquire() as conn, conn.transaction():
            # Insert test run
            run_id = await conn.fetchval(
                """
                    INSERT INTO metadata.test_runs (
                        test_name, test_script, test_profile, status,
                        thresholds, parameters, tags,
                        triggered_by, trigger_type,
                        ci_build_id, ci_job_id,
                        start_time
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING run_id
                """,
                run_data.test_name,
                run_data.test_script,
                run_data.test_profile,
                run_data.status,
                json.dumps(run_data.thresholds),
                json.dumps(run_data.parameters),
                run_data.tags,
                run_data.triggered_by,
                run_data.trigger_type,
                run_data.ci_build_id,
                run_data.ci_job_id,
                datetime.utcnow(),
            )

            # Insert environment fingerprint
            env = run_data.environment
            await conn.execute(
                """
                    INSERT INTO metadata.environment_fingerprints (
                        run_id, cluster_name, cluster_type,
                        kubernetes_version, cloud_provider, cloud_region,
                        cloud_zone, node_count, node_os, node_kernel,
                        node_architecture, node_resource_capacity,
                        fingerprint_hash
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """,
                run_id,
                env.cluster_name,
                env.cluster_type,
                env.kubernetes_version,
                env.cloud_provider,
                env.cloud_region,
                env.cloud_zone,
                env.node_count,
                env.node_os,
                env.node_kernel,
                env.node_architecture,
                json.dumps(env.node_resource_capacity),
                env.fingerprint_hash,
            )

            logger.info(f"Created test run with ID: {run_id}")
            return str(run_id)

    async def update_test_run(self, run_id: str, update_data: TestRunUpdate) -> bool:
        """Update test run status and results."""
        updates = []
        params = [run_id]
        param_counter = 1

        if update_data.status is not None:
            param_counter += 1
            updates.append(f"status = ${param_counter}")
            params.append(update_data.status)

        if update_data.end_time is not None:
            param_counter += 1
            updates.append(f"end_time = ${param_counter}")
            params.append(update_data.end_time)

        if update_data.duration_seconds is not None:
            param_counter += 1
            updates.append(f"duration_seconds = ${param_counter}")
            params.append(update_data.duration_seconds)

        if update_data.success_rate is not None:
            param_counter += 1
            updates.append(f"success_rate = ${param_counter}")
            params.append(update_data.success_rate)

        if update_data.average_response_time_ms is not None:
            param_counter += 1
            updates.append(f"average_response_time_ms = ${param_counter}")
            params.append(update_data.average_response_time_ms)

        if update_data.percentiles is not None:
            param_counter += 1
            updates.append(f"percentiles = ${param_counter}")
            params.append(json.dumps(update_data.percentiles))

        if update_data.error_count is not None:
            param_counter += 1
            updates.append(f"error_count = ${param_counter}")
            params.append(update_data.error_count)

        if update_data.total_requests is not None:
            param_counter += 1
            updates.append(f"total_requests = ${param_counter}")
            params.append(update_data.total_requests)

        if not updates:
            return False

        query = f"""
            UPDATE metadata.test_runs
            SET {", ".join(updates)}, updated_at = CURRENT_TIMESTAMP
            WHERE run_id = $1
        """

        async with self.pool.acquire() as conn:
            result = await conn.execute(query, *params)
            return result != "UPDATE 0"

    async def add_resource_snapshot(self, run_id: str, snapshot: ResourceSnapshotCreate) -> str:
        """Add a resource usage snapshot."""
        async with self.pool.acquire() as conn:
            snapshot_id = await conn.fetchval(
                """
                INSERT INTO metadata.resource_snapshots (
                    run_id, resource_type, node_name, namespace,
                    pod_name, container_name,
                    value_min, value_max, value_avg, value_current,
                    unit, test_phase, time_elapsed_seconds,
                    metadata, snapshot_time
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                RETURNING snapshot_id
            """,
                run_id,
                snapshot.resource_type,
                snapshot.node_name,
                snapshot.namespace,
                snapshot.pod_name,
                snapshot.container_name,
                snapshot.value_min,
                snapshot.value_max,
                snapshot.value_avg,
                snapshot.value_current,
                snapshot.unit,
                snapshot.test_phase,
                snapshot.time_elapsed_seconds,
                json.dumps(snapshot.metadata),
                datetime.utcnow(),
            )

            return str(snapshot_id)

    async def add_correlation_event(self, run_id: str, event: CorrelationEventCreate) -> str:
        """Add a correlation event."""
        async with self.pool.acquire() as conn:
            event_id = await conn.fetchval(
                """
                INSERT INTO metadata.correlation_events (
                    run_id, event_type, phase_name,
                    description, tags, metadata,
                    sequence_number, parent_event_id,
                    event_time
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING event_id
            """,
                run_id,
                event.event_type,
                event.phase_name,
                event.description,
                event.tags,
                json.dumps(event.metadata),
                event.sequence_number,
                event.parent_event_id,
                datetime.utcnow(),
            )

            return str(event_id)

    async def add_data_artifact(self, run_id: str, artifact: DataArtifactCreate) -> str:
        """Add a data artifact reference."""
        async with self.pool.acquire() as conn:
            artifact_id = await conn.fetchval(
                """
                INSERT INTO metadata.data_artifacts (
                    run_id, artifact_type, data_type,
                    storage_path, storage_uri, storage_backend,
                    data_size_bytes, checksum, file_format,
                    description, tags, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING artifact_id
            """,
                run_id,
                artifact.artifact_type,
                artifact.data_type,
                artifact.storage_path,
                artifact.storage_uri,
                artifact.storage_backend,
                artifact.data_size_bytes,
                artifact.checksum,
                artifact.file_format,
                artifact.description,
                artifact.tags,
                datetime.utcnow(),
            )

            return str(artifact_id)

    async def get_test_run(self, run_id: str) -> dict[str, Any]:
        """Get complete test run details."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM metadata.v_run_details
                WHERE run_id = $1
            """,
                run_id,
            )

            if not row:
                raise HTTPException(status_code=404, detail="Test run not found")

            return dict(row)

    async def list_test_runs(
        self,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        test_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """List test runs with filters."""
        conditions = []
        params = []
        param_counter = 1

        if status:
            conditions.append(f"status = ${param_counter}")
            params.append(status)
            param_counter += 1

        if test_name:
            conditions.append(f"test_name ILIKE $${param_counter}")
            params.append(f"%{test_name}%")
            param_counter += 1

        if start_date:
            conditions.append(f"start_time >= $${param_counter}")
            params.append(start_date)
            param_counter += 1

        if end_date:
            conditions.append(f"start_time <= $${param_counter}")
            params.append(end_date)
            param_counter += 1

        if tags:
            conditions.append(f"tags && $${param_counter}::text[]")
            params.append(tags)
            param_counter += 1

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
            SELECT
                run_id, test_name, test_script, test_profile,
                status, start_time, end_time, duration_seconds,
                created_at, success_rate, average_response_time_ms,
                error_count, total_requests
            FROM metadata.v_run_summary
            {where_clause}
            ORDER BY start_time DESC
            LIMIT ${param_counter}
            OFFSET ${param_counter + 1}
        """

        params.extend([limit, offset])

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]


# =============================================
# FastAPI Application
# =============================================

app = FastAPI(title="Metadata Storage Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database instance
db = MetadataDatabase()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Database connection lifecycle management."""
    await db.connect()
    yield
    await db.disconnect()


app.router.lifespan_context = lifespan

# =============================================
# API Endpoints
# =============================================


@app.post("/api/v1/runs", response_model=dict[str, str])
async def create_test_run(run_data: TestRunCreate):
    """Create a new test run."""
    run_id = await db.create_test_run(run_data)
    return {"run_id": run_id}


@app.patch("/api/v1/runs/{run_id}")
async def update_test_run(run_id: str, update_data: TestRunUpdate):
    """Update test run status and results."""
    success = await db.update_test_run(run_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail="Test run not found")
    return {"status": "updated"}


@app.get("/api/v1/runs/{run_id}")
async def get_test_run(run_id: str):
    """Get complete test run details."""
    return await db.get_test_run(run_id)


@app.get("/api/v1/runs")
async def list_test_runs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    test_name: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    tags: list[str] | None = Query(None),
):
    """List test runs with filters."""
    return await db.list_test_runs(
        limit=limit,
        offset=offset,
        status=status,
        test_name=test_name,
        start_date=start_date,
        end_date=end_date,
        tags=tags,
    )


@app.post("/api/v1/runs/{run_id}/snapshots")
async def add_resource_snapshot(run_id: str, snapshot: ResourceSnapshotCreate):
    """Add a resource usage snapshot."""
    snapshot_id = await db.add_resource_snapshot(run_id, snapshot)
    return {"snapshot_id": snapshot_id}


@app.post("/api/v1/runs/{run_id}/events")
async def add_correlation_event(run_id: str, event: CorrelationEventCreate):
    """Add a correlation event."""
    event_id = await db.add_correlation_event(run_id, event)
    return {"event_id": event_id}


@app.post("/api/v1/runs/{run_id}/artifacts")
async def add_data_artifact(run_id: str, artifact: DataArtifactCreate):
    """Add a data artifact reference."""
    artifact_id = await db.add_data_artifact(run_id, artifact)
    return {"artifact_id": artifact_id}


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# =============================================
# Main entry point
# =============================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
