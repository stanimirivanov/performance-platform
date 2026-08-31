"""EnvironmentSpecification builder with injected detectors."""

from __future__ import annotations

from perfeng.generated.environment import Application, EnvironmentSpecification, Kubernetes, Runtime
from perfeng.metadata.builders.fingerprint import DefaultFingerprintGenerator, FingerprintGenerator
from perfeng.metadata.config import CollectorConfig
from perfeng.metadata.detectors import KubernetesClusterDetector, LocalNodeDetector


class EnvironmentBuilder:
    """Builds an EnvironmentSpecification from typed config and live detectors."""

    def __init__(
        self,
        config: CollectorConfig,
        *,
        cluster_detector: KubernetesClusterDetector | None = None,
        node_detector: LocalNodeDetector | None = None,
        fingerprint_generator: FingerprintGenerator | None = None,
    ) -> None:
        self._config = config
        self._cluster_detector = cluster_detector
        self._node_detector = node_detector or LocalNodeDetector()
        self._fingerprint_generator = fingerprint_generator or DefaultFingerprintGenerator()

    def build(self) -> EnvironmentSpecification:
        """Assemble the full environment spec."""
        detected_cluster = self._detect_cluster()
        detected_node = self._node_detector.detect()

        cluster_name = self._resolve_cluster_name(detected_cluster)
        kubernetes = self._build_kubernetes(detected_cluster)
        runtime = self._build_runtime(detected_cluster, detected_node)
        application = self._build_application()

        # Kubernetes may be None; extract version safely
        k8s_version = kubernetes.version if kubernetes else None

        fingerprint = self._fingerprint_generator.generate(
            cluster_name=cluster_name,
            k8s_version=k8s_version,
            node_os=detected_node.os,
            container_runtime=runtime.containerRuntime,
            excludes=list(self._config.fingerprint_excludes),
        )

        return EnvironmentSpecification(
            cluster=cluster_name,
            fingerprint=fingerprint,
            kubernetes=kubernetes,
            runtime=runtime,
            application=application,
            compatibility=None,
        )

    def _detect_cluster(self):
        if self._config.auto_detect and self._cluster_detector is not None:
            return self._cluster_detector.detect()
        return None

    def _resolve_cluster_name(self, detected) -> str:
        return (
            (self._config.cluster.name if self._config.cluster else None)
            or (detected.name if detected else None)
            or "local"
        )

    def _build_kubernetes(self, detected_cluster) -> Kubernetes | None:
        cfg = self._config.kubernetes

        # If auto-detect is off and no Kubernetes config provided, do not build Kubernetes
        if cfg is None and not self._config.auto_detect:
            return None

        node_count = cfg.node_count if cfg else None
        version = cfg.version if cfg else None

        node_pools = None
        if self._config.auto_detect and self._cluster_detector is not None:
            if version is None:
                version = self._cluster_detector.detect_version()
            if node_count is None and detected_cluster is not None:
                node_count = detected_cluster.node_count
            node_pools = self._cluster_detector.detect_node_pools()

        if node_count is None:
            node_count = 1

        return Kubernetes(
            version=version,
            nodeCount=node_count,
            nodePools=node_pools,
        )

    def _build_runtime(self, detected_cluster, detected_node) -> Runtime:
        cfg = self._config.runtime

        container_runtime = cfg.container_runtime if cfg else None
        cni = cfg.cni if cfg else None
        storage_class = cfg.storage_class if cfg else None

        if self._config.auto_detect and self._cluster_detector is not None:
            container_runtime = (
                container_runtime or self._cluster_detector.detect_container_runtime()
            )
            cni = cni or self._cluster_detector.detect_cni()
            storage_class = storage_class or self._cluster_detector.detect_storage_class()

        return Runtime(
            containerRuntime=container_runtime,
            cni=cni,
            storageClass=storage_class,
            kernel=(cfg.kernel if cfg else None) or detected_node.kernel,
        )

    def _build_application(self) -> Application | None:
        cfg = self._config.application
        if cfg is None:
            return None
        return Application(
            configurationHash=cfg.configuration_hash,
            featureFlags=cfg.feature_flags or {},
        )
