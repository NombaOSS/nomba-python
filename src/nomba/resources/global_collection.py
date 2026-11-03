from __future__ import annotations

from .._core import Request, path
from ..types.global_collection import CollectionTransaction, DrcProvider, InflowResult, InitiateInflowParams
from ._base import AsyncResource, SyncResource


def _list_drc_providers() -> Request[list[DrcProvider]]:
    return Request("GET", "/v1/global-collection/drc/inflow/providers")


def _initiate_inflow(params: InitiateInflowParams) -> Request[InflowResult]:
    return Request("POST", "/v1/global-collection/inflow/initiate", body=dict(params))


def _get_transaction(transaction_id: str) -> Request[CollectionTransaction]:
    return Request("GET", path("/v1/global-collection/transactions/{}", transaction_id))


class GlobalCollection(SyncResource):
    def list_drc_providers(self) -> list[DrcProvider]:
        """Mobile money providers for DRC collections."""
        return self._client._request(_list_drc_providers())

    def initiate_inflow(self, params: InitiateInflowParams) -> InflowResult:
        """Ask a customer to pay by mobile money. Never retried automatically."""
        return self._client._request(_initiate_inflow(params))

    def get_transaction(self, transaction_id: str) -> CollectionTransaction:
        """Status of a mobile money collection."""
        return self._client._request(_get_transaction(transaction_id))


class AsyncGlobalCollection(AsyncResource):
    async def list_drc_providers(self) -> list[DrcProvider]:
        """Mobile money providers for DRC collections."""
        return await self._client._request(_list_drc_providers())

    async def initiate_inflow(self, params: InitiateInflowParams) -> InflowResult:
        """Ask a customer to pay by mobile money. Never retried automatically."""
        return await self._client._request(_initiate_inflow(params))

    async def get_transaction(self, transaction_id: str) -> CollectionTransaction:
        """Status of a mobile money collection."""
        return await self._client._request(_get_transaction(transaction_id))
