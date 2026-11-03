from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator, Mapping
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

if TYPE_CHECKING:
    from .._config import Config
    from .._core import Request

T = TypeVar("T")


class SyncTransport(Protocol):
    _config: Config

    def _request(self, req: Request[T]) -> T: ...

    def _revoke(self) -> Any: ...


class AsyncTransport(Protocol):
    _config: Config

    async def _request(self, req: Request[T]) -> T: ...

    async def _revoke(self) -> Any: ...


class SyncResource:
    def __init__(self, client: SyncTransport) -> None:
        self._client = client


class AsyncResource:
    def __init__(self, client: AsyncTransport) -> None:
        self._client = client


def _next_cursor(page: Any, seen: set[str]) -> str | None:
    cursor = page.get("cursor") if isinstance(page, Mapping) else None
    if not isinstance(cursor, str) or not cursor or cursor in seen:
        return None
    seen.add(cursor)
    return cursor


def _results(page: Any) -> list[Any]:
    results = page.get("results") if isinstance(page, Mapping) else None
    return results if isinstance(results, list) else []


def iterate_pages(fetch: Callable[[str | None], Any]) -> Iterator[Any]:
    """Yield every item across cursor pages. Stops on an empty or repeated cursor."""
    seen: set[str] = set()
    cursor: str | None = None
    while True:
        page = fetch(cursor)
        yield from _results(page)
        cursor = _next_cursor(page, seen)
        if cursor is None:
            return


async def aiterate_pages(fetch: Callable[[str | None], Awaitable[Any]]) -> AsyncIterator[Any]:
    """Async version of :func:`iterate_pages`."""
    seen: set[str] = set()
    cursor: str | None = None
    while True:
        page = await fetch(cursor)
        for item in _results(page):
            yield item
        cursor = _next_cursor(page, seen)
        if cursor is None:
            return
