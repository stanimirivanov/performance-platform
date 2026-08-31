"""
Test builders for creating instances of generated environment models.
These builders set optional fields to None unless explicitly provided.
All model fields use camelCase to match the generated Pydantic models.

Usage:
    env = (EnvironmentBuilder()
           .with_cluster("my-cluster")
           .with_fingerprint("a"*64)
           .with_kubernetes(KubernetesBuilder().with_version("1.28.0").with_node_count(3).build())
           .build())
"""

from perfeng.generated.environment import (
    Application,
    Compatibility,
    CpuArchitecture,
    EnvironmentSpecification,
    Kubernetes,
    NodePool,
    Runtime,
    Status,
)
from perfeng.metadata.types import AnyFeatureFlags


# -----------------------------------------------------------------------------
# Kubernetes Builder
# -----------------------------------------------------------------------------
class KubernetesBuilder:
    """Builder for Kubernetes model (fields: version, nodeCount, nodePools)."""

    def __init__(self) -> None:
        self._version: str | None = None
        self._node_count: int | None = None
        self._node_pools: list[NodePool] | None = None

    def with_version(self, version: str) -> "KubernetesBuilder":
        self._version = version
        return self

    def with_node_count(self, count: int) -> "KubernetesBuilder":
        self._node_count = count
        return self

    def with_node_pools(self, pools: list[NodePool]) -> "KubernetesBuilder":
        self._node_pools = pools
        return self

    def build(self) -> Kubernetes:
        return Kubernetes(
            version=self._version,
            nodeCount=self._node_count,
            nodePools=self._node_pools,
        )


# -----------------------------------------------------------------------------
# Runtime Builder
# -----------------------------------------------------------------------------
class RuntimeBuilder:
    """Builder for Runtime model (fields: containerRuntime, cni, storageClass, kernel)."""

    def __init__(self) -> None:
        self._container_runtime: str | None = None
        self._cni: str | None = None
        self._storage_class: str | None = None
        self._kernel: str | None = None

    def with_container_runtime(self, runtime: str) -> "RuntimeBuilder":
        self._container_runtime = runtime
        return self

    def with_cni(self, cni: str) -> "RuntimeBuilder":
        self._cni = cni
        return self

    def with_storage_class(self, storage_class: str) -> "RuntimeBuilder":
        self._storage_class = storage_class
        return self

    def with_kernel(self, kernel: str) -> "RuntimeBuilder":
        self._kernel = kernel
        return self

    def build(self) -> Runtime:
        return Runtime(
            containerRuntime=self._container_runtime,
            cni=self._cni,
            storageClass=self._storage_class,
            kernel=self._kernel,
        )


# -----------------------------------------------------------------------------
# Application Builder
# -----------------------------------------------------------------------------
class ApplicationBuilder:
    """Builder for Application model (fields: configurationHash, featureFlags)."""

    def __init__(self) -> None:
        self._configuration_hash: str | None = None
        self._feature_flags: AnyFeatureFlags | None = None

    def with_configuration_hash(self, hash_value: str) -> "ApplicationBuilder":
        self._configuration_hash = hash_value
        return self

    def with_feature_flags(self, flags: AnyFeatureFlags) -> "ApplicationBuilder":
        self._feature_flags = flags
        return self

    def build(self) -> Application:
        return Application(
            configurationHash=self._configuration_hash,
            featureFlags=self._feature_flags,
        )


# -----------------------------------------------------------------------------
# NodePool Builder
# -----------------------------------------------------------------------------
class NodePoolBuilder:
    """Builder for NodePool model (fields: name, nodeModel, cpuArchitecture, cpuCount, memoryGiB)."""

    def __init__(self) -> None:
        self._name: str | None = None
        self._node_model: str | None = None
        self._cpu_architecture: CpuArchitecture | None = None
        self._cpu_count: int | None = None
        self._memory_gi_b: float | None = None

    def with_name(self, name: str) -> "NodePoolBuilder":
        self._name = name
        return self

    def with_node_model(self, model: str) -> "NodePoolBuilder":
        self._node_model = model
        return self

    def with_cpu_architecture(self, arch: CpuArchitecture) -> "NodePoolBuilder":
        self._cpu_architecture = arch
        return self

    def with_cpu_count(self, count: int) -> "NodePoolBuilder":
        self._cpu_count = count
        return self

    def with_memory_gi_b(self, memory: float) -> "NodePoolBuilder":
        self._memory_gi_b = memory
        return self

    def build(self) -> NodePool:
        return NodePool(
            name=self._name,
            nodeModel=self._node_model,
            cpuArchitecture=self._cpu_architecture,
            cpuCount=self._cpu_count,
            memoryGiB=self._memory_gi_b,
        )


# -----------------------------------------------------------------------------
# Compatibility Builder
# -----------------------------------------------------------------------------
class CompatibilityBuilder:
    """Builder for Compatibility model (fields: status, reasons)."""

    def __init__(self) -> None:
        self._status: Status | None = None
        self._reasons: list[str] | None = None

    def with_status(self, status: Status) -> "CompatibilityBuilder":
        self._status = status
        return self

    def with_reasons(self, reasons: list[str]) -> "CompatibilityBuilder":
        self._reasons = reasons
        return self

    def build(self) -> Compatibility:
        return Compatibility(
            status=self._status,
            reasons=self._reasons,
        )


# -----------------------------------------------------------------------------
# EnvironmentSpecification Builder
# -----------------------------------------------------------------------------
class EnvironmentBuilder:
    """Builder for EnvironmentSpecification (fields: cluster, fingerprint, kubernetes, runtime, application, compatibility)."""

    def __init__(self) -> None:
        self._cluster: str | None = None
        self._fingerprint: str | None = None
        self._kubernetes: Kubernetes | None = None
        self._runtime: Runtime | None = None
        self._application: Application | None = None
        self._compatibility: Compatibility | None = None

    def with_cluster(self, cluster: str) -> "EnvironmentBuilder":
        self._cluster = cluster
        return self

    def with_fingerprint(self, fingerprint: str) -> "EnvironmentBuilder":
        self._fingerprint = fingerprint
        return self

    def with_kubernetes(self, kubernetes: Kubernetes) -> "EnvironmentBuilder":
        self._kubernetes = kubernetes
        return self

    def with_runtime(self, runtime: Runtime) -> "EnvironmentBuilder":
        self._runtime = runtime
        return self

    def with_application(self, application: Application) -> "EnvironmentBuilder":
        self._application = application
        return self

    def with_compatibility(self, compatibility: Compatibility) -> "EnvironmentBuilder":
        self._compatibility = compatibility
        return self

    def build(self) -> EnvironmentSpecification:
        # All fields are required, but can be None
        return EnvironmentSpecification(
            cluster=self._cluster,  # type: ignore[arg-type]  # will be set
            fingerprint=self._fingerprint,  # type: ignore[arg-type]
            kubernetes=self._kubernetes,
            runtime=self._runtime,
            application=self._application,
            compatibility=self._compatibility,
        )


# -----------------------------------------------------------------------------
# Default builders with common presets
# -----------------------------------------------------------------------------
def default_environment_builder() -> EnvironmentBuilder:
    """Return an EnvironmentBuilder with a default cluster and fingerprint."""
    return EnvironmentBuilder().with_cluster("test-cluster").with_fingerprint("a" * 64)


def default_kubernetes_builder() -> KubernetesBuilder:
    """Return a KubernetesBuilder with a default version and node count."""
    return KubernetesBuilder().with_version("v1.28.0").with_node_count(3)


def default_runtime_builder() -> RuntimeBuilder:
    """Return a RuntimeBuilder with common runtime values."""
    return (
        RuntimeBuilder()
        .with_container_runtime("containerd")
        .with_cni("calico")
        .with_storage_class("gp3")
        .with_kernel("5.15.0")
    )


def default_application_builder() -> ApplicationBuilder:
    """Return an ApplicationBuilder with a default configuration hash."""
    return ApplicationBuilder().with_configuration_hash("abc123")


def default_node_pool_builder() -> NodePoolBuilder:
    """Return a NodePoolBuilder with a default node pool configuration."""
    return (
        NodePoolBuilder()
        .with_name("pool-1")
        .with_node_model("m5.xlarge")
        .with_cpu_architecture(CpuArchitecture.amd64)
        .with_cpu_count(4)
        .with_memory_gi_b(16.0)
    )


def default_compatibility_builder() -> CompatibilityBuilder:
    """Return a CompatibilityBuilder with a default status."""
    return CompatibilityBuilder().with_status(Status.COMPATIBLE).with_reasons(["All checks passed"])
