"""Generate SQLAlchemy models from the database schema using sqlacodegen.

This script connects to the configured PostgreSQL database and creates
`src/perfeng/storage/models/generated.py` containing declarative models
that reflect the `metadata` schema.

Usage:
    uv run python scripts/generate_sqlalchemy_models.py

The database URL can be overridden with the `SQLACODEGEN_DATABASE_URL` environment variable.
If not set, the `database_sync_url` from the application settings is used.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from perfeng.core.config import settings

# Schema to reflect
TARGET_SCHEMA = "metadata"

# Where to write the generated file
OUTPUT_PATH = (
    Path(__file__).parent.parent / "src" / "perfeng" / "storage" / "models" / "generated.py"
)


def post_process_generated_models(output_path: Path) -> None:
    """Insert `__test__ = False` into any class whose name starts with 'Test'.

    This prevents pytest from attempting to collect SQLAlchemy model classes
    (e.g., TestRuns) as test classes.
    """
    content = output_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    new_lines = []

    for line in lines:
        new_lines.append(line)
        # Detect class definition lines that start with 'class Test'
        stripped = line.lstrip()
        if stripped.startswith("class Test") and stripped.endswith(":"):
            # Determine indentation of the class line
            indent = line[: len(line) - len(stripped)]
            # Add the __test__ attribute inside the class body (4 spaces deeper)
            new_lines.append(f"{indent}    __test__ = False")

    output_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def main() -> int:
    # Prefer explicit env var, then fall back to settings
    db_url = os.environ.get("SQLACODEGEN_DATABASE_URL", settings.database_sync_url)

    # Build sqlacodegen command with schema selection
    cmd = [
        sys.executable,
        "-m",
        "sqlacodegen",
        db_url,
        "--schema",
        TARGET_SCHEMA,
        "--outfile",
        str(OUTPUT_PATH),
        "--generator",
        "declarative",
    ]

    print(f"Generating SQLAlchemy models from {db_url}")
    print(f"Target schema: {TARGET_SCHEMA}")
    print(f"Writing to {OUTPUT_PATH}")

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"Error generating models: {exc}", file=sys.stderr)
        return exc.returncode

    # Post-process the generated file to add __test__ = False
    post_process_generated_models(OUTPUT_PATH)

    print("Model generation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
