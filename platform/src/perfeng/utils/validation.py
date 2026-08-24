"""Validation utilities for schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema


def load_schema(schema_name: str) -> dict[str, Any]:
    """Load a JSON schema from the schemas directory.

    Args:
        schema_name: Name of the schema file (e.g., 'run-metadata.schema.json').

    Returns:
        The schema as a dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
    """
    schema_path = Path(__file__).parent.parent.parent.parent.parent / "schemas" / schema_name
    if not schema_path.exists():
        # Fallback to relative path from repository root
        schema_path = Path(__file__).parent.parent.parent.parent / "schemas" / schema_name

    with open(schema_path) as f:
        return json.load(f)


def validate_against_schema(data: dict[str, Any], schema_name: str) -> list[str]:
    """Validate data against a JSON schema.

    Args:
        data: Data to validate.
        schema_name: Name of the schema file.

    Returns:
        List of validation errors (empty if valid).
    """
    schema = load_schema(schema_name)
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    return [f"{' -> '.join(str(p) for p in e.path)}: {e.message}" for e in errors]


def validate_run_metadata(data: dict[str, Any]) -> list[str]:
    """Validate run metadata against its schema.

    Args:
        data: Run metadata to validate.

    Returns:
        List of validation errors (empty if valid).
    """
    return validate_against_schema(data, "run-metadata.schema.json")


def validate_test_result(data: dict[str, Any]) -> list[str]:
    """Validate test result against its schema.

    Args:
        data: Test result to validate.

    Returns:
        List of validation errors (empty if valid).
    """
    return validate_against_schema(data, "test-result.schema.json")
