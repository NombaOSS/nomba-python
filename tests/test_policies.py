"""Request policy, sub-account paths, token-endpoint error bodies and the lock-free token fast path."""

from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from nomba import AuthenticationError, InMemoryTokenStore, NotFoundError, ServerError, Token, ValidationError
from nomba._core import Request, sub_account_path

from .conftest import MockAPI, envelope, make_async_client, make_client

BALANCE = {"amount": "1.0", "currency": "NGN", "timeCreated": "2026-01-01T00:00:00Z"}


@pytest.mark.parametrize(("method", "retryable"), [("GET", True), ("POST", False), ("PUT", False), ("DELETE", False)])
def test_request_retry_policy_defaults_from_method(method: str, retryable: bool) -> None:
    req: Request[None] = Request(method, "/x")
    assert req.retryable is retryable
    assert req.retry_on_401 is True
    assert req.authenticated is True
    assert req.auth_endpoint is False


def test_request_policy_can_be_overridden() -> None:
    req: Request[None] = Request("POST", "/x", retryable=True, retry_on_401=False, authenticated=False)
    assert (req.retryable, req.retry_on_401, req.authenticated) == (True, False, False)


@pytest.mark.parametrize(
    ("template", "sub", "expected"),
    [
        ("/v1/accounts{sub}/balance", None, "/v1/accounts/balance"),
        ("/v1/accounts{sub}/balance", "sub-1", "/v1/accounts/sub-1/balance"),
        ("/v2/transfers/bank{sub}", None, "/v2/transfers/bank"),
        ("/v2/transfers/bank{sub}", "a b", "/v2/transfers/bank/a%20b"),
        ("/v1/transactions/accounts{sub}/single", "s", "/v1/transactions/accounts/s/single"),
    ],
)
def test_sub_account_path(template: str, sub: str | None, expected: str) -> None:
    assert sub_account_path(template, sub) == expected


@pytest.mark.parametrize("bad", ["", ".", "..", "a/b"])
def test_sub_account_path_validates(bad: str) -> None:
    with pytest.raises(ValidationError):
        sub_account_path("/v2/bill/topup{sub}", bad)


def test_token_issue_error_body_has_no_data(api: MockAPI) -> None:
    api.add(
        "POST",
        "/v1/auth/token/issue",
        httpx.Response(400, json={"code": "400", "description": "bad", "data": {"access_token": "leak"}}),
    )
    with make_client(api) as client, pytest.raises(AuthenticationError) as info:
        client.accounts.get_balance()
    assert info.value.body == {"code": "400", "description": "bad"}
    assert "leak" not in repr(info.value.__dict__)


def test_token_issue_2xx_failure_body_has_no_data(api: MockAPI) -> None:
    api.add("POST", "/v1/auth/token/issue", envelope({"refresh_token": "leak"}, code="401", description="nope"))
    with make_client(api) as client, pytest.raises(AuthenticationError) as info:
        client.accounts.get_balance()
    assert "data" not in info.value.body


def test_revoke_error_body_has_no_data(api: MockAPI) -> None:
    store = InMemoryTokenStore()
    store.set(Token("t", "r", datetime.now(timezone.utc) + timedelta(minutes=20)))
    api.add("POST", "/v1/auth/token/revoke", httpx.Response(500, json={"code": "500", "data": {"access_token": "t"}}))
    with make_client(api, token_store=store) as client, pytest.raises(ServerError) as info:
        client.auth.revoke()
    assert info.value.body == {"code": "500"}


def test_api_error_body_keeps_data(api: MockAPI) -> None:
    api.add("GET", "/v1/accounts/parent", httpx.Response(404, json={"code": "404", "data": {"hint": "x"}}))
    with make_client(api) as client, pytest.raises(NotFoundError) as info:
        client.accounts.get_parent()
    assert info.value.body == {"code": "404", "data": {"hint": "x"}}


def _valid_store() -> InMemoryTokenStore:
    store = InMemoryTokenStore()
    store.set(Token("cached", "r", datetime.now(timezone.utc) + timedelta(minutes=20)))
    return store


def test_valid_cached_token_skips_the_lock(api: MockAPI) -> None:
    api.add("GET", "/v1/accounts/balance", envelope(BALANCE))
    with make_client(api, token_store=_valid_store()) as client:
        client._token_lock.acquire()
        try:
            worker = threading.Thread(target=client.accounts.get_balance, daemon=True)
            worker.start()
            worker.join(timeout=5)
            assert not worker.is_alive()
        finally:
            client._token_lock.release()
    assert api.last().headers["authorization"] == "Bearer cached"


async def test_async_valid_cached_token_skips_the_lock(api: MockAPI) -> None:
    api.add("GET", "/v1/accounts/balance", envelope(BALANCE))
    async with make_async_client(api, token_store=_valid_store()) as client, client._lock():
        await asyncio.wait_for(client.accounts.get_balance(), timeout=5)
    assert api.last().headers["authorization"] == "Bearer cached"


class YieldingStore:
    """An async store that yields to the event loop, so concurrent callers interleave."""

    def __init__(self) -> None:
        self.token: Token | None = None

    async def get(self) -> Token | None:
        await asyncio.sleep(0)
        return self.token

    async def set(self, token: Token | None) -> None:
        await asyncio.sleep(0)
        self.token = token


async def test_async_waiters_recheck_inside_the_lock(api: MockAPI) -> None:
    api.add("GET", "/v1/accounts/balance", envelope(BALANCE))
    async with make_async_client(api, token_store=YieldingStore()) as client:
        await asyncio.gather(*(client.accounts.get_balance() for _ in range(5)))
    assert api.paths().count("POST /v1/auth/token/issue") == 1
    assert api.paths().count("GET /v1/accounts/balance") == 5
