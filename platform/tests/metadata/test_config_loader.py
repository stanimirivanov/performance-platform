"""
Unit tests for the new ConfigLoader.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from perfeng.metadata.config.loader import ConfigLoader, load_collector_config
from perfeng.metadata.config.models import CollectorConfig


@pytest.fixture
def temp_config_dir(tmp_path) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


def write_yaml(path: Path, data: dict):
    import yaml

    path.write_text(yaml.safe_dump(data))


class TestConfigLoader:
    def test_load_defaults(self):
        loader = ConfigLoader("local")
        config = loader.load()
        assert isinstance(config, CollectorConfig)
        assert config.auto_detect is True
        assert config.timeout_seconds == 30

    def test_load_base_yaml(self, temp_config_dir):
        write_yaml(temp_config_dir / "base.yaml", {"auto_detect": False, "timeout_seconds": 60})
        with patch.dict(os.environ, {"PERFENG_CONFIG_DIR": str(temp_config_dir)}):
            loader = ConfigLoader("local")
            config = loader.load()
            assert config.auto_detect is False
            assert config.timeout_seconds == 60

    def test_load_env_yaml_override(self, temp_config_dir):
        write_yaml(temp_config_dir / "base.yaml", {"auto_detect": True})
        write_yaml(
            temp_config_dir / "local.yaml",
            {"cluster": {"name": "test-cluster"}, "kubernetes": {"version": "v1.28.0"}},
        )
        with patch.dict(os.environ, {"PERFENG_CONFIG_DIR": str(temp_config_dir)}):
            loader = ConfigLoader("local")
            config = loader.load()
            assert config.cluster.name == "test-cluster"
            assert config.kubernetes.version == "v1.28.0"

    def test_env_variables_override(self, temp_config_dir):
        with patch.dict(
            os.environ,
            {
                "PERFENG_CONFIG_DIR": str(temp_config_dir),
                "PERFENG_AUTO_DETECT": "false",
                "PERFENG_CLUSTER_NAME": "env-cluster",
                "PERFENG_NODE_COUNT": "5",
            },
        ):
            loader = ConfigLoader("local")
            config = loader.load()
            assert config.auto_detect is False
            assert config.cluster.name == "env-cluster"
            assert config.kubernetes.node_count == 5

    def test_load_collector_config_function(self):
        config = load_collector_config("local")
        assert isinstance(config, CollectorConfig)
