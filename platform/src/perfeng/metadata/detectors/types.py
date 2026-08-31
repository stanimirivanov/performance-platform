"""Typed data structures for detection results."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ClusterType(Enum):
    """Supported cluster types."""

    KUBERNETES = "k8s"
    DOCKER = "docker"
    LOCAL = "local"


@dataclass(frozen=True, slots=True)
class NodeResources:
    """Hardware resources available on a node."""

    cpu_cores: int
    memory_total_gb: float | None = None
    disk_total_gb: float | None = None


@dataclass(frozen=True, slots=True)
class NodeInfo:
    """Information about a single node."""

    os: str
    kernel: str
    architecture: str
    resources: NodeResources


@dataclass(frozen=True, slots=True)
class ClusterInfo:
    """High-level cluster metadata."""

    name: str
    type: ClusterType
    node_count: int
