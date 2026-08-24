"""Tests for schema validation."""

from __future__ import annotations

import json
from pathlib import Path

from perfeng.utils.validation import validate_run_metadata, validate_test_result


def load_example(name: str) -> dict:
    """Load an example JSON file."""
    path = Path(__file__).parent.parent.parent / "examples" / "metadata" / name
    with open(path) as f:
        return json.load(f)


def test_run_metadata_example_valid() -> None:
    """Test that the example run metadata is valid."""
    data = load_example("run-metadata-example.json")
    errors = validate_run_metadata(data)
    assert not errors, f"Validation errors: {errors}"


def test_test_result_example_valid() -> None:
    """Test that the example test result is valid."""
    data = load_example("test-result-example.json")
    errors = validate_test_result(data)
    assert not errors, f"Validation errors: {errors}"


def test_invalid_run_metadata() -> None:
    """Test that invalid metadata is rejected."""
    data = {"run": {"id": "invalid"}}
    errors = validate_run_metadata(data)
    assert errors
