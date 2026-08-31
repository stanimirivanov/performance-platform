"""Configuration loader that merges YAML files, environment variables, and defaults."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from perfeng.metadata.config.defaults import DEFAULT_CONFIG
from perfeng.metadata.config.models import (
    ApplicationConfig,
    ClusterConfig,
    CollectorConfig,
    KubernetesConfig,
    RuntimeConfig,
)


class ConfigLoader:
    """Load configuration from files and environment variables.

    The loader supports the following sources (in order of precedence):
        1. Environment variables (PERFENG_*)
        2. Environment-specific YAML file (e.g., dev.yaml)
        3. Base YAML file (base.yaml)
        4. Built-in defaults

    Merging is deep for nested dictionaries.
    """

    def __init__(self, env_type: str | None = None):
        self.env_type = env_type or self._detect_environment()
        self.config_dir = Path(os.environ.get("PERFENG_CONFIG_DIR", "~/.perfeng")).expanduser()

    def load(self) -> CollectorConfig:
        """Load and merge all configuration sources into a CollectorConfig."""
        base_data = self._load_base_yaml()
        env_data = self._load_env_yaml()
        env_vars = self._load_env_vars()

        merged = self._deep_merge(base_data, env_data)
        merged = self._deep_merge(merged, env_vars)

        return self._to_config(merged)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_environment(self) -> str:
        """Determine the current environment from env var or Kubernetes namespace."""
        env = os.environ.get("PERFENG_ENV", "").lower()
        if env in {"local", "dev", "staging", "prod", "test"}:
            return env

        # Fallback: detect from Kubernetes namespace
        try:
            namespace_file = Path("/var/run/secrets/kubernetes.io/serviceaccount/namespace")
            if namespace_file.exists():
                namespace = namespace_file.read_text().strip()
                if namespace.endswith("-prod"):
                    return "prod"
                if namespace.endswith("-staging"):
                    return "staging"
                if namespace.endswith("-dev"):
                    return "dev"
        except OSError:
            pass

        return "local"

    def _load_base_yaml(self) -> dict[str, Any]:
        """Load base.yaml from config directory or fallback location."""
        candidates = [
            self.config_dir / "base.yaml",
            Path("/etc/perfeng/base.yaml"),
            Path(__file__).parents[3] / "config" / "base.yaml",
        ]
        for path in candidates:
            if path.exists():
                return self._read_yaml(path)
        return {}

    def _load_env_yaml(self) -> dict[str, Any]:
        """Load environment-specific YAML (e.g., dev.yaml)."""
        candidates = [
            self.config_dir / f"{self.env_type}.yaml",
            Path("/etc/perfeng") / f"{self.env_type}.yaml",
            Path(__file__).parents[3] / "config" / f"{self.env_type}.yaml",
        ]
        for path in candidates:
            if path.exists():
                return self._read_yaml(path)
        return {}

    @staticmethod
    def _read_yaml(path: Path) -> dict[str, Any]:
        with path.open("r") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}

    def _load_env_vars(self) -> dict[str, Any]:
        """Extract configuration from PERFENG_* environment variables."""
        env_config: dict[str, Any] = {}

        mappings = {
            "PERFENG_AUTO_DETECT": "auto_detect",
            "PERFENG_TIMEOUT": "timeout_seconds",
            "PERFENG_FINGERPRINT_EXCLUDES": "fingerprint_excludes",
            "PERFENG_CLUSTER_NAME": "cluster.name",
            "PERFENG_CLUSTER_TYPE": "cluster.type",
            "PERFENG_K8S_VERSION": "kubernetes.version",
            "PERFENG_NODE_COUNT": "kubernetes.node_count",
            "PERFENG_CONTAINER_RUNTIME": "runtime.container_runtime",
            "PERFENG_CNI": "runtime.cni",
            "PERFENG_STORAGE_CLASS": "runtime.storage_class",
            "PERFENG_KERNEL_VERSION": "runtime.kernel",
            "PERFENG_APP_CONFIG_HASH": "application.configuration_hash",
        }

        for env_var, config_path in mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert value to appropriate type
                if env_var == "PERFENG_AUTO_DETECT":
                    value = value.lower() == "true"
                elif env_var == "PERFENG_TIMEOUT" or env_var == "PERFENG_NODE_COUNT":
                    value = int(value)
                elif env_var == "PERFENG_FINGERPRINT_EXCLUDES":
                    value = [item.strip() for item in value.split(",") if item.strip()]
                self._set_nested_value(env_config, config_path, value)

        return env_config

    @staticmethod
    def _set_nested_value(data: dict[str, Any], dotted_path: str, value: Any) -> None:
        keys = dotted_path.split(".")
        current = data
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        current[keys[-1]] = value

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Recursively merge override into base."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigLoader._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def _to_config(data: dict[str, Any]) -> CollectorConfig:
        """Convert a merged dictionary into a typed CollectorConfig."""
        config = DEFAULT_CONFIG

        # fingerprint_excludes
        excludes = data.get("fingerprint_excludes", ())
        if isinstance(excludes, str):
            excludes = tuple(item.strip() for item in excludes.split(",") if item.strip())
        else:
            excludes = tuple(excludes)

        # sub-configs
        cluster = None
        if "cluster" in data:
            cluster_data = data["cluster"]
            cluster = ClusterConfig(
                name=cluster_data.get("name"),
                type=cluster_data.get("type"),
            )

        kubernetes = None
        if "kubernetes" in data:
            k8s_data = data["kubernetes"]
            kubernetes = KubernetesConfig(
                version=k8s_data.get("version"),
                node_count=k8s_data.get("node_count"),
                node_pools=tuple(k8s_data.get("node_pools", ())),
            )

        runtime = None
        if "runtime" in data:
            runtime_data = data["runtime"]
            runtime = RuntimeConfig(
                container_runtime=runtime_data.get("container_runtime"),
                cni=runtime_data.get("cni"),
                storage_class=runtime_data.get("storage_class"),
                kernel=runtime_data.get("kernel"),
            )

        application = None
        if "application" in data:
            app_data = data["application"]
            application = ApplicationConfig(
                configuration_hash=app_data.get("configuration_hash"),
                feature_flags=app_data.get("feature_flags", {}),
            )

        return CollectorConfig(
            auto_detect=data.get("auto_detect", config.auto_detect),
            timeout_seconds=data.get("timeout_seconds", config.timeout_seconds),
            fingerprint_excludes=excludes,
            cluster=cluster,
            kubernetes=kubernetes,
            runtime=runtime,
            application=application,
        )


def load_collector_config(env_type: str | None = None) -> CollectorConfig:
    """Convenience function to load configuration for a given environment."""
    loader = ConfigLoader(env_type)
    return loader.load()
