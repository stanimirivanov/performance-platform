"""Manual integration demo: collect metadata, persist it, sample resources.

This script assumes the FastAPI storage service is running locally at
http://localhost:8000.

Usage:
    uv run python examples/metadata_sampling_demo.py

After execution, verify entries in the database using:
    psql -h localhost -U test_user -d metadata -c \
        "SELECT run_id, test_name, status FROM metadata.test_runs ORDER BY created_at DESC LIMIT 1;"
    psql -h localhost -U test_user -d metadata -c \
        "SELECT * FROM metadata.resource_snapshots WHERE run_id = '<run_id>' LIMIT 5;"
"""

import asyncio
import logging

from perfeng.integration.persistence import MetadataPersistenceClient
from perfeng.integration.sampling import ResourceUsageSampler
from perfeng.metadata.collector import MetadataCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
SAMPLING_DURATION_SECONDS = 10
SAMPLING_INTERVAL_SECONDS = 2


async def main() -> None:
    # 1. Collect metadata (disable auto-detection to avoid kubectl calls)
    collector = MetadataCollector(config_dict={"auto_detect": False})
    metadata = collector.collect_test_metadata(
        test_name="manual-demo-run",
        status="running",
        test_profile="smoke",
        tool="k6",
        toolVersion="0.45.0",
        scenario="demo-scenario.js",
        gitSha="0" * 40,
        version="1.0.0",
    )
    logger.info("Collected metadata for run: %s", metadata.run.id)

    # 2. Persist metadata and get run_id
    async with MetadataPersistenceClient(base_url=BASE_URL) as persister:
        result = await persister.save(metadata)
        run_id = result["run_id"]
        logger.info("Persisted run with ID: %s", run_id)

        # 3. Start resource sampling for a short period
        sampler = ResourceUsageSampler(
            run_id=run_id,
            base_url=BASE_URL,
            interval_seconds=SAMPLING_INTERVAL_SECONDS,
        )
        await sampler.start()
        logger.info("Sampling resources for %d seconds...", SAMPLING_DURATION_SECONDS)

        # Simulate a running test (or just wait)
        await asyncio.sleep(SAMPLING_DURATION_SECONDS)

        await sampler.stop()
        logger.info("Resource sampling stopped.")

    logger.info(
        "Demo complete. Verify database entries using the commands in the docstring."
    )


if __name__ == "__main__":
    asyncio.run(main())
