from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import httpx
import pytest

from nomba import APIConnectionError, APITimeoutError, RateLimitError, ServerError
from nomba._core import MAX_BACKOFF_SECONDS, backoff_seconds, retry_after_seconds

from .conftest import MockAPI, envelope, make_async_client, make_client

PARENT = {"accountId": "a"}


def server_error() -> httpx.Response:
    return httpx.Response(500, json={"code": "500", "description": "oops"})


def test_get_is_retried_on_5xx(api: MockAPI, sleeps: list[float]) -> None:
    api.add("GET", "/v1/accounts/parent", server_error(), httpx.Response(503), envelope(PARENT))
    with make_client(api, sleeps) as client:
        assert client.accounts.get_parent()["accountId"] == "a"
    assert api.paths().count("GET /v1/accounts/parent") == 3
    assert len(sleeps) == 2
    assert 0.4 <= sleeps[0] <= 0.6
    assert 0.8 <= sleeps[1] <= 1.2


def test_get_gives_up_after_max_retries(api: MockAPI, sleeps: list[float]) -> None:
    api.add("GET", "/v1/accounts/parent", server_error())
    with make_client(api, sleeps, max_retries=3) as client, pytest.raises(ServerError):
        client.accounts.get_parent()
    assert api.paths().count("GET /v1/accounts/parent") == 4
    assert len(sleeps) == 3


def test_max_retries_zero(api: MockAPI, sleeps: list[float]) -> None:
    api.add("GET", "/v1/accounts/parent", server_error())
    with make_client(api, sleeps, max_retries=0) as client, pytest.raises(ServerError):
        client.accounts.get_parent()
    assert api.paths().count("GET /v1/accounts/parent") == 1
    assert sleeps == []


def test_get_429_honours_retry_after(api: MockAPI, sleeps: list[float]) -> None:
    api.add(
        "GET",
        "/v1/accounts/parent",
        httpx.Response(429, headers={"Retry-After": "7"}, json={"code": "429"}),
        envelope(PARENT),
    )
    with make_client(api, sleeps) as client:
        client.accounts.get_parent()
    assert sleeps == [7.0]


def test_get_retries_connection_errors(api: MockAPI, sleeps: list[float]) -> None:
    api.add("GET", "/v1/accounts/parent", httpx.ConnectError("refused"), envelope(PARENT))
    with make_client(api, sleeps) as client:
        assert client.accounts.get_parent()["accountId"] == "a"
    assert len(sleeps) == 1


def test_get_connection_error_after_retries(api: MockAPI, sleeps: list[float]) -> None:
    api.add("GET", "/v1/accounts/parent", httpx.ConnectError("refused"))
    with make_client(api, sleeps) as client, pytest.raises(APIConnectionError) as info:
        client.accounts.get_parent()
    assert not isinstance(info.value, APITimeoutError)
    assert str(info.value) == "Could not connect to Nomba (ConnectError) [GET /v1/accounts/parent]"
    assert info.value.method == "GET"
    assert info.value.path == "/v1/accounts/parent"
    assert isinstance(info.value.__cause__, httpx.ConnectError)
    assert api.paths().count("GET /v1/accounts/parent") == 3


def test_get_timeout(api: MockAPI, sleeps: list[float]) -> None:
    api.add("GET", "/v1/accounts/parent", httpx.ReadTimeout("slow"))
    with make_client(api, sleeps) as client, pytest.raises(APITimeoutError, match="timed out"):
        client.accounts.get_parent()
    assert api.paths().count("GET /v1/accounts/parent") == 3


@pytest.mark.parametrize(
    "failure",
    [server_error(), httpx.Response(429, json={"code": "429"}), httpx.ConnectError("reset"), httpx.ReadTimeout("t")],
    ids=["500", "429", "connect", "timeout"],
)
def test_post_is_never_retried(api: MockAPI, sleeps: list[float], failure: httpx.Response | Exception) -> None:
    api.add("POST", "/v2/transfers/bank", failure)
    params = {"amount": 100, "accountNumber": "0123456789", "accountName": "A", "bankCode": "058"}
    with make_client(api, sleeps) as client, pytest.raises((ServerError, RateLimitError, APIConnectionError)):
        client.transfers.to_bank(params)  # type: ignore[arg-type]
    assert api.paths().count("POST /v2/transfers/bank") == 1
    assert sleeps == []


def test_put_and_delete_not_retried(api: MockAPI, sleeps: list[float]) -> None:
    api.add("PUT", "/v1/accounts/virtual/ref-1", server_error())
    api.add("DELETE", "/v1/accounts/virtual/ref-1", server_error())
    with make_client(api, sleeps) as client:
        with pytest.raises(ServerError):
            client.virtual_accounts.update("ref-1", {"accountName": "x"})
        with pytest.raises(ServerError):
            client.virtual_accounts.expire("ref-1")
    assert api.paths().count("PUT /v1/accounts/virtual/ref-1") == 1
    assert api.paths().count("DELETE /v1/accounts/virtual/ref-1") == 1
    assert sleeps == []


async def test_async_get_retry_and_post_no_retry(api: MockAPI, sleeps: list[float]) -> None:
    api.add("GET", "/v1/accounts/parent", server_error(), envelope(PARENT))
    api.add("POST", "/v1/checkout/refund", server_error())
    async with make_async_client(api, sleeps) as client:
        assert (await client.accounts.get_parent())["accountId"] == "a"
        with pytest.raises(ServerError):
            await client.checkout.refund({"transactionId": "t"})
    assert api.paths().count("POST /v1/checkout/refund") == 1
    assert len(sleeps) == 1


async def test_async_connection_error(api: MockAPI, sleeps: list[float]) -> None:
    api.add("GET", "/v1/accounts/parent", httpx.ConnectTimeout("slow"))
    async with make_async_client(api, sleeps) as client:
        with pytest.raises(APITimeoutError):
            await client.accounts.get_parent()
    assert len(sleeps) == 2


def test_backoff_grows_and_caps() -> None:
    for attempt, base in enumerate([0.5, 1, 2, 4, 8, 8, 8]):
        delay = backoff_seconds(attempt)
        assert base * 0.8 <= delay <= min(base * 1.2, MAX_BACKOFF_SECONDS)


def test_retry_after_parsing() -> None:
    assert retry_after_seconds(None) is None
    assert retry_after_seconds(httpx.Response(429)) is None
    assert retry_after_seconds(httpx.Response(429, headers={"Retry-After": "garbage"})) is None
    future = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=30), usegmt=True)
    after = retry_after_seconds(httpx.Response(429, headers={"Retry-After": future}))
    assert after is not None
    assert 25 <= after <= 31
    past = format_datetime(datetime.now(timezone.utc) - timedelta(seconds=30), usegmt=True)
    assert retry_after_seconds(httpx.Response(429, headers={"Retry-After": past})) == 0.0
    naive = "Wed, 21 Oct 2015 07:28:00 -0000"
    assert retry_after_seconds(httpx.Response(429, headers={"Retry-After": naive})) == 0.0


def test_retry_after_is_capped() -> None:
    response = httpx.Response(429, headers={"Retry-After": "3600"})
    assert backoff_seconds(0, response) == 60.0
