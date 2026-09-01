"""Resilient HTTP client with retry and circuit breaker."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from perfeng.integration.infrastructure.circuit_breaker import CircuitBreaker
from perfeng.integration.infrastructure.exceptions import RetryableRequestError
from perfeng.integration.models import RetryConfig

logger = logging.getLogger(__name__)


class ResilientHttpClient:
    """httpx wrapper with tenacity-based retry, circuit breaker, and ownership tracking."""

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

        retryer = AsyncRetrying(
            stop=stop_after_attempt(self._retry.max_attempts),
            wait=wait_exponential_jitter(
                initial=self._retry.base_delay,
                max=self._retry.max_delay,
                exp_base=self._retry.exponential_base,
            ),
            retry=retry_if_exception_type(RetryableRequestError),
            reraise=True,
        )

        try:
            async for attempt in retryer:
                with attempt:
                    try:
                        response = await self._client.post(full_url, json=json, timeout=timeout)

                        if response.status_code in self._retry.retryable_status_codes:
                            self._circuit.record_failure()
                            raise RetryableRequestError(f"Retryable HTTP {response.status_code}")

                        response.raise_for_status()
                        self._circuit.record_success()
                        return response.json()

                    except httpx.RequestError as exc:
                        self._circuit.record_failure()
                        raise RetryableRequestError(str(exc)) from exc

                    except httpx.HTTPStatusError:
                        self._circuit.record_failure()
                        raise  # non-retryable, let it propagate

        except RetryableRequestError as exc:
            logger.error("Retries exhausted for %s: %s", full_url, exc)
            raise

        raise RuntimeError("Retry loop exited unexpectedly")

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
        else:
            await self.close()
