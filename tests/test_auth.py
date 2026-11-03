from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import pytest

from nomba import AuthenticationError, InMemoryTokenStore, ServerError, Token
from nomba._core import token_decision
from nomba.tokens import parse_timestamp, token_from_response

from .conftest import ACCOUNT_ID, CLIENT_ID, CLIENT_SECRET, MockAPI, body_of, envelope, make_async_client, make_client

BALANCE = {"amount": "10.0", "currency": "NGN", "timeCreated": "2026-01-01T00:00:00Z"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_first_call_issues_token_then_reuses_it(api: MockAPI) -> None:
    api.add("GET", "/v1/accounts/balance", envelope(BALANCE))
    with make_client(api) as client:
        client.accounts.get_balance()
        client.accounts.get_balance()
    assert api.paths() == [
        "POST /v1/auth/token/issue",
        "GET /v1/accounts/balance",
        "GET /v1/accounts/balance",
    ]
    issue = api.requests[0]
    assert issue.headers["accountId"] == ACCOUNT_ID
    assert "authorization" not in issue.headers
    assert body_of(issue) == {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    call = api.requests[1]
    assert call.headers["authorization"] == "Bearer access-1"
    assert call.headers["accountid"] == ACCOUNT_ID
    assert call.headers["accept"] == "application/json"
    assert call.headers["content-type"] == "application/json"
    assert call.headers["user-agent"].startswith("nomba-python/0.1.1 python/")
    assert call.extensions["timeout"]["read"] == 30.0


def test_timeout_option_is_applied(api: MockAPI) -> None:
    api.add("GET", "/v1/accounts/balance", envelope(BALANCE))
    with make_client(api, timeout=5) as client:
        client.accounts.get_balance()
    assert api.last().extensions["timeout"] == {"connect": 5.0, "read": 5.0, "write": 5.0, "pool": 5.0}


def test_refreshes_within_five_minutes_of_expiry(api: MockAPI) -> None:
    store = InMemoryTokenStore()
    store.set(Token("old-access", "old-refresh", _now() + timedelta(minutes=4)))
    api.add("GET", "/v1/accounts/balance", envelope(BALANCE))
    with make_client(api, token_store=store) as client:
        client.accounts.get_balance()
    assert api.paths()[0] == "POST /v1/auth/token/refresh"
    assert body_of(api.requests[0]) == {"grant_type": "refresh_token", "refresh_token": "old-refresh"}
    assert api.requests[1].headers["authorization"] == "Bearer access-1"
    token = store.get()
    assert token is not None
    assert token.access_token == "access-1"


def test_valid_token_is_not_refreshed(api: MockAPI) -> None:
    store = InMemoryTokenStore()
    store.set(Token("cached", "r", _now() + timedelta(minutes=20)))
    api.add("GET", "/v1/accounts/balance", envelope(BALANCE))
    with make_client(api, token_store=store) as client:
        client.accounts.get_balance()
    assert api.paths() == ["GET /v1/accounts/balance"]
    assert api.requests[0].headers["authorization"] == "Bearer cached"


def test_refresh_4xx_falls_back_to_issue(api: MockAPI) -> None:
    store = InMemoryTokenStore()
    store.set(Token("old", "bad-refresh", _now() - timedelta(minutes=1)))
    api.add("POST", "/v1/auth/token/refresh", envelope(None, code="400", description="invalid", status=400))
    api.add("GET", "/v1/accounts/balance", envelope(BALANCE))
    with make_client(api, token_store=store) as client:
        client.accounts.get_balance()
    assert api.paths() == [
        "POST /v1/auth/token/refresh",
        "POST /v1/auth/token/issue",
        "GET /v1/accounts/balance",
    ]


def test_refresh_non_success_code_falls_back_to_issue(api: MockAPI) -> None:
    store = InMemoryTokenStore()
    store.set(Token("old", "bad-refresh", _now() + timedelta(minutes=1)))
    api.add("POST", "/v1/auth/token/refresh", envelope(None, code="401", description="expired"))
    api.add("GET", "/v1/accounts/balance", envelope(BALANCE))
    with make_client(api, token_store=store) as client:
        client.accounts.get_balance()
    assert api.paths()[:2] == ["POST /v1/auth/token/refresh", "POST /v1/auth/token/issue"]


def test_refresh_outage_keeps_unexpired_token(api: MockAPI) -> None:
    store = InMemoryTokenStore()
    store.set(Token("still-good", "r", _now() + timedelta(minutes=2)))
    api.add("POST", "/v1/auth/token/refresh", httpx.Response(503, json={"code": "503", "description": "down"}))
    api.add("GET", "/v1/accounts/balance", envelope(BALANCE))
    with make_client(api, token_store=store, max_retries=0) as client:
        client.accounts.get_balance()
    assert api.last().headers["authorization"] == "Bearer still-good"


def test_refresh_connection_error_keeps_unexpired_token(api: MockAPI) -> None:
    store = InMemoryTokenStore()
    store.set(Token("still-good", "r", _now() + timedelta(minutes=2)))
    api.add("POST", "/v1/auth/token/refresh", httpx.ConnectError("boom"))
    api.add("GET", "/v1/accounts/balance", envelope(BALANCE))
    with make_client(api, token_store=store, max_retries=0) as client:
        client.accounts.get_balance()
    assert api.last().headers["authorization"] == "Bearer still-good"


def test_refresh_connection_error_with_expired_token_issues(api: MockAPI) -> None:
    store = InMemoryTokenStore()
    store.set(Token("expired", "r", _now() - timedelta(minutes=2)))
    api.add("POST", "/v1/auth/token/refresh", httpx.ConnectError("boom"))
    api.add("GET", "/v1/accounts/balance", envelope(BALANCE))
    with make_client(api, token_store=store, max_retries=0) as client:
        client.accounts.get_balance()
    assert api.last().headers["authorization"] == "Bearer access-1"


def test_refresh_outage_with_expired_token_raises(api: MockAPI) -> None:
    store = InMemoryTokenStore()
    store.set(Token("expired", "r", _now() - timedelta(minutes=2)))
    api.add("POST", "/v1/auth/token/refresh", httpx.Response(503, json={"code": "503", "description": "down"}))
    with make_client(api, token_store=store, max_retries=0) as client, pytest.raises(ServerError):
        client.accounts.get_balance()


def test_issue_failure_raises_authentication_error(api: MockAPI) -> None:
    api.add(
        "POST",
        "/v1/auth/token/issue",
        httpx.Response(400, json={"code": "400", "description": "invalid client credentials"}),
    )
    with make_client(api) as client, pytest.raises(AuthenticationError) as info:
        client.accounts.get_balance()
    assert info.value.http_status == 400
    assert "invalid client credentials" in str(info.value)
    assert CLIENT_SECRET not in str(info.value)
    assert "/v1/auth/token/issue" in str(info.value)


def test_issue_without_access_token_raises(api: MockAPI) -> None:
    api.add("POST", "/v1/auth/token/issue", envelope({"expiresAt": "2026-01-01T00:00:00Z"}))
    with make_client(api) as client, pytest.raises(AuthenticationError, match="no access_token"):
        client.accounts.get_balance()


def test_issue_5xx_is_retried_then_server_error(api: MockAPI, sleeps: list[float]) -> None:
    api.add("POST", "/v1/auth/token/issue", httpx.Response(503, json={"code": "503", "description": "down"}))
    with make_client(api, sleeps) as client, pytest.raises(ServerError):
        client.accounts.get_balance()
    assert api.paths().count("POST /v1/auth/token/issue") == 3
    assert len(sleeps) == 2


def test_401_invalidates_and_retries_once(api: MockAPI) -> None:
    api.add(
        "POST",
        "/v2/transfers/wallet",
        httpx.Response(401, json={"code": "401", "description": "expired"}),
        envelope({"id": "t1", "status": "SUCCESS"}),
    )
    with make_client(api) as client:
        result = client.transfers.to_wallet({"amount": 10, "receiverAccountId": "r", "merchantTxRef": "ref-1"})
    assert result["id"] == "t1"
    assert api.paths() == [
        "POST /v1/auth/token/issue",
        "POST /v2/transfers/wallet",
        "POST /v1/auth/token/issue",
        "POST /v2/transfers/wallet",
    ]
    first, second = (r for r in api.requests if r.url.path == "/v2/transfers/wallet")
    assert first.headers["authorization"] == "Bearer access-1"
    assert second.headers["authorization"] == "Bearer access-2"
    assert body_of(first) == body_of(second)


def test_401_twice_raises_authentication_error(api: MockAPI) -> None:
    api.add("GET", "/v1/accounts/parent", httpx.Response(401, json={"code": "401", "description": "nope"}))
    with make_client(api) as client, pytest.raises(AuthenticationError) as info:
        client.accounts.get_parent()
    assert info.value.http_status == 401
    assert api.paths().count("GET /v1/accounts/parent") == 2
    assert "access-" not in str(info.value)


def test_401_after_other_caller_refreshed_reuses_new_token(api: MockAPI) -> None:
    store = InMemoryTokenStore()
    store.set(Token("stale", "r", _now() + timedelta(minutes=20)))

    def first(request: httpx.Request) -> httpx.Response:
        # Another worker replaced the token while this request was in flight.
        store.set(Token("fresh-from-elsewhere", "r2", _now() + timedelta(minutes=20)))
        return httpx.Response(401, json={"code": "401", "description": "expired"})

    api.add("GET", "/v1/accounts/parent", first, envelope({"accountId": "x"}))
    with make_client(api, token_store=store) as client:
        client.accounts.get_parent()
    assert "POST /v1/auth/token/issue" not in api.paths()
    assert api.last().headers["authorization"] == "Bearer fresh-from-elsewhere"


def test_single_flight_threads(api: MockAPI) -> None:
    gate = threading.Event()

    def slow_issue(request: httpx.Request) -> httpx.Response:
        gate.wait(1)
        return envelope(
            {"access_token": "shared", "refresh_token": "r", "expiresAt": (_now() + timedelta(minutes=30)).isoformat()}
        )

    api.add("POST", "/v1/auth/token/issue", slow_issue)
    api.add("GET", "/v1/accounts/balance", envelope(BALANCE))
    errors: list[BaseException] = []
    with make_client(api) as client:

        def work() -> None:
            try:
                client.accounts.get_balance()
            except BaseException as exc:  # pragma: no cover - surfaced below
                errors.append(exc)

        threads = [threading.Thread(target=work) for _ in range(8)]
        for t in threads:
            t.start()
        gate.set()
        for t in threads:
            t.join()
    assert errors == []
    assert api.paths().count("POST /v1/auth/token/issue") == 1
    assert api.paths().count("GET /v1/accounts/balance") == 8


async def test_single_flight_async(api: MockAPI) -> None:
    api.add("GET", "/v1/accounts/balance", envelope(BALANCE))
    client = make_async_client(api)
    async with client:
        await asyncio.gather(*(client.accounts.get_balance() for _ in range(10)))
    assert api.paths().count("POST /v1/auth/token/issue") == 1
    assert api.paths().count("GET /v1/accounts/balance") == 10


async def test_async_401_retry_and_refresh(api: MockAPI) -> None:
    api.add(
        "GET",
        "/v1/accounts/parent",
        httpx.Response(401, json={"code": "401", "description": "expired"}),
        envelope({"accountId": "x"}),
    )
    async with make_async_client(api) as client:
        result = await client.accounts.get_parent()
    assert result["accountId"] == "x"
    assert api.paths().count("POST /v1/auth/token/issue") == 2


class AsyncStore:
    def __init__(self) -> None:
        self.token: Token | None = None
        self.calls: list[str] = []

    async def get(self) -> Token | None:
        self.calls.append("get")
        return self.token

    async def set(self, token: Token | None) -> None:
        self.calls.append("set")
        self.token = token


async def test_async_token_store(api: MockAPI) -> None:
    store = AsyncStore()
    api.add("GET", "/v1/accounts/balance", envelope(BALANCE))
    async with make_async_client(api, token_store=store) as client:
        await client.accounts.get_balance()
        await client.accounts.get_balance()
    assert store.token is not None
    assert store.token.access_token == "access-1"
    assert api.paths().count("POST /v1/auth/token/issue") == 1
    assert "set" in store.calls


async def test_async_refresh_path(api: MockAPI) -> None:
    store = InMemoryTokenStore()
    store.set(Token("old", "old-refresh", _now() + timedelta(minutes=1)))
    api.add("GET", "/v1/accounts/balance", envelope(BALANCE))
    async with make_async_client(api, token_store=store) as client:
        await client.accounts.get_balance()
    assert api.paths()[0] == "POST /v1/auth/token/refresh"


def test_revoke_posts_token_and_clears_store(api: MockAPI) -> None:
    store = InMemoryTokenStore()
    store.set(Token("to-revoke", "r", _now() + timedelta(minutes=20)))
    api.add("POST", "/v1/auth/token/revoke", envelope({"code": "00", "description": "Token revoked successfully"}))
    with make_client(api, token_store=store) as client:
        result = client.auth.revoke()
    assert result == {"code": "00", "description": "Token revoked successfully"}
    assert body_of(api.last()) == {"clientId": CLIENT_ID, "access_token": "to-revoke"}
    assert api.last().headers["authorization"] == "Bearer to-revoke"
    assert store.get() is None


def test_revoke_without_token_is_a_no_op(api: MockAPI) -> None:
    with make_client(api) as client:
        assert client.auth.revoke() is None
    assert api.requests == []


def test_revoke_clears_store_even_on_error(api: MockAPI) -> None:
    store = InMemoryTokenStore()
    store.set(Token("t", "r", _now() + timedelta(minutes=20)))
    api.add("POST", "/v1/auth/token/revoke", httpx.Response(500, json={"code": "500", "description": "x"}))
    with make_client(api, token_store=store) as client, pytest.raises(ServerError):
        client.auth.revoke()
    assert store.get() is None
    assert api.paths().count("POST /v1/auth/token/revoke") == 1


async def test_async_revoke(api: MockAPI) -> None:
    store = AsyncStore()
    store.token = Token("t", "r", _now() + timedelta(minutes=20))
    api.add("POST", "/v1/auth/token/revoke", envelope({"code": "00"}))
    async with make_async_client(api, token_store=store) as client:
        assert await client.auth.revoke() == {"code": "00"}
        assert await client.auth.revoke() is None
    assert store.token is None


def test_token_repr_hides_secrets() -> None:
    token = Token("secret-access", "secret-refresh", _now())
    assert "secret-access" not in repr(token)
    assert "secret-refresh" not in repr(token)
    assert "has_token=False" in repr(InMemoryTokenStore())


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2026-03-08T14:56:59Z", datetime(2026, 3, 8, 14, 56, 59, tzinfo=timezone.utc)),
        ("2026-03-08T14:56:59.123456789Z", datetime(2026, 3, 8, 14, 56, 59, 123456, tzinfo=timezone.utc)),
        ("2026-03-08T14:56:59.5+01:00", datetime(2026, 3, 8, 13, 56, 59, 500000, tzinfo=timezone.utc)),
        ("2026-03-08T14:56:59", datetime(2026, 3, 8, 14, 56, 59, tzinfo=timezone.utc)),
    ],
)
def test_parse_timestamp(text: str, expected: datetime) -> None:
    assert parse_timestamp(text) == expected


def test_token_from_response_fallbacks() -> None:
    now = _now()
    token = token_from_response({"access_token": "a", "expiresAt": "not a date"}, now)
    assert token.refresh_token == ""
    assert now < token.expires_at <= now + timedelta(minutes=10)
    no_expiry = token_from_response({"access_token": "a"}, now)
    assert no_expiry.expires_at == now + timedelta(minutes=10)
    with pytest.raises(ValueError, match="data object"):
        token_from_response(None, now)


def test_token_decision() -> None:
    now = _now()
    assert token_decision(None, now) == "issue"
    assert token_decision(Token("a", "r", now + timedelta(minutes=10)), now) == "valid"
    assert token_decision(Token("a", "r", now + timedelta(minutes=4)), now) == "refresh"
    assert token_decision(Token("a", "", now + timedelta(minutes=4)), now) == "issue"


def test_custom_sync_store_shared_by_two_clients(api: MockAPI) -> None:
    store = InMemoryTokenStore()
    api.add("GET", "/v1/accounts/balance", envelope(BALANCE))
    kwargs: dict[str, Any] = {"token_store": store}
    with make_client(api, **kwargs) as one, make_client(api, **kwargs) as two:
        one.accounts.get_balance()
        two.accounts.get_balance()
    assert api.paths().count("POST /v1/auth/token/issue") == 1
