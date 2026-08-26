"""
Data retention policy implementation for metadata storage.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)


class RetentionPolicy:
    """Manages data retention policies for metadata."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.default_retention_days = config.get("default_retention_days", 90)
        self.policies = config.get("policies", {})

    async def apply_retention(
        self, conn: asyncpg.Connection, table_name: str, age_days: int | None = None
    ) -> int:
        """
        Apply retention policy to a table.

        Returns:
            Number of records deleted
        """
        if age_days is None:
            age_days = self.default_retention_days

        # Check if specific policy exists
        if table_name in self.policies:
            policy = self.policies[table_name]
            age_days = policy.get("retention_days", age_days)
            timestamp_column = policy.get("timestamp_column", "created_at")
        else:
            timestamp_column = "created_at"

        cutoff_date = datetime.utcnow() - timedelta(days=age_days)

        # Delete old records
        result = await conn.execute(
            f"""
            DELETE FROM metadata.{table_name}
            WHERE {timestamp_column} < $1
        """,
            cutoff_date,
        )

        # Parse deleted count
        deleted = int(result.split()[1]) if result else 0

        logger.info(
            f"Retention applied to {table_name}: "
            f"deleted {deleted} records older than {age_days} days"
        )

        return deleted

    async def cleanup_orphaned_records(self, conn: asyncpg.Connection) -> dict[str, int]:
        """Clean up orphaned records without parent references."""
        results = {}

        # Find orphaned snapshots
        deleted = await conn.execute("""
            DELETE FROM metadata.resource_snapshots
            WHERE NOT EXISTS (
                SELECT 1 FROM metadata.test_runs
                WHERE test_runs.run_id = resource_snapshots.run_id
            )
        """)
        results["orphaned_snapshots"] = int(deleted.split()[1]) if deleted else 0

        # Find orphaned artifacts
        deleted = await conn.execute("""
            DELETE FROM metadata.data_artifacts
            WHERE NOT EXISTS (
                SELECT 1 FROM metadata.test_runs
                WHERE test_runs.run_id = data_artifacts.run_id
            )
        """)
        results["orphaned_artifacts"] = int(deleted.split()[1]) if deleted else 0

        # Find orphaned correlation events
        deleted = await conn.execute("""
            DELETE FROM metadata.correlation_events
            WHERE NOT EXISTS (
                SELECT 1 FROM metadata.test_runs
                WHERE test_runs.run_id = correlation_events.run_id
            )
        """)
        results["orphaned_events"] = int(deleted.split()[1]) if deleted else 0

        # Find orphaned fingerprints
        deleted = await conn.execute("""
            DELETE FROM metadata.environment_fingerprints
            WHERE NOT EXISTS (
                SELECT 1 FROM metadata.test_runs
                WHERE test_runs.run_id = environment_fingerprints.run_id
            )
        """)
        results["orphaned_fingerprints"] = int(deleted.split()[1]) if deleted else 0

        return results

    async def get_storage_stats(self, conn: asyncpg.Connection) -> dict[str, Any]:
        """Get storage statistics for the metadata database."""
        stats = {}

        # Table sizes
        row = await conn.fetchrow("""
            SELECT
                pg_size_pretty(pg_database_size(current_database())) as db_size,
                (SELECT count(*) FROM metadata.test_runs) as total_runs,
                (SELECT count(*) FROM metadata.resource_snapshots) as total_snapshots,
                (SELECT count(*) FROM metadata.data_artifacts) as total_artifacts,
                (SELECT count(*) FROM metadata.correlation_events) as total_events
        """)

        stats["database_size"] = row["db_size"]
        stats["total_runs"] = row["total_runs"]
        stats["total_snapshots"] = row["total_snapshots"]
        stats["total_artifacts"] = row["total_artifacts"]
        stats["total_events"] = row["total_events"]

        # Retention age analysis
        row = await conn.fetchrow("""
            SELECT
                min(created_at) as oldest_record,
                max(created_at) as newest_record,
                avg(EXTRACT(EPOCH FROM (now() - created_at)) / 86400) as avg_age_days
            FROM metadata.test_runs
        """)

        stats["oldest_record"] = row["oldest_record"]
        stats["newest_record"] = row["newest_record"]
        stats["avg_age_days"] = round(row["avg_age_days"] or 0, 2)

        return stats


class RetentionScheduler:
    """Scheduled retention policy execution."""

    def __init__(self, pool: asyncpg.Pool, config: dict[str, Any]):
        self.pool = pool
        self.config = config
        self.policy = RetentionPolicy(config)
        self.schedule_days = config.get("schedule_days", 7)

    async def run_cleanup(self) -> dict[str, Any]:
        """Run complete cleanup process."""
        results = {"applied_policies": {}, "orphaned_cleanup": {}, "storage_stats": {}}

        async with self.pool.acquire() as conn, conn.transaction():
            # Apply retention policies
            for table in [
                "test_runs",
                "resource_snapshots",
                "correlation_events",
                "data_artifacts",
            ]:
                deleted = await self.policy.apply_retention(conn, table)
                results["applied_policies"][table] = deleted

            # Clean up orphaned records
            orphaned = await self.policy.cleanup_orphaned_records(conn)
            results["orphaned_cleanup"] = orphaned

            # Get storage stats
            stats = await self.policy.get_storage_stats(conn)
            results["storage_stats"] = stats

            # Log cleanup results
            logger.info(f"Retention cleanup completed: {results}")

        return results
