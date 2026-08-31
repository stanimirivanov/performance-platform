"""Fingerprint generation abstraction."""

from __future__ import annotations

from typing import Any, Protocol


class FingerprintGenerator(Protocol):
    """Protocol for cluster fingerprint generation."""

    def generate(
        self,
        *,
        cluster_name: str,
        k8s_version: str | None,
        node_os: str,
        container_runtime: str | None,
        excludes: list[str] | None = None,
    ) -> str: ...


class DefaultFingerprintGenerator:
    """Thin wrapper around the existing fingerprint module."""

    def __init__(self, module: Any | None = None) -> None:
        if module is None:
            from perfeng.metadata import fingerprint as _fp

            module = _fp
        self._module = module

    def generate(
        self,
        *,
        cluster_name: str,
        k8s_version: str | None,
        node_os: str,
        container_runtime: str | None,
        excludes: list[str] | None = None,
    ) -> str:
        return self._module.generate_fingerprint(
            cluster_name=cluster_name,
            k8s_version=k8s_version,
            node_os=node_os,
            container_runtime=container_runtime,
            excludes=excludes,
        )
