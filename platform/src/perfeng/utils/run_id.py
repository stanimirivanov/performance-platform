"""Run ID generation utilities."""

from __future__ import annotations

import uuid
from datetime import datetime


def generate_run_id(timestamp: datetime | None = None) -> str:
    """Generate a unique performance run ID.

    Format: perf-YYYYMMDD-HHMMSS-UUID4

    Args:
        timestamp: Optional timestamp. Defaults to now.

    Returns:
        A unique run ID string.

    Examples:
        >>> generate_run_id(datetime(2024, 1, 15, 14, 30, 22))
        'perf-20240115-143022-12345678'
    """
    ts = timestamp or datetime.now()
    uuid_part = str(uuid.uuid4())[:8]
    return f"perf-{ts.strftime('%Y%m%d')}-{ts.strftime('%H%M%S')}-{uuid_part}"


def parse_run_id(run_id: str) -> datetime:
    """Parse the timestamp from a run ID.

    Args:
        run_id: Run ID string.

    Returns:
        Datetime parsed from the run ID.

    Raises:
        ValueError: If the run ID format is invalid.
    """
    parts = run_id.split("-")
    if len(parts) != 4 or parts[0] != "perf":
        raise ValueError(f"Invalid run ID format: {run_id}")

    try:
        return datetime.strptime(f"{parts[1]}-{parts[2]}", "%Y%m%d-%H%M%S")
    except ValueError as e:
        raise ValueError(f"Invalid run ID timestamp: {run_id}") from e
