"""Tests for k6 result normalizer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from perfeng.normalizer import K6Normalizer


def load_json(name: str) -> dict[str, Any]:
    """Load a JSON file from examples."""
    path = Path(__file__).parent.parent.parent.parent / "examples" / "k6" / name
    with open(path) as f:
        return cast(dict[str, Any], json.load(f))


def test_normalize_empty_output() -> None:
    """Test that empty k6 output produces empty results."""
    normalizer = K6Normalizer()
    results = normalizer.normalize({}, "perf-test-123")
    assert results == []


def test_normalize_http_req_duration() -> None:
    """Test that http_req_duration is normalized correctly."""
    normalizer = K6Normalizer()
    k6_output = load_json("sample-k6-output.json")
    run_id = "perf-20240115-143022-ab12cd34"

    results = normalizer.normalize(k6_output, run_id, ["http_req_duration"])

    assert len(results) == 1
    result = results[0]

    assert result["schemaVersion"] == 1
    assert result["runId"] == run_id
    assert result["metric"]["name"] == "api.http.duration"
    assert result["metric"]["direction"] == "lower-is-better"
    assert result["metric"]["type"] == "latency"
    assert result["metric"]["unit"] == "ms"

    dist = result["distribution"]
    assert dist["samples"] == 1000
    assert dist["mean"] == 234.56
    assert dist["median"] == 221.0
    assert dist["p90"] == 312.0
    assert dist["p95"] == 345.0
    assert dist["p99"] == 412.0
    assert dist["stddev"] == 45.2
    assert dist["min"] == 150.0
    assert dist["max"] == 500.0
    assert "cv" in dist


def test_normalize_http_req_failed() -> None:
    """Test that http_req_failed is normalized correctly."""
    normalizer = K6Normalizer()
    k6_output = load_json("sample-k6-output.json")
    run_id = "perf-20240115-143022-ab12cd34"

    results = normalizer.normalize(k6_output, run_id, ["http_req_failed"])

    assert len(results) == 1
    result = results[0]

    assert result["metric"]["name"] == "api.http.error_rate"
    assert result["metric"]["direction"] == "lower-is-better"
    assert result["metric"]["type"] == "error_rate"
    assert result["metric"]["unit"] == "percent"


def test_normalize_http_reqs() -> None:
    """Test that http_reqs is normalized correctly."""
    normalizer = K6Normalizer()
    k6_output = load_json("sample-k6-output.json")
    run_id = "perf-20240115-143022-ab12cd34"

    results = normalizer.normalize(k6_output, run_id, ["http_reqs"])

    assert len(results) == 1
    result = results[0]

    assert result["metric"]["name"] == "api.http.throughput"
    assert result["metric"]["direction"] == "higher-is-better"
    assert result["metric"]["type"] == "throughput"
    assert result["metric"]["unit"] == "count"


def test_normalize_checkout_duration() -> None:
    """Test that checkout_duration is normalized correctly."""
    normalizer = K6Normalizer()
    k6_output = load_json("sample-k6-output.json")
    run_id = "perf-20240115-143022-ab12cd34"

    results = normalizer.normalize(k6_output, run_id, ["checkout_duration"])

    assert len(results) == 1
    result = results[0]

    assert result["metric"]["name"] == "biz.checkout.duration"
    assert result["metric"]["direction"] == "lower-is-better"
    assert result["metric"]["type"] == "latency"
    assert result["metric"]["unit"] == "ms"

    dist = result["distribution"]
    assert dist["samples"] == 500
    assert dist["mean"] == 310.25
    assert dist["p95"] == 415.0


def test_normalize_all_metrics() -> None:
    """Test that all metrics are normalized."""
    normalizer = K6Normalizer()
    k6_output = load_json("sample-k6-output.json")
    run_id = "perf-20240115-143022-ab12cd34"

    results = normalizer.normalize(k6_output, run_id)

    # Should have 4 metrics (http_req_duration, http_req_failed, http_reqs, checkout_duration)
    assert len(results) == 4

    # Check all metric names
    metric_names = [r["metric"]["name"] for r in results]
    assert "api.http.duration" in metric_names
    assert "api.http.error_rate" in metric_names
    assert "api.http.throughput" in metric_names
    assert "biz.checkout.duration" in metric_names


def test_normalize_with_filter() -> None:
    """Test that metric filter works."""
    normalizer = K6Normalizer()
    k6_output = load_json("sample-k6-output.json")
    run_id = "perf-20240115-143022-ab12cd34"

    results = normalizer.normalize(k6_output, run_id, ["http_req_duration"])

    assert len(results) == 1
    assert results[0]["metric"]["name"] == "api.http.duration"


def test_normalize_direction_determination() -> None:
    """Test direction determination."""
    normalizer = K6Normalizer()

    # Higher-is-better metrics
    assert normalizer._determine_direction("http_reqs", "counter") == "higher-is-better"
    assert (
        normalizer._determine_direction("successful_transactions", "counter") == "higher-is-better"
    )

    # Lower-is-better metrics
    assert normalizer._determine_direction("http_req_duration", "trend") == "lower-is-better"
    assert normalizer._determine_direction("http_req_failed", "rate") == "lower-is-better"

    # Default based on type
    assert normalizer._determine_direction("unknown_trend", "trend") == "lower-is-better"
    assert normalizer._determine_direction("unknown_counter", "counter") == "higher-is-better"
    assert normalizer._determine_direction("unknown_rate", "rate") == "lower-is-better"
