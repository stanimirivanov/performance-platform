"""Simple in-memory circuit breaker."""

from __future__ import annotations

import logging
import time

from perfeng.integration.models import CircuitBreakerConfig

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Simple in-memory circuit breaker."""

    def __init__(self, config: CircuitBreakerConfig | None = None):
        self._config = config or CircuitBreakerConfig()
        self._failures = 0
        self._last_failure_time: float | None = None
        self._state = "closed"  # closed -> open -> half-open

    def record_success(self) -> None:
        self._failures = 0
        self._state = "closed"

    def record_failure(self) -> None:
        self._failures += 1
        self._last_failure_time = time.monotonic()
        if self._failures >= self._config.failure_threshold:
            self._state = "open"
            logger.warning("Circuit breaker opened after %d failures", self._failures)

    def can_execute(self) -> bool:
        if self._state == "closed":
            return True
        if self._state == "open":
            elapsed = time.monotonic() - (self._last_failure_time or 0)
            if elapsed > self._config.recovery_timeout:
                logger.info("Circuit breaker entering half-open state")
                self._state = "half-open"
                return True
            return False
        # half-open: allow one probe
        return True
