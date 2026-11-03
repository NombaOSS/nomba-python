from __future__ import annotations

import json
from collections.abc import AsyncIterator, Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import pytest

from nomba import AsyncNomba, Nomba

CLIENT_ID = "test-client-id"
CLIENT_SECRET = "test-client-secret-do-not-log"
ACCOUNT_ID = "test-account-id"

Responder = httpx.Response | Exception | Callable[[httpx.Request], httpx.Response]


def envelope(
    data: Any = None, *, code: str | None = "00", description: str = "Success", status: int = 200
) -> httpx.Response:
    body: dict[str, Any] = {"description": description, "data": data}
    if code is not None:
        body["code"] = code
    return httpx.Response(status, json=body)


def token_response(n: int, *, minutes: int = 30) -> httpx.Response:
    expires = (datetime.now(timezone.utc) + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return envelope(
        {
            "businessId": "biz",
            "access_token": f"access-{n}",
            "refresh_token": f"refresh-{n}",
            "expiresAt": expires,
        }
    )


@dataclass
class MockAPI:
    """A fake Nomba API for httpx.MockTransport.

    Token issue/refresh are answered automatically (``access-1``, ``access-2``, ...)
    unless a test queues its own responses for them.
    """

    routes: dict[tuple[str, str], list[Responder]] = field(default_factory=dict)
    requests: list[httpx.Request] = field(default_factory=list)
    token_minutes: int = 30
    _tokens: int = 0

    def add(self, method: str, path: str, *responses: Responder) -> None:
        self.routes.setdefault((method, path), []).extend(responses)

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        key = (request.method, request.url.path)
        queue = self.routes.get(key)
        if queue:
            item = queue.pop(0) if len(queue) > 1 else queue[0]
            if isinstance(item, Exception):
                raise item
            if callable(item) and not isinstance(item, httpx.Response):
                return item(request)
            # A response body can be streamed only once; hand out a fresh copy.
            return httpx.Response(item.status_code, headers=item.headers, content=item.content)
        if key in (("POST", "/v1/auth/token/issue"), ("POST", "/v1/auth/token/refresh")):
            self._tokens += 1
            return token_response(self._tokens, minutes=self.token_minutes)
        return httpx.Response(404, json={"code": "404", "description": f"no mock for {key}"})

    # -- inspection helpers

    def api_requests(self) -> list[httpx.Request]:
        return [r for r in self.requests if r.url.path not in ("/v1/auth/token/issue", "/v1/auth/token/refresh")]

    def paths(self) -> list[str]:
        return [f"{r.method} {r.url.path}" for r in self.requests]

    def last(self) -> httpx.Request:
        return self.api_requests()[-1]


def body_of(request: httpx.Request) -> Any:
    return json.loads(request.content) if request.content else None


@pytest.fixture
def api() -> MockAPI:
    return MockAPI()


@pytest.fixture
def sleeps() -> list[float]:
    return []


def make_client(api: MockAPI, sleeps: list[float] | None = None, **kwargs: Any) -> Nomba:
    client = Nomba(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        account_id=ACCOUNT_ID,
        http_client=httpx.Client(transport=httpx.MockTransport(api)),
        **kwargs,
    )
    record = sleeps if sleeps is not None else []
    client._sleep = record.append
    return client


def make_async_client(api: MockAPI, sleeps: list[float] | None = None, **kwargs: Any) -> AsyncNomba:
    client = AsyncNomba(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        account_id=ACCOUNT_ID,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(api)),
        **kwargs,
    )
    record = sleeps if sleeps is not None else []

    async def fake_sleep(seconds: float) -> None:
        record.append(seconds)

    client._sleep = fake_sleep
    return client


@pytest.fixture
def client(api: MockAPI, sleeps: list[float]) -> Iterator[Nomba]:
    c = make_client(api, sleeps)
    yield c
    c._http.close()


@pytest.fixture
async def aclient(api: MockAPI, sleeps: list[float]) -> AsyncIterator[AsyncNomba]:
    c = make_async_client(api, sleeps)
    yield c
    await c._http.aclose()
