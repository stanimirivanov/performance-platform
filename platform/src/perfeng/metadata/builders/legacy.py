"""Backward-compatible convenience wrappers."""

from __future__ import annotations

from typing import Any

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.generated.run_metadata import PerformanceRunMetadata
from perfeng.metadata.builders.config import (
    CandidateConfig,
    DataConfig,
    EnvironmentOverrideConfig,
    PhasesConfig,
    RunConfig,
    RunMetadataBuildConfig,
    RunRuntimeConfig,
    TestConfig,
)
from perfeng.metadata.builders.environment import EnvironmentBuilder
from perfeng.metadata.builders.run_metadata import RunMetadataBuilder
from perfeng.metadata.config import (
    ApplicationConfig,
    ClusterConfig,
    CollectorConfig,
    KubernetesConfig,
    RuntimeConfig,
)


def build_environment_spec(
    config: dict[str, Any],
    auto_detect: bool = True,
) -> EnvironmentSpecification:
    """Legacy entry-point: builds an EnvironmentSpecification from a raw dict."""
    env_raw = config.get("environment_config", {})
    k8s_raw = env_raw.get("kubernetes", {})
    rt_raw = env_raw.get("runtime", {})
    app_raw = env_raw.get("application", {})

    collector_config = CollectorConfig(
        auto_detect=auto_detect,
        timeout_seconds=config.get("timeout_seconds", 30),
        fingerprint_excludes=tuple(config.get("fingerprint_excludes", [])),
        cluster=ClusterConfig(
            name=env_raw.get("cluster"),
            type=None,
        ),
        kubernetes=KubernetesConfig(
            node_count=k8s_raw.get("nodeCount"),
            version=k8s_raw.get("version"),
            node_pools=tuple(k8s_raw.get("nodePools", [])) if k8s_raw.get("nodePools") else None,
        )
        if k8s_raw
        else None,
        runtime=RuntimeConfig(
            container_runtime=rt_raw.get("containerRuntime"),
            cni=rt_raw.get("cni"),
            storage_class=rt_raw.get("storageClass"),
            kernel=rt_raw.get("kernel"),
        )
        if rt_raw
        else None,
        application=ApplicationConfig(
            configuration_hash=app_raw.get("configurationHash"),
            feature_flags=app_raw.get("featureFlags", {}),
        )
        if app_raw
        else None,
    )
    return EnvironmentBuilder(collector_config).build()


def build_performance_run_metadata(
    test_name: str,
    status: str,
    env_spec: EnvironmentSpecification,
    kwargs: dict[str, Any],
) -> PerformanceRunMetadata:
    """Legacy entry-point: builds PerformanceRunMetadata from a raw kwargs dict."""
    run_cfg = RunMetadataBuildConfig(
        test_name=test_name,
        status=status,
        run=RunConfig(
            profile=kwargs.get("test_profile", "regression"),
            trigger=kwargs.get("trigger_type", "manual"),
            policy_version=kwargs.get("policyVersion"),
            notes=kwargs.get("notes"),
        ),
        test=TestConfig(
            tool=kwargs.get("tool", "k6"),
            tool_version=kwargs.get("toolVersion", "unknown"),
            test_type=kwargs.get("test_type", "api"),
            scenario=kwargs.get("scenario"),
            workload_version=kwargs.get("workloadVersion"),
            config_hash=kwargs.get("configHash"),
        ),
        candidate=CandidateConfig(
            git_sha=kwargs.get("gitSha", "0" * 40),
            image_digest=kwargs.get("imageDigest"),
            version=kwargs.get("version"),
            branch=kwargs.get("branch"),
            configuration_hash=kwargs.get("configurationHash"),
            feature_flags=kwargs.get("featureFlags", {}),
            tags=kwargs.get("tags"),
            thresholds=kwargs.get("thresholds"),
            database_migration_version=kwargs.get("databaseMigrationVersion"),
        ),
        runtime=RunRuntimeConfig(
            replicas=kwargs.get("replicas"),
            cpu_requests=kwargs.get("cpuRequests"),
            cpu_limits=kwargs.get("cpuLimits"),
            memory_requests=kwargs.get("memoryRequests"),
            memory_limits=kwargs.get("memoryLimits"),
            hpa=kwargs.get("hpa"),
        )
        if any(
            k in kwargs
            for k in [
                "replicas",
                "cpuRequests",
                "cpuLimits",
                "memoryRequests",
                "memoryLimits",
                "hpa",
            ]
        )
        else None,
        data=DataConfig(
            dataset_id=kwargs.get("datasetId"),
            dataset_version=kwargs.get("datasetVersion"),
            database_size=kwargs.get("databaseSize"),
            seed_version=kwargs.get("seedVersion"),
        )
        if any(
            k in kwargs
            for k in [
                "datasetId",
                "datasetVersion",
                "databaseSize",
                "seedVersion",
            ]
        )
        else None,
        phases=PhasesConfig(
            provision_start=kwargs.get("provisionStart"),
            warmup_start=kwargs.get("warmupStart"),
            measurement_start=kwargs.get("measurementStart"),
            measurement_end=kwargs.get("measurementEnd"),
            cooldown_end=kwargs.get("cooldownEnd"),
        )
        if any(
            k in kwargs
            for k in [
                "provisionStart",
                "warmupStart",
                "measurementStart",
                "measurementEnd",
                "cooldownEnd",
            ]
        )
        else None,
        environment=EnvironmentOverrideConfig(
            node_pool=kwargs.get("nodePool"),
            node_model=kwargs.get("nodeModel"),
            cpu_architecture=kwargs.get("cpuArchitecture"),
            region=kwargs.get("region"),
        ),
    )
    return RunMetadataBuilder(run_cfg).build(env_spec)
