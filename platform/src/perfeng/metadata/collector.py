"""Main metadata collector orchestrator."""

from pathlib import Path
from typing import Any

from perfeng.generated.environment import EnvironmentSpecification
from perfeng.generated.run_metadata import PerformanceRunMetadata

from . import builders
from . import config as cfg


class MetadataCollector:
    """
    Collects metadata about the test runner environment using the
    Environment Specification schema.

    The collector detects the environment where the test runner is executing
    and creates a validated EnvironmentSpecification object.
    """

    def __init__(
        self,
        config_path: str | Path | None = None,
        config_dict: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the collector.

        Args:
            config_path: Path to a YAML configuration file.
            config_dict: In-memory configuration dictionary.
        """
        if config_dict is not None:
            self.config = config_dict
        else:
            self.config = cfg.load_config(config_path)
        self.override_values: dict[str, Any] = {}
        self._environment_cache: EnvironmentSpecification | None = None

    def set_override(self, key: str, value: Any) -> None:
        """
        Set a manual override for a metadata value.

        Args:
            key: Override key (e.g., "environment", "test_metadata").
            value: Override value.
        """
        self.override_values[key] = value

    def collect_environment(self) -> EnvironmentSpecification:
        """
        Collect environment information and return as validated schema.

        Priority:
        1. Manual overrides
        2. Environment variables (PERFENG_*)
        3. Configuration file
        4. Auto-detection (if enabled)
        """
        if "environment" in self.override_values:
            env_data = self.override_values["environment"]
            return EnvironmentSpecification(**env_data)

        if self._environment_cache:
            return self._environment_cache

        env_spec = builders.build_environment_spec(
            self.config,
            auto_detect=self.config.get("auto_detect", True),
        )
        self._environment_cache = env_spec
        return env_spec

    def collect_test_metadata(
        self,
        test_name: str,
        status: str = "CREATED",
        **kwargs,
    ) -> PerformanceRunMetadata:
        """
        Collect complete test metadata and return a PerformanceRunMetadata instance.

        Args:
            test_name: Name of the test (used as suite and scenario).
            status: Initial status string (mapped to RunStatus enum).
            **kwargs: Additional parameters to populate nested models.
                Common keys: test_profile, trigger_type, tool, toolVersion,
                scenario, gitSha, version, branch, replicas, cpuRequests, etc.

        Returns:
            A fully populated PerformanceRunMetadata instance.
        """
        env_spec = self.collect_environment()
        metadata = builders.build_performance_run_metadata(
            test_name,
            status,
            env_spec,
            kwargs,
        )

        # Apply overrides (support dotted notation)
        if "test_metadata" in self.override_values:
            override = self.override_values["test_metadata"]
            for key, value in override.items():
                parts = key.split(".")
                obj = metadata
                for part in parts[:-1]:
                    obj = getattr(obj, part, None)
                    if obj is None:
                        break
                else:
                    setattr(obj, parts[-1], value)

        return metadata


# -----------------------------------------------------------------------------
# Convenience functions
# -----------------------------------------------------------------------------


def get_metadata_collector(
    config_path: str | Path | None = None,
) -> MetadataCollector:
    """Factory function for metadata collector."""
    return MetadataCollector(config_path)


def collect_run_metadata(test_name: str, **kwargs) -> dict[str, Any]:
    """
    Convenience function to collect run metadata and return as a dict.

    Args:
        test_name: Name of the test.
        **kwargs: Additional parameters passed to collect_test_metadata.

    Returns:
        Dictionary representation of the run metadata.
    """
    collector = MetadataCollector()
    metadata = collector.collect_test_metadata(test_name, **kwargs)
    return metadata.model_dump(exclude_none=True)
