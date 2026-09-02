"""Metadata mapping strategies."""

from __future__ import annotations

from perfeng.generated.run_metadata import PerformanceRunMetadata
from perfeng.storage.schemas import EnvironmentCreate, RunCreate


class DefaultMetadataMapper:
    """Default mapping from PerformanceRunMetadata to storage DTOs."""

    def map_run(self, metadata: PerformanceRunMetadata) -> RunCreate:
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
            thresholds=None,
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

    def map_environment(self, metadata: PerformanceRunMetadata) -> EnvironmentCreate | None:
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
