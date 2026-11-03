"""The ``timeout`` option bounds a whole attempt, not just each httpx phase."""

from __future__ import annotations

import gzip
import json
from collections.abc import AsyncIterator, Iterator

import httpx
import pytest

from nomba import APITimeoutError

from .conftest import MockAPI, body_of, make_async_client, make_client


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class SlowStream(httpx.SyncByteStream, httpx.AsyncByteStream):
    """Yields ``chunks``, advancing the fake clock by ``step`` seconds before each."""

    def __init__(self, chunks: list[bytes], clock: FakeClock, step: float) -> None:
        self.chunks = chunks
        self.clock = clock
        self.step = step
        self.closed = False

    def __iter__(self) -> Iterator[bytes]:
        for chunk in self.chunks:
            self.clock.now += self.step
            yield chunk

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for chunk in self.chunks:
            self.clock.now += self.step
            yield chunk

    def close(self) -> None:
        self.closed = True

    async def aclose(self) -> None:
        self.closed = True


def envelope_bytes(data: object) -> bytes:
    return json.dumps({"code": "00", "description": "ok", "data": data}).encode()


def split(raw: bytes, n: int) -> list[bytes]:
    size = max(1, len(raw) // n + 1)
    return [raw[i : i + size] for i in range(0, len(raw), size)]


def slow_response(clock: FakeClock, step: float, data: object = None, *, headers_delay: float = 0.0) -> object:
    streams: list[SlowStream] = []

    def handler(request: httpx.Request) -> httpx.Response:
        clock.now += headers_delay
        stream = SlowStream(split(envelope_bytes(data or {"ok": True}), 3), clock, step)
        streams.append(stream)
        return httpx.Response(200, headers={"content-type": "application/json"}, stream=stream)

    handler.streams = streams  # type: ignore[attr-defined]
    return handler


def test_slow_body_on_post_raises_timeout_once(api: MockAPI) -> None:
    clock = FakeClock()
    handler = slow_response(clock, step=20.0)  # 3 chunks x 20 s > 30 s
    api.add("POST", "/v2/transfers/bank", handler)  # type: ignore[arg-type]
    with make_client(api) as client:
        client._monotonic = clock
        with pytest.raises(APITimeoutError, match="timed out") as info:
            client.transfers.to_bank({"amount": 1, "accountNumber": "1", "accountName": "A", "bankCode": "058"})
    assert api.paths().count("POST /v2/transfers/bank") == 1
    assert info.value.reference is not None
    assert info.value.reference.value == body_of(api.last())["merchantTxRef"]
    assert handler.streams[0].closed  # type: ignore[attr-defined]


def test_slow_body_on_get_is_retried_then_times_out(api: MockAPI, sleeps: list[float]) -> None:
    clock = FakeClock()
    api.add("GET", "/v1/accounts/parent", slow_response(clock, step=11.0))  # type: ignore[arg-type]
    with make_client(api, sleeps) as client:
        client._monotonic = clock
        with pytest.raises(APITimeoutError):
            client.accounts.get_parent()
    assert api.paths().count("GET /v1/accounts/parent") == 3
    assert len(sleeps) == 2


def test_slow_headers_count_towards_the_deadline(api: MockAPI) -> None:
    clock = FakeClock()
    api.add("POST", "/v1/checkout/refund", slow_response(clock, step=0.0, headers_delay=31.0))  # type: ignore[arg-type]
    with make_client(api) as client:
        client._monotonic = clock
        with pytest.raises(APITimeoutError):
            client.checkout.refund({"transactionId": "t"})


def test_streamed_body_within_deadline_is_parsed(api: MockAPI) -> None:
    clock = FakeClock()
    api.add("GET", "/v1/accounts/parent", slow_response(clock, step=9.0, data={"accountId": "abc"}))  # type: ignore[arg-type]
    with make_client(api, timeout=30) as client:
        client._monotonic = clock
        assert client.accounts.get_parent()["accountId"] == "abc"


def test_custom_timeout_is_the_total_budget(api: MockAPI) -> None:
    clock = FakeClock()
    api.add("GET", "/v1/accounts/parent", slow_response(clock, step=4.0))  # type: ignore[arg-type]
    with make_client(api, timeout=10, max_retries=0) as client:
        client._monotonic = clock
        with pytest.raises(APITimeoutError):
            client.accounts.get_parent()  # 12 s > 10 s


def test_gzip_streamed_body_is_decoded(api: MockAPI) -> None:
    raw = gzip.compress(envelope_bytes({"accountId": "zipped"}))

    def handler(request: httpx.Request) -> httpx.Response:
        stream = SlowStream(split(raw, 4), FakeClock(), 0.0)
        return httpx.Response(200, headers={"content-encoding": "gzip"}, stream=stream)

    api.add("GET", "/v1/accounts/parent", handler)
    with make_client(api) as client:
        assert client.accounts.get_parent()["accountId"] == "zipped"


async def test_async_slow_body_times_out(api: MockAPI) -> None:
    clock = FakeClock()
    api.add("POST", "/v2/bill/topup", slow_response(clock, step=20.0))  # type: ignore[arg-type]
    async with make_async_client(api) as client:
        client._monotonic = clock
        with pytest.raises(APITimeoutError) as info:
            await client.bills.buy_airtime({"amount": 1, "phoneNumber": "080", "network": "MTN"})
    assert info.value.reference is not None
    assert api.paths().count("POST /v2/bill/topup") == 1


async def test_async_streamed_body_within_deadline(api: MockAPI) -> None:
    clock = FakeClock()
    api.add("GET", "/v1/accounts/parent", slow_response(clock, step=5.0, data={"accountId": "async"}))  # type: ignore[arg-type]
    async with make_async_client(api) as client:
        client._monotonic = clock
        assert (await client.accounts.get_parent())["accountId"] == "async"


async def test_async_slow_headers(api: MockAPI) -> None:
    clock = FakeClock()
    api.add("GET", "/v1/accounts/parent", slow_response(clock, step=0.0, headers_delay=40.0))  # type: ignore[arg-type]
    async with make_async_client(api, max_retries=0) as client:
        client._monotonic = clock
        with pytest.raises(APITimeoutError):
            await client.accounts.get_parent()
