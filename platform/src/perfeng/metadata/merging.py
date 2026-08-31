"""Pure functions for merging CollectorConfig instances."""

from __future__ import annotations

from perfeng.metadata.config.models import CollectorConfig


def merge_collector_config(
    base: CollectorConfig,
    overrides: CollectorConfig | None,
) -> CollectorConfig:
    """Return a new CollectorConfig with fields from `overrides` taking precedence.

    None values in overrides are ignored (i.e., they don't override base values).
    """
    if overrides is None:
        return base

    # Merge cluster
    cluster = base.cluster
    if overrides.cluster is not None:
        if cluster is None:
            cluster = overrides.cluster
        else:
            cluster = type(cluster)(
                name=overrides.cluster.name or cluster.name,
                type=overrides.cluster.type or cluster.type,
            )

    # Merge kubernetes
    kubernetes = base.kubernetes
    if overrides.kubernetes is not None:
        if kubernetes is None:
            kubernetes = overrides.kubernetes
        else:
            kubernetes = type(kubernetes)(
                version=overrides.kubernetes.version or kubernetes.version,
                node_count=(
                    overrides.kubernetes.node_count
                    if overrides.kubernetes.node_count is not None
                    else kubernetes.node_count
                ),
                node_pools=(
                    overrides.kubernetes.node_pools
                    if overrides.kubernetes.node_pools is not None
                    else kubernetes.node_pools
                ),
            )

    # Merge runtime
    runtime = base.runtime
    if overrides.runtime is not None:
        if runtime is None:
            runtime = overrides.runtime
        else:
            runtime = type(runtime)(
                container_runtime=overrides.runtime.container_runtime or runtime.container_runtime,
                cni=overrides.runtime.cni or runtime.cni,
                storage_class=overrides.runtime.storage_class or runtime.storage_class,
                kernel=overrides.runtime.kernel or runtime.kernel,
            )

    # application: overrides replace entirely if provided
    application = overrides.application if overrides.application is not None else base.application

    return CollectorConfig(
        auto_detect=overrides.auto_detect
        if overrides.auto_detect is not None
        else base.auto_detect,
        timeout_seconds=overrides.timeout_seconds
        if overrides.timeout_seconds is not None
        else base.timeout_seconds,
        fingerprint_excludes=overrides.fingerprint_excludes
        if overrides.fingerprint_excludes
        else base.fingerprint_excludes,
        cluster=cluster,
        kubernetes=kubernetes,
        runtime=runtime,
        application=application,
    )
