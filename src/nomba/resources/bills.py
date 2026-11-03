from __future__ import annotations

from typing import Any

from .._core import Request, add_reference, path, require, validate_segment, with_reference
from ..types.bills import (
    AirtimeParams,
    BettingParams,
    BettingProvider,
    BillPurchase,
    CableTvParams,
    CableTvPlan,
    DataParams,
    DataPlan,
    ElectricityCustomer,
    ElectricityParams,
    ElectricityProvider,
)
from ._base import AsyncResource, SyncResource


def _purchase(product: str, params: Any, sub_account_id: str | None) -> Request[BillPurchase]:
    body, ref = with_reference(params)
    base = f"/v2/bill/{product}"
    p = base if sub_account_id is None else path(base + "/{}", sub_account_id)
    return Request("POST", p, body=body, postprocess=add_reference("merchantTxRef", ref))


def _list_data_plans(telco: str) -> Request[list[DataPlan]]:
    return Request("GET", path("/v1/bill/data-plan/{}", validate_segment(telco, "telco").lower()))


def _list_electricity_providers() -> Request[list[ElectricityProvider]]:
    return Request("GET", "/v1/bill/electricity/discos")


def _lookup_electricity_customer(disco: str, customer_id: str) -> Request[ElectricityCustomer]:
    require(disco, "disco")
    require(customer_id, "customer_id")
    return Request("GET", "/v2/bill/electricity/lookup", query={"disco": disco, "customerId": customer_id})


def _list_cable_tv_plans(cable_tv_type: str) -> Request[list[CableTvPlan]]:
    require(cable_tv_type, "cable_tv_type")
    return Request("GET", "/v1/bill/cableTvProduct", query={"cableTvType": cable_tv_type})


def _lookup_cable_tv_customer(customer_id: str, cable_tv_type: str) -> Request[str]:
    require(customer_id, "customer_id")
    require(cable_tv_type, "cable_tv_type")
    return Request("GET", "/v1/bill/cabletv/lookup", query={"customerId": customer_id, "cableTvType": cable_tv_type})


def _list_betting_providers() -> Request[list[BettingProvider]]:
    return Request("GET", "/v1/bill/betting/providers")


def _lookup_betting_customer(provider_id: str, customer_id: str) -> Request[str]:
    require(provider_id, "provider_id")
    require(customer_id, "customer_id")
    return Request("GET", "/v1/bill/betting/lookup", query={"providerId": provider_id, "customerId": customer_id})


class Bills(SyncResource):
    """Airtime, data, electricity, cable TV and betting.

    Purchases are never retried automatically. Each one sends a
    ``merchantTxRef`` (yours, or a generated UUID v4) and returns it in the result.
    """

    def buy_airtime(self, params: AirtimeParams, *, sub_account_id: str | None = None) -> BillPurchase:
        return self._client._request(_purchase("topup", params, sub_account_id))

    def buy_data(self, params: DataParams, *, sub_account_id: str | None = None) -> BillPurchase:
        return self._client._request(_purchase("data", params, sub_account_id))

    def list_data_plans(self, telco: str) -> list[DataPlan]:
        """Data plans for a network (``"mtn"``, ``"glo"``, ...; case-insensitive)."""
        return self._client._request(_list_data_plans(telco))

    def buy_electricity(self, params: ElectricityParams, *, sub_account_id: str | None = None) -> BillPurchase:
        return self._client._request(_purchase("electricity", params, sub_account_id))

    def list_electricity_providers(self) -> list[ElectricityProvider]:
        return self._client._request(_list_electricity_providers())

    def lookup_electricity_customer(self, *, disco: str, customer_id: str) -> ElectricityCustomer:
        """Name and address for a meter number."""
        return self._client._request(_lookup_electricity_customer(disco, customer_id))

    def pay_cable_tv(self, params: CableTvParams, *, sub_account_id: str | None = None) -> BillPurchase:
        return self._client._request(_purchase("cabletv", params, sub_account_id))

    def list_cable_tv_plans(self, cable_tv_type: str) -> list[CableTvPlan]:
        """Plans for ``"dstv"``, ``"gotv"``, ``"startimes"`` or ``"showmax"``."""
        return self._client._request(_list_cable_tv_plans(cable_tv_type))

    def lookup_cable_tv_customer(self, *, customer_id: str, cable_tv_type: str) -> str:
        """The customer's name for a smartcard/IUC number."""
        return self._client._request(_lookup_cable_tv_customer(customer_id, cable_tv_type))

    def fund_betting(self, params: BettingParams, *, sub_account_id: str | None = None) -> BillPurchase:
        return self._client._request(_purchase("betting", params, sub_account_id))

    def list_betting_providers(self) -> list[BettingProvider]:
        return self._client._request(_list_betting_providers())

    def lookup_betting_customer(self, *, provider_id: str, customer_id: str) -> str:
        """The customer's name on a betting account."""
        return self._client._request(_lookup_betting_customer(provider_id, customer_id))


class AsyncBills(AsyncResource):
    """Airtime, data, electricity, cable TV and betting (async)."""

    async def buy_airtime(self, params: AirtimeParams, *, sub_account_id: str | None = None) -> BillPurchase:
        return await self._client._request(_purchase("topup", params, sub_account_id))

    async def buy_data(self, params: DataParams, *, sub_account_id: str | None = None) -> BillPurchase:
        return await self._client._request(_purchase("data", params, sub_account_id))

    async def list_data_plans(self, telco: str) -> list[DataPlan]:
        return await self._client._request(_list_data_plans(telco))

    async def buy_electricity(self, params: ElectricityParams, *, sub_account_id: str | None = None) -> BillPurchase:
        return await self._client._request(_purchase("electricity", params, sub_account_id))

    async def list_electricity_providers(self) -> list[ElectricityProvider]:
        return await self._client._request(_list_electricity_providers())

    async def lookup_electricity_customer(self, *, disco: str, customer_id: str) -> ElectricityCustomer:
        return await self._client._request(_lookup_electricity_customer(disco, customer_id))

    async def pay_cable_tv(self, params: CableTvParams, *, sub_account_id: str | None = None) -> BillPurchase:
        return await self._client._request(_purchase("cabletv", params, sub_account_id))

    async def list_cable_tv_plans(self, cable_tv_type: str) -> list[CableTvPlan]:
        return await self._client._request(_list_cable_tv_plans(cable_tv_type))

    async def lookup_cable_tv_customer(self, *, customer_id: str, cable_tv_type: str) -> str:
        return await self._client._request(_lookup_cable_tv_customer(customer_id, cable_tv_type))

    async def fund_betting(self, params: BettingParams, *, sub_account_id: str | None = None) -> BillPurchase:
        return await self._client._request(_purchase("betting", params, sub_account_id))

    async def list_betting_providers(self) -> list[BettingProvider]:
        return await self._client._request(_list_betting_providers())

    async def lookup_betting_customer(self, *, provider_id: str, customer_id: str) -> str:
        return await self._client._request(_lookup_betting_customer(provider_id, customer_id))
