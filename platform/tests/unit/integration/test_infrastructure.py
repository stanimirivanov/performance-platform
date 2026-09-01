"""Unit tests for infrastructure components."""

import asyncio
import time
from unittest.mock import AsyncMock, Mock

import pytest

from perfeng.integration.infrastructure import (
    CircuitBreaker,
    IntervalScheduler,
    ResilientHttpClient,
)
from perfeng.integration.models import RetryConfig


class TestCircuitBreaker:
    def test_initial_state_closed(self):
        cb = CircuitBreaker()
        assert cb.can_execute() is True

    def test_opens_after_threshold(self, monkeypatch):
        cb = CircuitBreaker()
        for _ in range(5):
            cb.record_failure()
        assert cb.can_execute() is False

    def test_half_open_after_timeout(self, monkeypatch):
        cb = CircuitBreaker()
        for _ in range(5):
            cb.record_failure()
        assert cb.can_execute() is False

        # Simulate time passing beyond recovery_timeout
        future_time = time.monotonic() + 31.0
        monkeypatch.setattr(
            "perfeng.integration.infrastructure.circuit_breaker.time.monotonic", lambda: future_time
        )
        assert cb.can_execute() is True

    def test_record_success_resets(self):
        cb = CircuitBreaker()
        for _ in range(5):
            cb.record_failure()
        assert cb.can_execute() is False
        cb.record_success()
        assert cb.can_execute() is True


class TestResilientHttpClient:
    @pytest.mark.asyncio
    async def test_post_success(self):
        mock_client = AsyncMock()
        response = Mock(status_code=200)
        response.raise_for_status = Mock()
        response.json.return_value = {"ok": True}
        mock_client.post.return_value = response

        client = ResilientHttpClient(base_url="http://test", client=mock_client)
        result = await client.post("/path", json={})
        assert result == {"ok": True}
        mock_client.post.assert_awaited_once_with("http://test/path", json={}, timeout=None)

    @pytest.mark.asyncio
    async def test_post_retries_then_succeeds(self):
        mock_client = AsyncMock()
        resp500 = Mock(status_code=500)
        resp500.raise_for_status = Mock()
        resp200 = Mock(status_code=200)
        resp200.raise_for_status = Mock()
        resp200.json.return_value = {"ok": True}
        mock_client.post.side_effect = [resp500, resp200]

        client = ResilientHttpClient(
            base_url="http://test",
            client=mock_client,
            retry=RetryConfig(
                max_attempts=3,
                base_delay=0.01,
                max_delay=0.1,
                exponential_base=2,
                retryable_status_codes=frozenset({500, 502}),
            ),
        )
        result = await client.post("/path", json={})
        assert result == {"ok": True}
        assert mock_client.post.await_count == 2

    @pytest.mark.asyncio
    async def test_post_circuit_open_raises(self):
        cb = CircuitBreaker()
        for _ in range(5):
            cb.record_failure()
        mock_client = AsyncMock()
        client = ResilientHttpClient(
            base_url="http://test",
            client=mock_client,
            circuit_breaker=cb,
        )
        with pytest.raises(RuntimeError, match="Circuit breaker is OPEN"):
            await client.post("/path", json={})

    @pytest.mark.asyncio
    async def test_close_owned_client(self):
        mock_client = AsyncMock()
        client = ResilientHttpClient(base_url="http://test", client=mock_client)
        await client.close()
        mock_client.aclose.assert_awaited_once()
        mock_client.close.assert_not_awaited()  # optional, ensure close not called


class TestIntervalScheduler:
    @pytest.mark.asyncio
    async def test_scheduler_runs_and_stops(self):
        call_count = 0

        async def callback():
            nonlocal call_count
            call_count += 1

        scheduler = IntervalScheduler(interval_seconds=0.01, callback=callback)
        await scheduler.start()
        await asyncio.sleep(0.05)
        await scheduler.stop()
        assert call_count >= 2

    @pytest.mark.asyncio
    async def test_scheduler_start_twice_raises(self):
        async def callback():
            pass

        scheduler = IntervalScheduler(interval_seconds=0.1, callback=callback)
        await scheduler.start()
        with pytest.raises(RuntimeError, match="already running"):
            await scheduler.start()
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_scheduler_handles_callback_exception(self):
        call_count = 0

        async def callback():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("boom")

        scheduler = IntervalScheduler(interval_seconds=0.01, callback=callback)
        await scheduler.start()
        await asyncio.sleep(0.05)
        await scheduler.stop()
        assert call_count >= 3
