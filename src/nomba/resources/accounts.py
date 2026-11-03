from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

from .._core import Request, check_limit, exactly_one, path
from ..types.accounts import AccountBalance, AccountDetails, Terminal, TerminalPage
from ._base import AsyncResource, SyncResource, aiterate_pages, iterate_pages


def _get_parent() -> Request[AccountDetails]:
    return Request("GET", "/v1/accounts/parent")


def _get_balance(sub_account_id: str | None) -> Request[AccountBalance]:
    if sub_account_id is None:
        return Request("GET", "/v1/accounts/balance")
    return Request("GET", path("/v1/accounts/{}/balance", sub_account_id))


def _get_sub_account(account_id: str | None, account_ref: str | None) -> Request[AccountDetails]:
    key, value = exactly_one(account_id=account_id, account_ref=account_ref)
    query = {"accountId": value} if key == "account_id" else {"accountRef": value}
    return Request("GET", "/v1/accounts/sub-account-details", query=query)


def _list_terminals(
    sub_account_id: str | None,
    limit: int | None,
    cursor: str | None,
    terminal_id: str | None,
    serial_number: str | None,
    terminal_label: str | None,
    merchant_name: str | None,
) -> Request[TerminalPage]:
    p = "/v1/accounts/terminals" if sub_account_id is None else path("/v1/accounts/{}/terminals", sub_account_id)
    query = {
        "limit": check_limit(limit),
        "cursor": cursor,
        "terminalId": terminal_id,
        "serialNumber": serial_number,
        "terminalLabel": terminal_label,
        "merchantName": merchant_name,
    }
    return Request("GET", p, query=query)


class Accounts(SyncResource):
    def get_parent(self) -> AccountDetails:
        """Details of the parent account. ``GET /v1/accounts/parent``."""
        return self._client._request(_get_parent())

    def get_balance(self, *, sub_account_id: str | None = None) -> AccountBalance:
        """Balance of the parent account, or of ``sub_account_id``."""
        return self._client._request(_get_balance(sub_account_id))

    def get_sub_account(self, *, account_id: str | None = None, account_ref: str | None = None) -> AccountDetails:
        """Look up a sub-account by ``account_id`` or ``account_ref`` (exactly one)."""
        return self._client._request(_get_sub_account(account_id, account_ref))

    def list_terminals(
        self,
        *,
        sub_account_id: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        terminal_id: str | None = None,
        serial_number: str | None = None,
        terminal_label: str | None = None,
        merchant_name: str | None = None,
    ) -> TerminalPage:
        """One page of terminals assigned to the parent account or ``sub_account_id``."""
        return self._client._request(
            _list_terminals(sub_account_id, limit, cursor, terminal_id, serial_number, terminal_label, merchant_name)
        )

    def list_all_terminals(
        self,
        *,
        sub_account_id: str | None = None,
        limit: int | None = None,
        terminal_id: str | None = None,
        serial_number: str | None = None,
        terminal_label: str | None = None,
        merchant_name: str | None = None,
    ) -> Iterator[Terminal]:
        """Iterate over every terminal, fetching pages as needed."""
        check_limit(limit)
        return iterate_pages(
            lambda cursor: self.list_terminals(
                sub_account_id=sub_account_id,
                limit=limit,
                cursor=cursor,
                terminal_id=terminal_id,
                serial_number=serial_number,
                terminal_label=terminal_label,
                merchant_name=merchant_name,
            )
        )


class AsyncAccounts(AsyncResource):
    async def get_parent(self) -> AccountDetails:
        """Details of the parent account. ``GET /v1/accounts/parent``."""
        return await self._client._request(_get_parent())

    async def get_balance(self, *, sub_account_id: str | None = None) -> AccountBalance:
        """Balance of the parent account, or of ``sub_account_id``."""
        return await self._client._request(_get_balance(sub_account_id))

    async def get_sub_account(self, *, account_id: str | None = None, account_ref: str | None = None) -> AccountDetails:
        """Look up a sub-account by ``account_id`` or ``account_ref`` (exactly one)."""
        return await self._client._request(_get_sub_account(account_id, account_ref))

    async def list_terminals(
        self,
        *,
        sub_account_id: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        terminal_id: str | None = None,
        serial_number: str | None = None,
        terminal_label: str | None = None,
        merchant_name: str | None = None,
    ) -> TerminalPage:
        """One page of terminals assigned to the parent account or ``sub_account_id``."""
        return await self._client._request(
            _list_terminals(sub_account_id, limit, cursor, terminal_id, serial_number, terminal_label, merchant_name)
        )

    def list_all_terminals(
        self,
        *,
        sub_account_id: str | None = None,
        limit: int | None = None,
        terminal_id: str | None = None,
        serial_number: str | None = None,
        terminal_label: str | None = None,
        merchant_name: str | None = None,
    ) -> AsyncIterator[Terminal]:
        """Iterate (``async for``) over every terminal, fetching pages as needed."""
        check_limit(limit)
        return aiterate_pages(
            lambda cursor: self.list_terminals(
                sub_account_id=sub_account_id,
                limit=limit,
                cursor=cursor,
                terminal_id=terminal_id,
                serial_number=serial_number,
                terminal_label=terminal_label,
                merchant_name=merchant_name,
            )
        )
