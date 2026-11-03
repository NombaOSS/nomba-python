from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

from .._core import Request, check_limit, path, sub_account_path
from ..types.virtual_accounts import (
    CreateVirtualAccountParams,
    ExpireVirtualAccountResult,
    UpdateVirtualAccountParams,
    UpdateVirtualAccountResult,
    VirtualAccount,
    VirtualAccountFilters,
    VirtualAccountPage,
)
from ._base import AsyncResource, SyncResource, aiterate_pages, iterate_pages


def _create(params: CreateVirtualAccountParams, sub_account_id: str | None) -> Request[VirtualAccount]:
    return Request("POST", sub_account_path("/v1/accounts/virtual{sub}", sub_account_id), body=dict(params))


def _get(identifier: str) -> Request[VirtualAccount]:
    return Request("GET", path("/v1/accounts/virtual/{}", identifier))


def _update(identifier: str, params: UpdateVirtualAccountParams) -> Request[UpdateVirtualAccountResult]:
    return Request("PUT", path("/v1/accounts/virtual/{}", identifier), body=dict(params))


def _expire(identifier: str) -> Request[ExpireVirtualAccountResult]:
    return Request("DELETE", path("/v1/accounts/virtual/{}", identifier))


def _list(filters: VirtualAccountFilters | None, limit: int | None, cursor: str | None) -> Request[VirtualAccountPage]:
    query = {"limit": check_limit(limit), "cursor": cursor}
    return Request("POST", "/v1/accounts/virtual/list", query=query, body=dict(filters or {}))


class VirtualAccounts(SyncResource):
    def create(self, params: CreateVirtualAccountParams, *, sub_account_id: str | None = None) -> VirtualAccount:
        """Create a virtual account on the parent account or ``sub_account_id``."""
        return self._client._request(_create(params, sub_account_id))

    def get(self, identifier: str) -> VirtualAccount:
        """Fetch a virtual account by its ``accountRef`` or bank account number."""
        return self._client._request(_get(identifier))

    def update(self, identifier: str, params: UpdateVirtualAccountParams) -> UpdateVirtualAccountResult:
        """Update a virtual account's reference, name or expected amount."""
        return self._client._request(_update(identifier, params))

    def expire(self, identifier: str) -> ExpireVirtualAccountResult:
        """Expire a virtual account so it stops accepting payments."""
        return self._client._request(_expire(identifier))

    def list(
        self,
        filters: VirtualAccountFilters | None = None,
        *,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> VirtualAccountPage:
        """One page of virtual accounts matching ``filters``."""
        return self._client._request(_list(filters, limit, cursor))

    def list_all(
        self, filters: VirtualAccountFilters | None = None, *, limit: int | None = None
    ) -> Iterator[VirtualAccount]:
        """Iterate over every matching virtual account, fetching pages as needed."""
        check_limit(limit)
        return iterate_pages(lambda cursor: self.list(filters, limit=limit, cursor=cursor))


class AsyncVirtualAccounts(AsyncResource):
    async def create(self, params: CreateVirtualAccountParams, *, sub_account_id: str | None = None) -> VirtualAccount:
        """Create a virtual account on the parent account or ``sub_account_id``."""
        return await self._client._request(_create(params, sub_account_id))

    async def get(self, identifier: str) -> VirtualAccount:
        """Fetch a virtual account by its ``accountRef`` or bank account number."""
        return await self._client._request(_get(identifier))

    async def update(self, identifier: str, params: UpdateVirtualAccountParams) -> UpdateVirtualAccountResult:
        """Update a virtual account's reference, name or expected amount."""
        return await self._client._request(_update(identifier, params))

    async def expire(self, identifier: str) -> ExpireVirtualAccountResult:
        """Expire a virtual account so it stops accepting payments."""
        return await self._client._request(_expire(identifier))

    async def list(
        self,
        filters: VirtualAccountFilters | None = None,
        *,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> VirtualAccountPage:
        """One page of virtual accounts matching ``filters``."""
        return await self._client._request(_list(filters, limit, cursor))

    def list_all(
        self, filters: VirtualAccountFilters | None = None, *, limit: int | None = None
    ) -> AsyncIterator[VirtualAccount]:
        """Iterate (``async for``) over every matching virtual account."""
        check_limit(limit)
        return aiterate_pages(lambda cursor: self.list(filters, limit=limit, cursor=cursor))
