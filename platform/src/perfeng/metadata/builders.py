"""Builders for EnvironmentSpecification and PerformanceRunMetadata."""

import platform
import uuid
from datetime import UTC, datetime
from typing import Any

from perfeng.generated.environment import Application, EnvironmentSpecification, Kubernetes, Runtime
from perfeng.generated.run_metadata import (
    Candidate,
    Data,
    PerformanceRunMetadata,
    Phases,
    Profile,
    Run,
    Test,
    Trigger,
)
from perfeng.generated.run_metadata import Environment as RunEnvironment
from perfeng.generated.run_metadata import Runtime as RunRuntime
from perfeng.generated.run_metadata import Status as RunStatus
from perfeng.generated.run_metadata import Tool as TestTool
from perfeng.generated.run_metadata import Type as TestType

from . import detectors
from . import fingerprint as fp


def build_environment_spec(
    config: dict[str, Any],
    auto_detect: bool = True,
) -> EnvironmentSpecification:
    """
    Build an EnvironmentSpecification from configuration and auto-detection.

    Args:
        config: Configuration dictionary (from config loader)
        auto_detect: Whether to run auto-detection (kubectl, etc.)

    Returns:
        A fully populated EnvironmentSpecification.
    """
    env_config = config.get("environment_config", {})

    # Run detection if enabled
    if auto_detect:
        cluster_info = detectors.detect_cluster_info(config.get("timeout_seconds", 30))
        node_info = detectors.detect_node_info()
        k8s_version = detectors.get_kubernetes_version()
        node_pools = detectors.detect_node_pools()
        container_runtime = detectors.detect_container_runtime()
        cni = detectors.detect_cni()
        storage_class = detectors.detect_storage_class()
    else:
        # Use config values only, minimal detection for node info
        cluster_info = {"name": "local", "type": "docker", "node_count": 1}
        node_info = detectors.detect_node_info()
        k8s_version = None
        node_pools = None
        container_runtime = None
        cni = None
        storage_class = None

    # Build Kubernetes object
    config_node_count = env_config.get("kubernetes", {}).get("nodeCount")
    node_count = (
        config_node_count if config_node_count is not None else cluster_info.get("node_count", 1)
    )

    kubernetes = Kubernetes(
        version=k8s_version or env_config.get("kubernetes", {}).get("version"),
        nodeCount=node_count,
        nodePools=node_pools or env_config.get("kubernetes", {}).get("nodePools"),
    )

    # Build Runtime object
    runtime_config = env_config.get("runtime", {})
    runtime = Runtime(
        containerRuntime=container_runtime or runtime_config.get("containerRuntime"),
        cni=cni or runtime_config.get("cni"),
        storageClass=storage_class or runtime_config.get("storageClass"),
        kernel=node_info.get("kernel", platform.release()),
    )

    # Build Application object if configured
    application = None
    if env_config.get("application"):
        app_config = env_config.get("application", {})
        application = Application(
            configurationHash=app_config.get("configurationHash"),
            featureFlags=app_config.get("featureFlags", {}),
        )

    cluster_name = env_config.get("cluster") or cluster_info.get("name", "local")

    # Generate fingerprint
    fingerprint = fp.generate_fingerprint(
        cluster_name=cluster_name,
        k8s_version=kubernetes.version,
        node_os=node_info.get("os", ""),
        container_runtime=runtime.containerRuntime,
        excludes=config.get("fingerprint_excludes"),
    )

    return EnvironmentSpecification(
        cluster=cluster_name,
        fingerprint=fingerprint,
        kubernetes=kubernetes,
        runtime=runtime,
        application=application,
        compatibility=None,
    )


def build_performance_run_metadata(
    test_name: str,
    status: str,
    env_spec: EnvironmentSpecification,
    kwargs: dict[str, Any],
) -> PerformanceRunMetadata:
    """
    Build a PerformanceRunMetadata from the given environment and parameters.

    Args:
        test_name: Name of the test (used as suite and scenario)
        status: Status string (e.g., "RUNNING", "COMPLETED")
        env_spec: Collected environment specification
        kwargs: Additional parameters (test_profile, trigger_type, tool, etc.)

    Returns:
        A fully populated PerformanceRunMetadata.
    """
    # 1. Convert environment
    env = _convert_environment(env_spec, kwargs)

    # 2. Generate run ID
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    suffix = uuid.uuid4().hex[:8]
    run_id = f"perf-{ts}-{suffix}"

    # 3. Map status to enum
    status_map = {
        "created": RunStatus.CREATED,
        "validating": RunStatus.VALIDATING,
        "provisioning": RunStatus.PROVISIONING,
        "warming_up": RunStatus.WARMING_UP,
        "running": RunStatus.RUNNING,
        "collecting": RunStatus.COLLECTING,
        "analyzing": RunStatus.ANALYZING,
        "reporting": RunStatus.REPORTING,
        "completed": RunStatus.COMPLETED,
        "invalid": RunStatus.INVALID,
        "aborted": RunStatus.ABORTED,
        "infrastructure_failure": RunStatus.INFRASTRUCTURE_FAILURE,
        "test_failure": RunStatus.TEST_FAILURE,
        "inconclusive": RunStatus.INCONCLUSIVE,
    }
    run_status = status_map.get(status.lower(), RunStatus.CREATED)

    # 4. Map profile
    profile_map = {
        "smoke": Profile.smoke,
        "average": Profile.average,
        "regression": Profile.regression,
        "stress": Profile.stress,
        "capacity": Profile.capacity,
        "soak": Profile.soak,
    }
    profile_key = kwargs.get("test_profile", "regression")
    run_profile = profile_map.get(profile_key.lower(), Profile.regression)

    # 5. Map trigger
    trigger_map = {
        "manual": Trigger.manual,
        "ci": Trigger.ci,
        "schedule": Trigger.schedule,
        "bisect": Trigger.bisect,
        "release": Trigger.release,
    }
    trigger_key = kwargs.get("trigger_type", "manual")
    run_trigger = trigger_map.get(trigger_key.lower(), Trigger.manual)

    # 6. Build Run
    run = Run(
        id=run_id,
        suite=test_name,
        profile=run_profile,
        timestamp=datetime.utcnow().replace(tzinfo=UTC),
        trigger=run_trigger,
        status=run_status,
        policyVersion=kwargs.get("policyVersion"),
        notes=kwargs.get("notes"),
    )

    # 7. Build Test
    tool_map = {
        "k6": TestTool.k6,
        "playwright": TestTool.playwright,
        "kube-burner": TestTool.kube_burner,
        "benchmark-operator": TestTool.benchmark_operator,
    }
    tool = kwargs.get("tool", "k6")
    test_tool = tool_map.get(tool.lower(), TestTool.k6)

    type_map = {
        "api": TestType.api,
        "browser": TestType.browser,
        "kubernetes": TestType.kubernetes,
        "infrastructure": TestType.infrastructure,
    }
    test_type_str = kwargs.get("test_type", "api")
    test_type = type_map.get(test_type_str.lower(), TestType.api)

    test = Test(
        type=test_type,
        tool=test_tool,
        toolVersion=kwargs.get("toolVersion", "unknown"),
        scenario=kwargs.get("scenario", test_name),
        workloadVersion=kwargs.get("workloadVersion"),
        configHash=kwargs.get("configHash"),
    )

    # 8. Build Candidate with featureFlags from kwargs
    feature_flags = kwargs.get("featureFlags", {})
    if "tags" in kwargs:
        feature_flags["tags"] = kwargs["tags"]
    if "thresholds" in kwargs:
        feature_flags["thresholds"] = kwargs["thresholds"]

    candidate = Candidate(
        gitSha=kwargs.get("gitSha", "0" * 40),
        imageDigest=kwargs.get("imageDigest"),
        version=kwargs.get("version"),
        branch=kwargs.get("branch"),
        configurationHash=kwargs.get("configurationHash"),
        featureFlags=feature_flags if feature_flags else None,
        databaseMigrationVersion=kwargs.get("databaseMigrationVersion"),
    )

    # 9. Optional Runtime
    runtime = None
    if any(
        key in kwargs
        for key in [
            "replicas",
            "cpuRequests",
            "cpuLimits",
            "memoryRequests",
            "memoryLimits",
            "hpa",
        ]
    ):
        runtime = RunRuntime(
            replicas=kwargs.get("replicas"),
            cpuRequests=kwargs.get("cpuRequests"),
            cpuLimits=kwargs.get("cpuLimits"),
            memoryRequests=kwargs.get("memoryRequests"),
            memoryLimits=kwargs.get("memoryLimits"),
            hpa=kwargs.get("hpa"),
        )

    # 10. Optional Data
    data = None
    if any(
        key in kwargs
        for key in [
            "datasetId",
            "datasetVersion",
            "databaseSize",
            "seedVersion",
        ]
    ):
        data = Data(
            datasetId=kwargs.get("datasetId"),
            datasetVersion=kwargs.get("datasetVersion"),
            databaseSize=kwargs.get("databaseSize"),
            seedVersion=kwargs.get("seedVersion"),
        )

    # 11. Optional Phases
    phases = None
    if any(
        key in kwargs
        for key in [
            "provisionStart",
            "warmupStart",
            "measurementStart",
            "measurementEnd",
            "cooldownEnd",
        ]
    ):
        phases = Phases(
            provisionStart=kwargs.get("provisionStart"),
            warmupStart=kwargs.get("warmupStart"),
            measurementStart=kwargs.get("measurementStart"),
            measurementEnd=kwargs.get("measurementEnd"),
            cooldownEnd=kwargs.get("cooldownEnd"),
        )

    return PerformanceRunMetadata(
        run=run,
        test=test,
        candidate=candidate,
        environment=env,
        runtime=runtime,
        data=data,
        phases=phases,
    )


def _convert_environment(
    env_spec: EnvironmentSpecification,
    kwargs: dict[str, Any],
) -> RunEnvironment:
    """Convert EnvironmentSpecification to the run-metadata Environment model."""
    kubernetes = env_spec.kubernetes
    runtime = env_spec.runtime

    node_pool = None
    cpu_arch = None
    if kubernetes and kubernetes.nodePools and len(kubernetes.nodePools) > 0:
        first_pool = kubernetes.nodePools[0]
        node_pool = first_pool.name
        cpu_arch = first_pool.cpuArchitecture.value if first_pool.cpuArchitecture else None

    k8s_version = kubernetes.version if kubernetes and kubernetes.version else "0.0.0"

    return RunEnvironment(
        cluster=env_spec.cluster,
        kubernetesVersion=k8s_version,
        nodePool=kwargs.get("nodePool", node_pool),
        nodeModel=kwargs.get("nodeModel"),
        cpuArchitecture=kwargs.get("cpuArchitecture", cpu_arch),
        kernel=runtime.kernel if runtime else None,
        containerRuntime=runtime.containerRuntime if runtime else None,
        cni=runtime.cni if runtime else None,
        storageClass=runtime.storageClass if runtime else None,
        fingerprint=env_spec.fingerprint,
        nodeCount=kubernetes.nodeCount if kubernetes else None,
        region=kwargs.get("region"),
    )
