"""Validation utilities for schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypeVar, cast

import jsonschema
from jsonschema import FormatChecker
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def load_schema(schema_name: str) -> dict[str, Any]:
    """Load a JSON schema from the schemas directory.

    Args:
        schema_name: Name of the schema file (e.g., 'run-metadata.schema.json').

    Returns:
        The schema as a dictionary.
    """
    schema_path = Path(__file__).parent.parent.parent.parent.parent / "schemas" / schema_name

    if not schema_path.exists():
        schema_path = Path(__file__).parent.parent.parent.parent / "schemas" / schema_name

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_name}")

    with open(schema_path) as f:
        return cast(dict[str, Any], json.load(f))


def validate_against_schema(data: dict[str, Any], schema_name: str) -> list[str]:
    """Validate data against a JSON schema.

    Args:
        data: Data to validate.
        schema_name: Name of the schema file.

    Returns:
        List of validation errors (empty if valid).
    """
    schema = load_schema(schema_name)

    # Enable format checking for date-time, uri, etc.
    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )

    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    return [f"{' -> '.join(str(p) for p in e.path)}: {e.message}" for e in errors]


def validate_pydantic_model(
    data: dict[str, Any], model_class: type[T]
) -> tuple[T | None, list[str]]:
    """Validate data using a Pydantic model.

    Args:
        data: Data to validate.
        model_class: Pydantic model class to validate against.

    Returns:
        Tuple of (validated model or None, list of validation errors).
    """
    try:
        model = model_class.model_validate(data)
        return model, []
    except ValidationError as e:
        errors = [f"{' -> '.join(str(p) for p in err['loc'])}: {err['msg']}" for err in e.errors()]
        return None, errors


def validate_run_metadata(data: dict[str, Any]) -> list[str]:
    """Validate run metadata against its JSON schema.

    Args:
        data: Run metadata to validate.

    Returns:
        List of validation errors (empty if valid).
    """
    return validate_against_schema(data, "run-metadata.schema.json")


def validate_test_result(data: dict[str, Any]) -> list[str]:
    """Validate test result against its JSON schema.

    Args:
        data: Test result to validate.

    Returns:
        List of validation errors (empty if valid).
    """
    return validate_against_schema(data, "test-result.schema.json")
