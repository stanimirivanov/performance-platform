"""Default configuration values."""

from perfeng.metadata.config.models import CollectorConfig

DEFAULT_CONFIG = CollectorConfig(
    auto_detect=True,
    timeout_seconds=30,
    fingerprint_excludes=(),
    cluster=None,
    kubernetes=None,
    runtime=None,
    application=None,
)
