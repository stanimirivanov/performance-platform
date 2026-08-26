"""
Configuration loader for metadata collector with environment-specific
initialization (local, dev, staging, prod, test).
"""

import os
from pathlib import Path
from typing import Any, Literal

import yaml

from perfeng.metadata.collector import MetadataCollector

# Define EnvironmentType using Literal
EnvironmentType = Literal["local", "dev", "staging", "prod", "test"]


class ConfigLoader:
    """Loads environment-specific configuration for metadata collection."""

    def __init__(self, env_type: EnvironmentType | None = None) -> None:
        self.env_type = env_type or self._detect_environment()
        self.config_dir = Path(os.environ.get("PERFENG_CONFIG_DIR", "~/.perfeng")).expanduser()

    def _detect_environment(self) -> EnvironmentType:
        """Detect the current environment."""
        # Check environment variable first
        env = os.environ.get("PERFENG_ENV", "").lower()
        if env in ["local", "dev", "staging", "prod", "test"]:
            return env  # type: ignore

        # Detect from K8s namespace
        try:
            with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace") as f:
                namespace = f.read().strip()
                if namespace.endswith("-prod"):
                    return "prod"
                elif namespace.endswith("-staging"):
                    return "staging"
                elif namespace.endswith("-dev"):
                    return "dev"
        except FileNotFoundError:
            pass

        # Default to local
        return "local"

    def load_config(self) -> dict[str, Any]:
        """Load environment-specific configuration."""
        # Load base config
        base_config = self._load_base_config()

        # Load environment-specific config
        env_config = self._load_env_config()

        # Merge with environment overrides
        return self._deep_merge(base_config, env_config)

    def _load_base_config(self) -> dict[str, Any]:
        """Load base configuration."""
        base_paths = [
            self.config_dir / "base.yaml",
            Path("/etc/perfeng/base.yaml"),
            Path(__file__).parent.parent.parent.parent / "config" / "base.yaml",
        ]

        for path in base_paths:
            if path.exists():
                with open(path) as f:
                    return yaml.safe_load(f)

        # Default base config
        return {
            "auto_detect": True,
            "timeout_seconds": 30,
            "fingerprint_excludes": ["local", "test"],
            "environment_config": {
                "runtime": {"kernel": None},
            },
        }

    def _load_env_config(self) -> dict[str, Any]:
        """Load environment-specific configuration."""
        env_paths = [
            self.config_dir / f"{self.env_type}.yaml",
            Path("/etc/perfeng") / f"{self.env_type}.yaml",
            Path(__file__).parent.parent.parent.parent / "config" / f"{self.env_type}.yaml",
        ]

        for path in env_paths:
            if path.exists():
                with open(path) as f:
                    return yaml.safe_load(f)

        # Return empty if no env config found
        return {}

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def load_environment_variables(self) -> dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}

        # Map environment variables to config structure
        env_mappings = {
            "PERFENG_CLUSTER_NAME": "environment_config.cluster",
            "PERFENG_AUTO_DETECT": "auto_detect",
            "PERFENG_TIMEOUT": "timeout_seconds",
            "PERFENG_K8S_VERSION": "environment_config.kubernetes.version",
            "PERFENG_NODE_COUNT": "environment_config.kubernetes.nodeCount",
            "PERFENG_CONTAINER_RUNTIME": "environment_config.runtime.containerRuntime",
            "PERFENG_CNI": "environment_config.runtime.cni",
            "PERFENG_STORAGE_CLASS": "environment_config.runtime.storageClass",
            "PERFENG_KERNEL_VERSION": "environment_config.runtime.kernel",
            "PERFENG_APP_CONFIG_HASH": "environment_config.application.configurationHash",
        }

        for env_var, config_path in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert to appropriate type
                if env_var == "PERFENG_AUTO_DETECT":
                    value = value.lower() == "true"
                elif env_var in ("PERFENG_TIMEOUT", "PERFENG_NODE_COUNT"):
                    value = int(value)
                self._set_nested_value(env_config, config_path, value)

        return env_config

    def _set_nested_value(self, config: dict, path: str, value: Any) -> None:
        """Set a nested value in a dictionary using dot notation path."""
        keys = path.split(".")
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value


def create_collector_for_environment(
    env_type: EnvironmentType | None = None,
) -> MetadataCollector:
    """
    Create a metadata collector configured for a specific environment.

    Args:
        env_type: The environment type ('local', 'dev', 'staging', 'prod', 'test').

    Returns:
        A MetadataCollector instance with merged configuration.
    """
    from .collector import MetadataCollector

    loader = ConfigLoader(env_type)

    # Load configuration from multiple sources
    config = loader.load_config()

    # Override with environment variables
    env_config = loader.load_environment_variables()
    config = loader._deep_merge(config, env_config)

    # Create collector with merged config dictionary (no temp file needed)
    collector = MetadataCollector(config_dict=config)

    return collector
