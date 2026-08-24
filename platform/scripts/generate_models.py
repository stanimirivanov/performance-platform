"""Generate Pydantic models from JSON schemas.

This script uses datamodel-code-generator to create Python models
from the JSON schemas in the schemas/ directory.

Usage:
    uv run python scripts/generate_models.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from datamodel_code_generator import InputFileType, PythonVersion, generate

# Paths
SCHEMAS_DIR: Final[Path] = Path(__file__).parent.parent.parent / "schemas"
OUTPUT_DIR: Final[Path] = Path(__file__).parent.parent / "src" / "perfeng" / "generated"

# Schema to output mapping
SCHEMA_TO_MODEL: Final[dict[str, str]] = {
    "run-metadata.schema.json": "run_metadata.py",
    "test-result.schema.json": "test_result.py",
    "environment.schema.json": "environment.py",
    "candidate.schema.json": "candidate.py",
}


def generate_models() -> None:
    """Generate Pydantic models from all JSON schemas."""
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for schema_file, model_file in SCHEMA_TO_MODEL.items():
        schema_path = SCHEMAS_DIR / schema_file
        output_path = OUTPUT_DIR / model_file

        if not schema_path.exists():
            print(f"Warning: Schema {schema_file} not found, skipping...")
            continue

        print(f"Generating {model_file} from {schema_file}...")

        generate(
            input_=schema_path,
            input_file_type=InputFileType.JsonSchema,
            output=output_path,
            output_model_type="pydantic_v2.BaseModel",
            target_python_version=PythonVersion.PY_311,
            use_standard_collections=True,
            use_union_operator=True,
            field_constraints=True,
            snake_case_field=True,
            strip_default_none=True,
            apply_default_values_for_required_fields=False,
            use_annotated=True,
            use_field_description=True,
            collapse_root_models=False,
            use_double_quotes=True,
            custom_template_dir=None,
            extra_template_data=None,
        )

        print(f"  Generated: {output_path}")

    print("\nGenerating __init__.py...")
    init_content = '''"""Generated Pydantic models from JSON schemas.

This module is auto-generated. Do not edit manually.
Run `uv run python scripts/generate_models.py` to regenerate.
"""

from .candidate import Candidate
from .environment import Environment
from .run_metadata import RunMetadata
from .test_result import TestResult

__all__ = [
    "Candidate",
    "Environment",
    "RunMetadata",
    "TestResult",
]
'''
    (OUTPUT_DIR / "__init__.py").write_text(init_content)
    print("  Generated: __init__.py")

    print("\nModel generation complete!")


if __name__ == "__main__":
    generate_models()
