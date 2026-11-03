from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator, Mapping
from typing import TYPE_CHECKING, Any, Generic, Protocol, TypeVar

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


C = TypeVar("C")


class _Resource(Generic[C]):
    def __init__(self, client: C) -> None:
        self._client = client


class SyncResource(_Resource[SyncTransport]):
    pass


class AsyncResource(_Resource[AsyncTransport]):
    pass


def _split_page(page: Any, seen: set[str]) -> tuple[list[Any], str | None]:
    """The page's items, and the cursor to fetch next (``None`` when done or repeated)."""
    if not isinstance(page, Mapping):
        return [], None
    results = page.get("results")
    cursor = page.get("cursor")
    items = results if isinstance(results, list) else []
    if not isinstance(cursor, str) or not cursor or cursor in seen:
        return items, None
    seen.add(cursor)
    return items, cursor


def iterate_pages(fetch: Callable[[str | None], Any]) -> Iterator[Any]:
    """Yield every item across cursor pages. Stops on an empty or repeated cursor."""
    seen: set[str] = set()
    cursor: str | None = None
    while True:
        items, cursor = _split_page(fetch(cursor), seen)
        yield from items
        if cursor is None:
            return


async def aiterate_pages(fetch: Callable[[str | None], Awaitable[Any]]) -> AsyncIterator[Any]:
    """Async version of :func:`iterate_pages`."""
    seen: set[str] = set()
    cursor: str | None = None
    while True:
        items, cursor = _split_page(await fetch(cursor), seen)
        for item in items:
            yield item
        if cursor is None:
            return
