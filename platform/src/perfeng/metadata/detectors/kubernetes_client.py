"""Lightweight kubectl wrapper with caching."""

from __future__ import annotations

import json
import subprocess
from typing import Any


class KubectlError(Exception):
    """Raised when a kubectl command fails or is unavailable."""

    pass


class KubectlClient:
    """Wraps kubectl with consistent error handling and simple JSON caching."""

    def __init__(self, timeout: int = 10) -> None:
        self._timeout = timeout
        self._cache: dict[tuple[str, ...], Any] = {}  # tuple key for safety

    def run(self, *args: str) -> str:
        """Execute a kubectl command and return stdout.

        Raises:
            KubectlError: if kubectl is missing, times out, or returns non-zero.
        """
        try:
            result = subprocess.run(
                ["kubectl", *args],
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except FileNotFoundError as exc:
            raise KubectlError("kubectl not found in PATH") from exc
        except subprocess.TimeoutExpired as exc:
            raise KubectlError(f"kubectl timed out after {self._timeout}s") from exc

        if result.returncode != 0:
            raise KubectlError(f"kubectl {' '.join(args)} failed: {result.stderr.strip()}")
        return result.stdout

    def _fetch_json(self, *args: str) -> dict[str, Any]:
        """Run a kubectl command and parse JSON output with caching."""
        if args not in self._cache:
            output = self.run(*args)
            try:
                self._cache[args] = json.loads(output)
            except json.JSONDecodeError as exc:
                raise KubectlError(f"Invalid JSON from kubectl: {exc}") from exc
        return self._cache[args]

    def get_nodes(self) -> dict[str, Any]:
        return self._fetch_json("get", "nodes", "-o", "json")

    def get_storage_classes(self) -> dict[str, Any]:
        return self._fetch_json("get", "storageclass", "-o", "json")

    def get_pods(self, namespace: str, label_selector: str) -> str:
        return self.run("get", "pods", "-n", namespace, "-l", label_selector, "-o", "name")

    def version(self) -> dict[str, Any]:
        return self._fetch_json("version", "--short", "-o", "json")

    def current_context(self) -> str:
        return self.run("config", "current-context").strip()
