from __future__ import annotations

import asyncio
import inspect
import threading
import time
from collections.abc import Awaitable, Callable
from datetime import datetime
from types import TracebackType
from typing import Any, TypeVar, cast

import httpx

from . import _core
from ._config import Config, resolve_config
from ._core import AccessToken, Flow, Request, Send, Sleep
from .resources.accounts import Accounts, AsyncAccounts
from .resources.auth import AsyncAuth, Auth
from .resources.bills import AsyncBills, Bills
from .resources.checkout import AsyncCheckout, Checkout
from .resources.direct_debits import AsyncDirectDebits, DirectDebits
from .resources.global_collection import AsyncGlobalCollection, GlobalCollection
from .resources.global_payout import AsyncGlobalPayout, GlobalPayout
from .resources.terminals import AsyncTerminals, Terminals
from .resources.transactions import AsyncTransactions, Transactions
from .resources.transfers import AsyncTransfers, Transfers
from .resources.virtual_accounts import AsyncVirtualAccounts, VirtualAccounts
from .tokens import AsyncTokenStore, InMemoryTokenStore, Token, TokenStore
from .webhooks import Webhooks

__all__ = ["AsyncNomba", "Nomba"]

T = TypeVar("T")


def _repr(name: str, config: Config) -> str:
    return (
        f"{name}(environment={config.environment!r}, base_url={config.base_url!r}, "
        f"account_id={config.account_id!r}, client_id={config.client_id!r}, client_secret='***')"
    )


class Nomba:
    """Synchronous Nomba API client.

    Credentials default to the ``NOMBA_CLIENT_ID``, ``NOMBA_CLIENT_SECRET`` and
    ``NOMBA_ACCOUNT_ID`` environment variables. The environment defaults to
    ``"sandbox"``; pass ``environment="production"`` to move real money.
    No network call happens until the first API call.
    """

    def __init__(
        self,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        account_id: str | None = None,
        environment: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        token_store: TokenStore | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._config = resolve_config(
            client_id=client_id,
            client_secret=client_secret,
            account_id=account_id,
            environment=environment,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._store: TokenStore = token_store if token_store is not None else InMemoryTokenStore()
        self._owns_http = http_client is None
        self._http = http_client if http_client is not None else httpx.Client(follow_redirects=False)
        self._token_lock = threading.Lock()
        self._sleep: Callable[[float], None] = time.sleep
        self._now: Callable[[], datetime] = _core.utcnow

        self.auth = Auth(self)
        self.accounts = Accounts(self)
        self.virtual_accounts = VirtualAccounts(self)
        self.checkout = Checkout(self)
        self.transfers = Transfers(self)
        self.transactions = Transactions(self)
        self.terminals = Terminals(self)
        self.direct_debits = DirectDebits(self)
        self.bills = Bills(self)
        self.global_payout = GlobalPayout(self)
        self.global_collection = GlobalCollection(self)
        self.webhooks = Webhooks()

    @property
    def environment(self) -> str:
        return self._config.environment

    @property
    def base_url(self) -> str:
        return self._config.base_url

    def __repr__(self) -> str:
        return _repr("Nomba", self._config)

    # -- lifecycle

    def close(self) -> None:
        """Close the underlying HTTP client (unless you passed your own)."""
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> Nomba:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    # -- driver

    def _request(self, req: Request[T]) -> T:
        return cast(T, self._run(_core.api_flow(req, self._config)))

    def _run(self, flow: Flow[Any]) -> Any:
        value: Any = None
        error: BaseException | None = None
        while True:
            try:
                action = flow.throw(error) if error is not None else flow.send(value)
            except StopIteration as stop:
                return stop.value
            value, error = None, None
            try:
                value = self._perform(action)
            except Exception as exc:  # handed back to the flow
                error = exc

    def _perform(self, action: Any) -> Any:
        if isinstance(action, Send):
            return self._http.send(action.request, follow_redirects=False)
        if isinstance(action, Sleep):
            self._sleep(action.seconds)
            return None
        if isinstance(action, AccessToken):
            return self._access_token(action.stale)
        raise TypeError(f"unknown action {action!r}")  # pragma: no cover

    def _access_token(self, stale: str | None) -> str:
        # Single-flight: concurrent callers wait here and then reuse the token
        # the first caller obtained.
        with self._token_lock:
            token = self._store.get()
            if stale is not None and token is not None and token.access_token == stale:
                self._store.set(None)
                token = None
            decision = _core.token_decision(token, self._now())
            if decision == "valid" and token is not None:
                return token.access_token
            current = token if decision == "refresh" else None
            new: Token = self._run(_core.obtain_token_flow(self._config, current, self._now))
            self._store.set(new)
            return new.access_token

    def _revoke(self) -> Any:
        with self._token_lock:
            token = self._store.get()
        if token is None:
            return None
        try:
            return self._request(_revoke_request(self._config, token))
        finally:
            with self._token_lock:
                self._store.set(None)


class AsyncNomba:
    """Asynchronous Nomba API client. Same surface as :class:`Nomba`, with ``await``."""

    def __init__(
        self,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        account_id: str | None = None,
        environment: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        token_store: AsyncTokenStore | TokenStore | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._config = resolve_config(
            client_id=client_id,
            client_secret=client_secret,
            account_id=account_id,
            environment=environment,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._store: AsyncTokenStore | TokenStore = token_store if token_store is not None else InMemoryTokenStore()
        self._owns_http = http_client is None
        self._http = http_client if http_client is not None else httpx.AsyncClient(follow_redirects=False)
        self._token_lock: asyncio.Lock | None = None
        self._sleep: Callable[[float], Awaitable[None]] = asyncio.sleep
        self._now: Callable[[], datetime] = _core.utcnow

        self.auth = AsyncAuth(self)
        self.accounts = AsyncAccounts(self)
        self.virtual_accounts = AsyncVirtualAccounts(self)
        self.checkout = AsyncCheckout(self)
        self.transfers = AsyncTransfers(self)
        self.transactions = AsyncTransactions(self)
        self.terminals = AsyncTerminals(self)
        self.direct_debits = AsyncDirectDebits(self)
        self.bills = AsyncBills(self)
        self.global_payout = AsyncGlobalPayout(self)
        self.global_collection = AsyncGlobalCollection(self)
        self.webhooks = Webhooks()

    @property
    def environment(self) -> str:
        return self._config.environment

    @property
    def base_url(self) -> str:
        return self._config.base_url

    def __repr__(self) -> str:
        return _repr("AsyncNomba", self._config)

    # -- lifecycle

    async def aclose(self) -> None:
        """Close the underlying HTTP client (unless you passed your own)."""
        if self._owns_http:
            await self._http.aclose()

    async def close(self) -> None:
        """Alias of :meth:`aclose`."""
        await self.aclose()

    async def __aenter__(self) -> AsyncNomba:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    # -- driver

    def _lock(self) -> asyncio.Lock:
        if self._token_lock is None:
            self._token_lock = asyncio.Lock()
        return self._token_lock

    async def _request(self, req: Request[T]) -> T:
        return cast(T, await self._run(_core.api_flow(req, self._config)))

    async def _run(self, flow: Flow[Any]) -> Any:
        value: Any = None
        error: BaseException | None = None
        while True:
            try:
                action = flow.throw(error) if error is not None else flow.send(value)
            except StopIteration as stop:
                return stop.value
            value, error = None, None
            try:
                value = await self._perform(action)
            except Exception as exc:  # handed back to the flow
                error = exc

    async def _perform(self, action: Any) -> Any:
        if isinstance(action, Send):
            return await self._http.send(action.request, follow_redirects=False)
        if isinstance(action, Sleep):
            await self._sleep(action.seconds)
            return None
        if isinstance(action, AccessToken):
            return await self._access_token(action.stale)
        raise TypeError(f"unknown action {action!r}")  # pragma: no cover

    async def _store_get(self) -> Token | None:
        result: Any = self._store.get()
        if inspect.isawaitable(result):
            result = await result
        return cast("Token | None", result)

    async def _store_set(self, token: Token | None) -> None:
        result: Any = self._store.set(token)
        if inspect.isawaitable(result):
            await result

    async def _access_token(self, stale: str | None) -> str:
        async with self._lock():
            token = await self._store_get()
            if stale is not None and token is not None and token.access_token == stale:
                await self._store_set(None)
                token = None
            decision = _core.token_decision(token, self._now())
            if decision == "valid" and token is not None:
                return token.access_token
            current = token if decision == "refresh" else None
            new: Token = await self._run(_core.obtain_token_flow(self._config, current, self._now))
            await self._store_set(new)
            return new.access_token

    async def _revoke(self) -> Any:
        async with self._lock():
            token = await self._store_get()
        if token is None:
            return None
        try:
            return await self._request(_revoke_request(self._config, token))
        finally:
            async with self._lock():
                await self._store_set(None)


def _revoke_request(config: Config, token: Token) -> Request[Any]:
    return Request(
        "POST",
        "/v1/auth/token/revoke",
        body={"clientId": config.client_id, "access_token": token.access_token},
        retry_on_401=False,
    )
