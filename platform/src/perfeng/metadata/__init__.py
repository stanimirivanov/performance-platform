"""Performance metadata collection package."""

from perfeng.metadata.collector import (
    MetadataCollector,
    MetadataInput,
    MetadataOverrides,
    collect_run_metadata,
    get_metadata_collector,
)

__all__ = [
    "MetadataCollector",
    "MetadataOverrides",
    "MetadataInput",
    "get_metadata_collector",
    "collect_run_metadata",
]
