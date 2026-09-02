"""Pluggable system metric collectors."""

from perfeng.integration.collectors.composite import CompositeCollector
from perfeng.integration.collectors.cpu import CpuCollector
from perfeng.integration.collectors.disk import DiskCollector
from perfeng.integration.collectors.memory import MemoryCollector
from perfeng.integration.collectors.network import NetworkCollector

__all__ = [
    "CpuCollector",
    "MemoryCollector",
    "DiskCollector",
    "NetworkCollector",
    "CompositeCollector",
]
