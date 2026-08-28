"""Tests for schema validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from perfeng.generated import RunMetadata
from perfeng.utils.validation import (
    validate_pydantic_model,
    validate_run_metadata,
    validate_test_result,
)


def load_example(name: str) -> dict[str, Any]:
    """Load an example JSON file.

    Args:
        name: Name of the example file.

    Returns:
        The example data as a dictionary.
    """
    path = Path(__file__).parent.parent.parent.parent / "examples" / "metadata" / name
    with open(path) as f:
        return cast(dict[str, Any], json.load(f))


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
    data: dict[str, Any] = {"run": {"id": "invalid"}}
    errors = validate_run_metadata(data)
    assert errors


def test_pydantic_model_validation() -> None:
    """Test Pydantic model validation."""
    data = load_example("run-metadata-example.json")
    model, errors = validate_pydantic_model(data, RunMetadata)
    assert model is not None, f"Validation errors: {errors}"
    assert not errors
    assert model.run.id == "perf-20240115-143022-ab12cd34"


def test_pydantic_model_validation_without_optional_fields() -> None:
    """Test Pydantic model validation works without optional fields."""
    data = load_example("run-metadata-example.json")

    # Remove only fields that are truly optional (not enums with null)
    # Note: cpuArchitecture is kept because the generator treats it as required
    del data["run"]["notes"]
    del data["run"]["policyVersion"]
    del data["test"]["workloadVersion"]
    del data["test"]["configHash"]
    del data["candidate"]["imageDigest"]
    del data["candidate"]["version"]
    del data["candidate"]["branch"]
    del data["candidate"]["configurationHash"]
    del data["candidate"]["featureFlags"]
    del data["candidate"]["databaseMigrationVersion"]
    del data["environment"]["nodePool"]
    del data["environment"]["nodeModel"]
    # Keep cpuArchitecture - generator has issue with enum + null
    # del data["environment"]["cpuArchitecture"]
    del data["environment"]["kernel"]
    del data["environment"]["containerRuntime"]
    del data["environment"]["cni"]
    del data["environment"]["storageClass"]
    del data["environment"]["fingerprint"]
    del data["environment"]["nodeCount"]
    del data["environment"]["region"]
    del data["runtime"]
    del data["data"]
    del data["phases"]

    model, errors = validate_pydantic_model(data, RunMetadata)
    assert model is not None, f"Validation errors: {errors}"
    assert not errors


def test_pydantic_model_invalid() -> None:
    """Test Pydantic model rejects invalid data."""
    data: dict[str, Any] = {"run": {"id": "invalid"}}
    model, errors = validate_pydantic_model(data, RunMetadata)
    assert model is None
    assert errors


def test_pydantic_model_rejects_unexpected_fields() -> None:
    """Test that Pydantic model rejects unexpected fields."""
    data = load_example("run-metadata-example.json")
    # Add an unexpected field
    data["unexpectedField"] = "should be rejected"

    # JSON Schema validation should catch it
    errors = validate_run_metadata(data)
    assert errors

    # Pydantic model validation should also catch it
    model, model_errors = validate_pydantic_model(data, RunMetadata)
    assert model is None
    assert model_errors


def test_pydantic_model_requires_status() -> None:
    """Test that Pydantic model requires status field."""
    data = load_example("run-metadata-example.json")
    # Remove the status field
    del data["run"]["status"]

    # JSON Schema validation should catch it
    errors = validate_run_metadata(data)
    assert errors

    # Pydantic model validation should also catch it
    model, model_errors = validate_pydantic_model(data, RunMetadata)
    assert model is None
    assert model_errors
