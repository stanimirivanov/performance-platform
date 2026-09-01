"""Simple in-memory circuit breaker with correct half-open probe handling."""

from __future__ import annotations

import logging
import time

from perfeng.integration.models import CircuitBreakerConfig

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Simple in-memory circuit breaker.

    Implements the standard closed -> open -> half-open -> closed state machine.
    When the circuit transitions from open to half-open, exactly one probe
    request is allowed; all other requests are rejected until that probe
    completes (success or failure). This prevents concurrent requests from
    flooding a recovering downstream service.
    """

    def __init__(self, config: CircuitBreakerConfig | None = None):
        self._config = config or CircuitBreakerConfig()
        self._failures = 0
        self._last_failure_time: float | None = None
        self._state = "closed"  # closed -> open -> half-open
        self._probe_in_flight = False

    def record_success(self) -> None:
        """Reset the circuit after a successful probe or request."""
        self._failures = 0
        self._state = "closed"
        self._probe_in_flight = False

    def record_failure(self) -> None:
        """Record a failure, transitioning to open if threshold reached.

        If the failure occurs during a half-open probe, the circuit immediately
        re-opens, regardless of the configured failure threshold.
        """
        self._failures += 1
        self._last_failure_time = time.monotonic()

        if self._state == "half-open":
            # The probe failed; open the circuit again immediately.
            self._state = "open"
            self._probe_in_flight = False
            logger.warning("Circuit breaker re-opened after failed half-open probe")
            return

        if self._failures >= self._config.failure_threshold:
            self._state = "open"
            self._probe_in_flight = False
            logger.warning("Circuit breaker opened after %d failures", self._failures)

    def can_execute(self) -> bool:
        """Return True if a request may be executed, respecting the state machine."""
        if self._state == "closed":
            return True

        if self._state == "open":
            elapsed = time.monotonic() - (self._last_failure_time or 0)
            if elapsed > self._config.recovery_timeout:
                logger.info("Circuit breaker entering half-open state")
                self._state = "half-open"
                self._probe_in_flight = True
                return True
            return False

        # state == "half-open": only the probe that transitioned is allowed.
        # Since `_probe_in_flight` is True, all other calls get False.
        return False
