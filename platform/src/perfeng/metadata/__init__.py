"""Performance metadata collection package."""

from perfeng.metadata.collector import (
    MetadataCollector,
    collect_run_metadata,
    get_metadata_collector,
)

__all__ = [
    "MetadataCollector",
    "get_metadata_collector",
    "collect_run_metadata",
]
