from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

from .._core import Request, check_limit, exactly_one, path, sub_account_path
from ..types.transactions import (
    BankTransaction,
    BankTransactionPage,
    Transaction,
    TransactionFilters,
    TransactionPage,
)
from ._base import AsyncResource, SyncResource, aiterate_pages, iterate_pages


def _page_query(limit: int | None, cursor: str | None, date_from: str | None, date_to: str | None) -> dict[str, object]:
    return {"limit": check_limit(limit), "cursor": cursor, "dateFrom": date_from, "dateTo": date_to}


def _list(
    sub_account_id: str | None, limit: int | None, cursor: str | None, date_from: str | None, date_to: str | None
) -> Request[TransactionPage]:
    return Request(
        "GET",
        sub_account_path("/v1/transactions/accounts{sub}", sub_account_id),
        query=_page_query(limit, cursor, date_from, date_to),
    )


def _filter(
    filters: TransactionFilters,
    sub_account_id: str | None,
    limit: int | None,
    cursor: str | None,
    date_from: str | None,
    date_to: str | None,
) -> Request[TransactionPage]:
    return Request(
        "POST",
        sub_account_path("/v1/transactions/accounts{sub}", sub_account_id),
        query=_page_query(limit, cursor, date_from, date_to),
        body=dict(filters),
    )


_REF_KEYS = {
    "transaction_ref": "transactionRef",
    "merchant_tx_ref": "merchantTxRef",
    "order_reference": "orderReference",
    "order_id": "orderId",
}


def _get(
    transaction_ref: str | None,
    merchant_tx_ref: str | None,
    order_reference: str | None,
    order_id: str | None,
    sub_account_id: str | None,
) -> Request[Transaction]:
    key, value = exactly_one(
        transaction_ref=transaction_ref,
        merchant_tx_ref=merchant_tx_ref,
        order_reference=order_reference,
        order_id=order_id,
    )
    p = sub_account_path("/v1/transactions/accounts{sub}/single", sub_account_id)
    return Request("GET", p, query={_REF_KEYS[key]: value})


def _list_bank_transactions(
    limit: int | None, cursor: str | None, date_from: str | None, date_to: str | None
) -> Request[BankTransactionPage]:
    return Request("GET", "/v1/transactions/bank", query=_page_query(limit, cursor, date_from, date_to))


def _requery(session_id: str) -> Request[Transaction]:
    return Request("GET", path("/v1/transactions/requery/{}", session_id))


class Transactions(SyncResource):
    def list(
        self,
        *,
        sub_account_id: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> TransactionPage:
        """One page of transactions on the parent account or ``sub_account_id``."""
        return self._client._request(_list(sub_account_id, limit, cursor, date_from, date_to))

    def list_all(
        self,
        *,
        sub_account_id: str | None = None,
        limit: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> Iterator[Transaction]:
        """Iterate over every transaction, fetching pages as needed."""
        check_limit(limit)
        return iterate_pages(
            lambda cursor: self.list(
                sub_account_id=sub_account_id, limit=limit, cursor=cursor, date_from=date_from, date_to=date_to
            )
        )

    def filter(
        self,
        filters: TransactionFilters,
        *,
        sub_account_id: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> TransactionPage:
        """One page of transactions matching ``filters``."""
        return self._client._request(_filter(filters, sub_account_id, limit, cursor, date_from, date_to))

    def filter_all(
        self,
        filters: TransactionFilters,
        *,
        sub_account_id: str | None = None,
        limit: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> Iterator[Transaction]:
        """Iterate over every transaction matching ``filters``."""
        check_limit(limit)
        return iterate_pages(
            lambda cursor: self.filter(
                filters,
                sub_account_id=sub_account_id,
                limit=limit,
                cursor=cursor,
                date_from=date_from,
                date_to=date_to,
            )
        )

    def get(
        self,
        *,
        transaction_ref: str | None = None,
        merchant_tx_ref: str | None = None,
        order_reference: str | None = None,
        order_id: str | None = None,
        sub_account_id: str | None = None,
    ) -> Transaction:
        """Fetch one transaction by exactly one of its references."""
        return self._client._request(_get(transaction_ref, merchant_tx_ref, order_reference, order_id, sub_account_id))

    def list_bank_transactions(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> BankTransactionPage:
        """One page of credits and debits on the parent account."""
        return self._client._request(_list_bank_transactions(limit, cursor, date_from, date_to))

    def list_all_bank_transactions(
        self, *, limit: int | None = None, date_from: str | None = None, date_to: str | None = None
    ) -> Iterator[BankTransaction]:
        """Iterate over every credit and debit on the parent account."""
        check_limit(limit)
        return iterate_pages(
            lambda cursor: self.list_bank_transactions(limit=limit, cursor=cursor, date_from=date_from, date_to=date_to)
        )

    def requery(self, session_id: str) -> Transaction:
        """Confirm a transaction's status by its NIP ``sessionId``."""
        return self._client._request(_requery(session_id))


class AsyncTransactions(AsyncResource):
    async def list(
        self,
        *,
        sub_account_id: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> TransactionPage:
        """One page of transactions on the parent account or ``sub_account_id``."""
        return await self._client._request(_list(sub_account_id, limit, cursor, date_from, date_to))

    def list_all(
        self,
        *,
        sub_account_id: str | None = None,
        limit: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> AsyncIterator[Transaction]:
        """Iterate (``async for``) over every transaction."""
        check_limit(limit)
        return aiterate_pages(
            lambda cursor: self.list(
                sub_account_id=sub_account_id, limit=limit, cursor=cursor, date_from=date_from, date_to=date_to
            )
        )

    async def filter(
        self,
        filters: TransactionFilters,
        *,
        sub_account_id: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> TransactionPage:
        """One page of transactions matching ``filters``."""
        return await self._client._request(_filter(filters, sub_account_id, limit, cursor, date_from, date_to))

    def filter_all(
        self,
        filters: TransactionFilters,
        *,
        sub_account_id: str | None = None,
        limit: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> AsyncIterator[Transaction]:
        """Iterate (``async for``) over every transaction matching ``filters``."""
        check_limit(limit)
        return aiterate_pages(
            lambda cursor: self.filter(
                filters,
                sub_account_id=sub_account_id,
                limit=limit,
                cursor=cursor,
                date_from=date_from,
                date_to=date_to,
            )
        )

    async def get(
        self,
        *,
        transaction_ref: str | None = None,
        merchant_tx_ref: str | None = None,
        order_reference: str | None = None,
        order_id: str | None = None,
        sub_account_id: str | None = None,
    ) -> Transaction:
        """Fetch one transaction by exactly one of its references."""
        return await self._client._request(
            _get(transaction_ref, merchant_tx_ref, order_reference, order_id, sub_account_id)
        )

    async def list_bank_transactions(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> BankTransactionPage:
        """One page of credits and debits on the parent account."""
        return await self._client._request(_list_bank_transactions(limit, cursor, date_from, date_to))

    def list_all_bank_transactions(
        self, *, limit: int | None = None, date_from: str | None = None, date_to: str | None = None
    ) -> AsyncIterator[BankTransaction]:
        """Iterate (``async for``) over every credit and debit on the parent account."""
        check_limit(limit)
        return aiterate_pages(
            lambda cursor: self.list_bank_transactions(limit=limit, cursor=cursor, date_from=date_from, date_to=date_to)
        )

    async def requery(self, session_id: str) -> Transaction:
        """Confirm a transaction's status by its NIP ``sessionId``."""
        return await self._client._request(_requery(session_id))
