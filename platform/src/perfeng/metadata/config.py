"""Configuration loading and merging for the metadata collector."""

import os
from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load collector configuration from file and environment defaults."""
    default_config = {
        "auto_detect": True,
        "timeout_seconds": 30,
        "kubeconfig_path": os.environ.get("KUBECONFIG", "~/.kube/config"),
        "fingerprint_excludes": [],
        "environment_config": {
            "cluster": os.environ.get("PERFENG_CLUSTER_NAME", "local"),
            "kubernetes": {
                "version": os.environ.get("PERFENG_K8S_VERSION"),
                "nodeCount": int(os.environ.get("PERFENG_NODE_COUNT", 1)),
            },
            "runtime": {
                "containerRuntime": os.environ.get("PERFENG_CONTAINER_RUNTIME"),
                "cni": os.environ.get("PERFENG_CNI"),
                "storageClass": os.environ.get("PERFENG_STORAGE_CLASS"),
                "kernel": os.environ.get("PERFENG_KERNEL_VERSION"),
            },
        },
    }

    if config_path and Path(config_path).exists():
        with open(config_path) as f:
            user_config = yaml.safe_load(f)
            if user_config:
                default_config = deep_merge(default_config, user_config)

    return default_config


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
