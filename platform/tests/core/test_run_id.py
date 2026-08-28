"""Tests for run ID generation."""

from __future__ import annotations

from datetime import datetime

import pytest

from perfeng.utils.run_id import generate_run_id, parse_run_id

pytestmark = pytest.mark.core


def test_generate_run_id_format() -> None:
    """Test that generated run ID has correct format."""
    run_id = generate_run_id(datetime(2024, 1, 15, 14, 30, 22))
    assert run_id.startswith("perf-20240115-143022-")
    assert len(run_id.split("-")) == 4
    assert len(run_id.split("-")[3]) == 8


def test_generate_run_id_unique() -> None:
    """Test that generated run IDs are unique."""
    ids = {generate_run_id() for _ in range(100)}
    assert len(ids) == 100


def test_parse_run_id() -> None:
    """Test parsing timestamp from run ID."""
    run_id = "perf-20240115-143022-ab12cd34"
    ts = parse_run_id(run_id)
    assert ts == datetime(2024, 1, 15, 14, 30, 22)


def test_parse_run_id_invalid() -> None:
    """Test parsing invalid run ID raises error."""
    with pytest.raises(ValueError):
        parse_run_id("invalid-format")
