"""Generate SQLAlchemy models from the database schema using sqlacodegen.

This script connects to the configured PostgreSQL database and creates
`src/perfeng/storage/generated_models.py` containing declarative models
that reflect the `metadata` schema.

Usage:
    uv run python scripts/generate_sqlalchemy_models.py

The database URL can be overridden with the `SQLACODEGEN_DATABASE_URL` environment variable.
Use a synchronous PostgreSQL driver (e.g., `postgresql+psycopg2://`).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Default database URL – must use a sync driver
DEFAULT_DATABASE_URL = "postgresql+psycopg2://test_user:test_password@localhost:5432/metadata"

# Schema to reflect
TARGET_SCHEMA = "metadata"

# Where to write the generated file
OUTPUT_PATH = Path(__file__).parent.parent / "src" / "perfeng" / "storage" / "generated_models.py"


def main() -> int:
    db_url = os.environ.get("SQLACODEGEN_DATABASE_URL", DEFAULT_DATABASE_URL)

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

    print("Model generation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
