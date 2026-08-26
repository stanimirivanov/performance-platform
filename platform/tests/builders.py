"""
Test builders for creating instances of generated environment models.
These builders simplify test setup by setting optional fields to None
unless explicitly provided.
"""

from typing import Any

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


class KubernetesBuilder:
    """Builder for Kubernetes model."""

    def __init__(self):
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
            node_count=self._node_count,
            node_pools=self._node_pools,
        )


class RuntimeBuilder:
    """Builder for Runtime model."""

    def __init__(self):
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
            container_runtime=self._container_runtime,
            cni=self._cni,
            storage_class=self._storage_class,
            kernel=self._kernel,
        )


class ApplicationBuilder:
    """Builder for Application model."""

    def __init__(self):
        self._configuration_hash: str | None = None
        self._feature_flags: dict[str, Any] | None = None

    def with_configuration_hash(self, hash: str) -> "ApplicationBuilder":
        self._configuration_hash = hash
        return self

    def with_feature_flags(self, flags: dict[str, Any]) -> "ApplicationBuilder":
        self._feature_flags = flags
        return self

    def build(self) -> Application:
        return Application(
            configuration_hash=self._configuration_hash,
            feature_flags=self._feature_flags,
        )


class NodePoolBuilder:
    """Builder for NodePool model."""

    def __init__(self):
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
            node_model=self._node_model,
            cpu_architecture=self._cpu_architecture,
            cpu_count=self._cpu_count,
            memory_gi_b=self._memory_gi_b,
        )


class CompatibilityBuilder:
    """Builder for Compatibility model."""

    def __init__(self):
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


class EnvironmentBuilder:
    """Builder for EnvironmentSpecification model."""

    def __init__(self):
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
            cluster=self._cluster,  # type: ignore (will be set)
            fingerprint=self._fingerprint,  # type: ignore
            kubernetes=self._kubernetes,
            runtime=self._runtime,
            application=self._application,
            compatibility=self._compatibility,
        )


# Convenience functions to create default builders with common presets
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


def default_node_pool_builder() -> NodePoolBuilder:
    """Return a NodePoolBuilder with a default node pool."""
    return (
        NodePoolBuilder()
        .with_name("pool-1")
        .with_node_model("m5.xlarge")
        .with_cpu_architecture(CpuArchitecture.amd64)
        .with_cpu_count(4)
        .with_memory_gi_b(16.0)
    )
