"""
Unit tests for the configuration loader.
"""

import os
from unittest.mock import patch

from perfeng.metadata.config_loader import ConfigLoader, create_collector_for_environment


class TestConfigLoader:
    """Test cases for ConfigLoader."""

    def test_init_default(self):
        """Test default initialization."""
        loader = ConfigLoader()
        assert loader.env_type in ["local", "dev", "staging", "prod", "test"]

    def test_init_with_env(self):
        """Test initialization with specific environment."""
        loader = ConfigLoader("local")
        assert loader.env_type == "local"

        loader = ConfigLoader("prod")
        assert loader.env_type == "prod"

    @patch.dict(os.environ, {"PERFENG_ENV": "prod"})
    def test_detect_environment_from_env(self):
        """Test environment detection from environment variable."""
        loader = ConfigLoader()
        assert loader.env_type == "prod"

    @patch.dict(os.environ, {}, clear=True)
    @patch("builtins.open")
    def test_detect_environment_from_namespace(self, mock_open):
        """Test environment detection from Kubernetes namespace."""
        mock_open.return_value.__enter__.return_value.read.return_value = "my-app-prod"
        loader = ConfigLoader()
        assert loader.env_type == "prod"

    @patch.dict(os.environ, {}, clear=True)
    def test_detect_environment_default(self):
        """Test default environment detection."""
        loader = ConfigLoader()
        assert loader.env_type == "local"

    def test_load_base_config(self, tmp_path):
        """Test loading base configuration."""
        # Create test config
        config_dir = tmp_path / ".perfeng"
        config_dir.mkdir()
        base_config = config_dir / "base.yaml"
        base_config.write_text("""
            auto_detect: true
            timeout_seconds: 60
            fingerprint_excludes: []
        """)

        with patch.dict(os.environ, {"PERFENG_CONFIG_DIR": str(config_dir)}):
            loader = ConfigLoader("local")
            config = loader._load_base_config()

            assert config["auto_detect"] is True
            assert config["timeout_seconds"] == 60

    def test_load_base_config_default(self):
        """Test loading base configuration when no file exists."""
        loader = ConfigLoader("local")
        config = loader._load_base_config()

        # Should return defaults
        assert "auto_detect" in config
        assert "timeout_seconds" in config
        assert "fingerprint_excludes" in config

    def test_load_env_config(self, tmp_path):
        """Test loading environment-specific configuration."""
        config_dir = tmp_path / ".perfeng"
        config_dir.mkdir()
        env_config = config_dir / "local.yaml"
        env_config.write_text("""
            environment_config:
                cluster: test-cluster
                kubernetes:
                    version: v1.28.0
        """)

        with patch.dict(os.environ, {"PERFENG_CONFIG_DIR": str(config_dir)}):
            loader = ConfigLoader("local")
            config = loader._load_env_config()

            assert config["environment_config"]["cluster"] == "test-cluster"
            assert config["environment_config"]["kubernetes"]["version"] == "v1.28.0"

    def test_load_env_config_default(self):
        """Test loading environment config when no file exists."""
        loader = ConfigLoader("local")
        config = loader._load_env_config()

        # Should return empty dict
        assert config == {}

    def test_deep_merge(self, loader):
        """Test deep merge of dictionaries."""
        base = {"a": 1, "b": {"c": 2, "d": 3}}
        override = {"b": {"c": 4, "e": 5}, "f": 6}

        result = loader._deep_merge(base, override)

        assert result["a"] == 1
        assert result["b"]["c"] == 4
        assert result["b"]["d"] == 3
        assert result["b"]["e"] == 5
        assert result["f"] == 6

    def test_load_environment_variables(self, loader):
        """Test loading configuration from environment variables."""
        with patch.dict(
            os.environ,
            {
                "PERFENG_CLUSTER_NAME": "env-cluster",
                "PERFENG_AUTO_DETECT": "false",
                "PERFENG_TIMEOUT": "60",
                "PERFENG_K8S_VERSION": "v1.27.0",
                "PERFENG_NODE_COUNT": "5",
                "PERFENG_CONTAINER_RUNTIME": "containerd",
            },
        ):
            config = loader.load_environment_variables()

            assert config["environment_config"]["cluster"] == "env-cluster"
            assert config["auto_detect"] is False
            assert config["timeout_seconds"] == 60
            assert config["environment_config"]["kubernetes"]["version"] == "v1.27.0"
            assert config["environment_config"]["kubernetes"]["nodeCount"] == 5
            assert config["environment_config"]["runtime"]["containerRuntime"] == "containerd"

    def test_load_complete_config(self, tmp_path):
        """Test loading complete configuration from all sources."""
        config_dir = tmp_path / ".perfeng"
        config_dir.mkdir()

        # Base config
        base_config = config_dir / "base.yaml"
        base_config.write_text("""
            auto_detect: true
            timeout_seconds: 30
            fingerprint_excludes: ['test']
        """)

        # Environment config
        env_config = config_dir / "dev.yaml"
        env_config.write_text("""
            environment_config:
                cluster: dev-cluster
                kubernetes:
                    version: v1.28.0
                    nodeCount: 3
        """)

        with patch.dict(
            os.environ, {"PERFENG_CONFIG_DIR": str(config_dir), "PERFENG_AUTO_DETECT": "false"}
        ):
            loader = ConfigLoader("dev")
            config = loader.load_config()

            # Environment variable overrides base
            assert config["auto_detect"] is False

            # Environment config loaded
            assert config["environment_config"]["cluster"] == "dev-cluster"
            assert config["environment_config"]["kubernetes"]["version"] == "v1.28.0"
            assert config["environment_config"]["kubernetes"]["nodeCount"] == 3

            # Base config preserved
            assert config["fingerprint_excludes"] == ["test"]


class TestFactoryFunctions:
    """Test factory functions."""

    def test_create_collector_for_environment(self):
        """Test creating a collector for a specific environment."""
        collector = create_collector_for_environment("local")
        assert collector is not None

        # Should have loaded configuration
        assert hasattr(collector, "collect_environment")
        assert hasattr(collector, "config")

    def test_create_collector_with_no_env(self):
        """Test creating a collector without specifying environment."""
        collector = create_collector_for_environment()
        assert collector is not None
        assert hasattr(collector, "collect_environment")
