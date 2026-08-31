"""Fingerprint generation abstraction."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol


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
    """Wrapper around a provided fingerprint function."""

    def __init__(self, generate_fn: Callable[..., str]) -> None:
        self._generate = generate_fn

    def generate(
        self,
        *,
        cluster_name: str,
        k8s_version: str | None,
        node_os: str,
        container_runtime: str | None,
        excludes: list[str] | None = None,
    ) -> str:
        return self._generate(
            cluster_name=cluster_name,
            k8s_version=k8s_version,
            node_os=node_os,
            container_runtime=container_runtime,
            excludes=excludes,
        )
