"""Value objects and configuration DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Normalized resource snapshot."""

    resource_type: str
    value_current: float
    unit: str
    test_phase: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RetryConfig:
    """Exponential backoff configuration."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    retryable_status_codes: frozenset[int] = frozenset({408, 429, 500, 502, 503, 504})


@dataclass(frozen=True, slots=True)
class CircuitBreakerConfig:
    """Circuit breaker settings."""

    failure_threshold: int = 5
    recovery_timeout: float = 30.0
