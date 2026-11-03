from __future__ import annotations

from .._core import Request, require
from ..types.direct_debits import (
    CreateMandateParams,
    DebitMandateParams,
    DebitMandateResult,
    MandateCreated,
    MandatePage,
    MandateStatus,
    UpdateMandateStatusParams,
    UpdateMandateStatusResult,
)
from ._base import AsyncResource, SyncResource


def _create_mandate(params: CreateMandateParams) -> Request[MandateCreated]:
    return Request("POST", "/v1/direct-debits", body=dict(params))


def _debit_mandate(params: DebitMandateParams) -> Request[DebitMandateResult]:
    return Request("POST", "/v1/direct-debits/debit-mandate", body=dict(params))


def _get_mandate_status(mandate_id: str) -> Request[MandateStatus]:
    require(mandate_id, "mandate_id")
    return Request("GET", "/v1/direct-debits/status", query={"mandateId": mandate_id})


def _list_mandates(
    page: int | None, page_size: int | None, from_: str | None, to: str | None, status: str | None
) -> Request[MandatePage]:
    query = {"page": page, "pageSize": page_size, "from": from_, "to": to, "status": status}
    return Request("GET", "/v1/direct-debits/mandates", query=query)


def _update_mandate_status(params: UpdateMandateStatusParams) -> Request[UpdateMandateStatusResult]:
    return Request("PUT", "/v1/direct-debits/update-status", body=dict(params))


class DirectDebits(SyncResource):
    def create_mandate(self, params: CreateMandateParams) -> MandateCreated:
        """Create a direct debit mandate for a customer's bank account."""
        return self._client._request(_create_mandate(params))

    def debit_mandate(self, params: DebitMandateParams) -> DebitMandateResult:
        """Debit a customer through an active mandate. Never retried automatically."""
        return self._client._request(_debit_mandate(params))

    def get_mandate_status(self, mandate_id: str) -> MandateStatus:
        """Status of one mandate."""
        return self._client._request(_get_mandate_status(mandate_id))

    def list_mandates(
        self,
        *,
        page: int | None = None,
        page_size: int | None = None,
        from_: str | None = None,
        to: str | None = None,
        status: str | None = None,
    ) -> MandatePage:
        """One page of mandates. ``from_`` is sent as the ``from`` query parameter."""
        return self._client._request(_list_mandates(page, page_size, from_, to, status))

    def update_mandate_status(self, params: UpdateMandateStatusParams) -> UpdateMandateStatusResult:
        """Suspend, reactivate or delete a mandate."""
        return self._client._request(_update_mandate_status(params))


class AsyncDirectDebits(AsyncResource):
    async def create_mandate(self, params: CreateMandateParams) -> MandateCreated:
        """Create a direct debit mandate for a customer's bank account."""
        return await self._client._request(_create_mandate(params))

    async def debit_mandate(self, params: DebitMandateParams) -> DebitMandateResult:
        """Debit a customer through an active mandate. Never retried automatically."""
        return await self._client._request(_debit_mandate(params))

    async def get_mandate_status(self, mandate_id: str) -> MandateStatus:
        """Status of one mandate."""
        return await self._client._request(_get_mandate_status(mandate_id))

    async def list_mandates(
        self,
        *,
        page: int | None = None,
        page_size: int | None = None,
        from_: str | None = None,
        to: str | None = None,
        status: str | None = None,
    ) -> MandatePage:
        """One page of mandates. ``from_`` is sent as the ``from`` query parameter."""
        return await self._client._request(_list_mandates(page, page_size, from_, to, status))

    async def update_mandate_status(self, params: UpdateMandateStatusParams) -> UpdateMandateStatusResult:
        """Suspend, reactivate or delete a mandate."""
        return await self._client._request(_update_mandate_status(params))
