"""Generate Pydantic models from JSON schemas.

This script uses datamodel-code-generator to create Python models
from the JSON schemas in the schemas/ directory.

Usage:
    uv run python scripts/generate_models.py
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Final

from datamodel_code_generator import InputFileType, generate
from datamodel_code_generator.enums import DataModelType
from datamodel_code_generator.format import Formatter

# Suppress FutureWarning from datamodel_code_generator
warnings.filterwarnings(
    "ignore",
    message="The default external formatters",
    category=FutureWarning,
)

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
            output_model_type=DataModelType.PydanticV2BaseModel,
            use_standard_collections=True,
            use_union_operator=True,
            field_constraints=True,
            snake_case_field=False,
            strip_default_none=True,
            use_annotated=True,
            use_field_description=True,
            use_double_quotes=True,
            collapse_root_models=False,
            formatters=[Formatter.BUILTIN],
        )

        print(f"  Generated: {output_path}")

    # Generate __init__.py with correct class names
    print("\nGenerating __init__.py...")
    init_content = '''"""Generated Pydantic models from JSON schemas.

This module is auto-generated. Do not edit manually.
Run `uv run python scripts/generate_models.py` to regenerate.
"""

from .candidate import CandidateSpecification
from .environment import EnvironmentSpecification
from .run_metadata import PerformanceRunMetadata
from .test_result import NormalizedTestResult

# Type aliases for convenience
Candidate = CandidateSpecification
Environment = EnvironmentSpecification
RunMetadata = PerformanceRunMetadata
TestResult = NormalizedTestResult

__all__ = [
    "CandidateSpecification",
    "EnvironmentSpecification",
    "PerformanceRunMetadata",
    "NormalizedTestResult",
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
