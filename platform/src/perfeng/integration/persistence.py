"""Client for persisting PerformanceRunMetadata via the storage API."""

from __future__ import annotations

from typing import Any

import httpx

from perfeng.generated.run_metadata import PerformanceRunMetadata
from perfeng.storage.schemas import EnvironmentCreate, RunCreate


class MetadataPersistenceClient:
    """Convert metadata to API payload and POST it to the storage service."""

    def __init__(self, base_url: str, client: httpx.AsyncClient | None = None):
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.AsyncClient()

    async def __aenter__(self) -> MetadataPersistenceClient:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def save(self, metadata: PerformanceRunMetadata) -> dict[str, Any]:
        """Persist the metadata and return the API response JSON."""
        run_payload = self._to_run_create(metadata)
        environment_payload = self._to_environment_create(metadata)

        payload = run_payload.model_dump()
        if environment_payload:
            payload["environment"] = environment_payload.model_dump()

        response = await self._client.post(
            f"{self.base_url}/api/v1/runs/",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _to_run_create(metadata: PerformanceRunMetadata) -> RunCreate:
        """Map high-level metadata to the simple RunCreate schema."""
        run = metadata.run
        test = metadata.test
        candidate = metadata.candidate
        runtime = metadata.runtime
        data = metadata.data
        phases = metadata.phases

        return RunCreate(
            test_name=run.suite,
            test_script=test.scenario,
            test_profile=run.profile.value,
            status=run.status.value.lower(),
            thresholds=None,  # we don't have threshold details here
            parameters={
                "tool": test.tool.value,
                "tool_version": test.toolVersion,
                "workload_version": test.workloadVersion,
                "config_hash": test.configHash,
                "candidate": candidate.model_dump(),
                "runtime": runtime.model_dump() if runtime else None,
                "data": data.model_dump() if data else None,
                "phases": phases.model_dump() if phases else None,
            },
            tags=None,
            triggered_by=None,
            trigger_type=run.trigger.value,
            ci_build_id=None,
            ci_job_id=None,
            policy_version=run.policyVersion,
            notes=run.notes,
        )

    @staticmethod
    def _to_environment_create(
        metadata: PerformanceRunMetadata,
    ) -> EnvironmentCreate | None:
        """Map environment section to the EnvironmentCreate schema."""
        env = metadata.environment
        if not env:
            return None

        return EnvironmentCreate(
            cluster_name=env.cluster,
            cluster_type=None,
            kubernetes_version=env.kubernetesVersion,
            cloud_provider=None,
            cloud_region=env.region,
            cloud_zone=None,
            node_count=env.nodeCount,
            node_os=None,
            node_kernel=env.kernel,
            node_architecture=env.cpuArchitecture,
            node_resource_capacity=None,
            fingerprint_hash=env.fingerprint or "",
        )
