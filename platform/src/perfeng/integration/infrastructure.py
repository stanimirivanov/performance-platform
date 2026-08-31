"""Cross-cutting infrastructure: resilient HTTP, scheduling, circuit breaker."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import random
import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from perfeng.integration.models import CircuitBreakerConfig, RetryConfig

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


class ResilientHttpClient:
    """httpx wrapper with retry, circuit breaker, and ownership tracking."""

    def __init__(
        self,
        base_url: str,
        client: httpx.AsyncClient | None = None,
        retry: RetryConfig | None = None,
        circuit_breaker: CircuitBreaker | None = None,
        default_timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=default_timeout)
        self._owns_client = client is None
        self._retry = retry or RetryConfig()
        self._circuit = circuit_breaker or CircuitBreaker()

    async def post(
        self,
        url: str,
        json: dict[str, Any],
        timeout: float | None = None,
    ) -> dict[str, Any]:
        if not self._circuit.can_execute():
            raise RuntimeError("Circuit breaker is OPEN")

        full_url = f"{self.base_url}{url}"
        last_exception: Exception | None = None

        for attempt in range(1, self._retry.max_attempts + 1):
            try:
                response = await self._client.post(full_url, json=json, timeout=timeout)

                if (
                    response.status_code in self._retry.retryable_status_codes
                    and attempt < self._retry.max_attempts
                ):
                    delay = self._backoff_delay(attempt)
                    logger.warning(
                        "Retryable HTTP %d on attempt %d/%d for %s, backing off %.2fs",
                        response.status_code,
                        attempt,
                        self._retry.max_attempts,
                        full_url,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue

                response.raise_for_status()
                self._circuit.record_success()
                return response.json()

            except httpx.HTTPStatusError as exc:
                if (
                    exc.response.status_code in self._retry.retryable_status_codes
                    and attempt < self._retry.max_attempts
                ):
                    delay = self._backoff_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                self._circuit.record_failure()
                raise

            except httpx.RequestError as exc:
                last_exception = exc
                if attempt < self._retry.max_attempts:
                    delay = self._backoff_delay(attempt)
                    logger.warning(
                        "Request error on attempt %d/%d for %s: %s, backing off %.2fs",
                        attempt,
                        self._retry.max_attempts,
                        full_url,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    self._circuit.record_failure()
                    raise last_exception

        raise last_exception or RuntimeError("Retry loop exhausted unexpectedly")

    def _backoff_delay(self, attempt: int) -> float:
        delay = min(
            self._retry.base_delay * (self._retry.exponential_base ** (attempt - 1)),
            self._retry.max_delay,
        )
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()


class IntervalScheduler:
    """Robust interval scheduler with graceful stop and error isolation."""

    def __init__(
        self,
        interval_seconds: float,
        callback: Callable[[], Awaitable[None]],
        name: str = "scheduler",
    ):
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        self._interval = interval_seconds
        self._callback = callback
        self._name = name
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task | None = None
        self._logger = logging.getLogger(f"{__name__}.{name}")

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            raise RuntimeError(f"Scheduler '{self._name}' is already running")
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run(), name=f"scheduler-{self._name}")

    async def stop(self) -> None:
        if self._task is None or self._task.done():
            return
        self._stop_event.set()
        try:
            await asyncio.wait_for(self._task, timeout=self._interval + 5.0)
        except TimeoutError:
            self._logger.warning("Scheduler task did not stop gracefully, cancelling")
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        self._task = None

    async def _run(self) -> None:
        self._logger.info("Scheduler '%s' started (interval=%.2fs)", self._name, self._interval)
        while not self._stop_event.is_set():
            try:
                await self._callback()
            except Exception:
                self._logger.exception("Unhandled error in scheduled callback '%s'", self._name)

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self._interval)
            except TimeoutError:
                pass  # Normal interval expiration
        self._logger.info("Scheduler '%s' stopped", self._name)
