from __future__ import annotations

from typing import Literal, TypedDict

from .shared import BillPurchase

__all__ = [
    "AirtimeParams",
    "BettingParams",
    "BettingProvider",
    "BillPurchase",
    "CableTvParams",
    "CableTvPlan",
    "CableTvType",
    "DataParams",
    "DataPlan",
    "ElectricityCustomer",
    "ElectricityParams",
    "ElectricityProvider",
    "Network",
]

Network = Literal["GLO", "MTN", "9MOBILE", "AIRTEL"]
CableTvType = Literal["dstv", "gotv", "startimes", "showmax"]


class _AirtimeRequired(TypedDict):
    amount: float
    phoneNumber: str
    network: Network


class AirtimeParams(_AirtimeRequired, total=False):
    """``merchantTxRef`` is generated (UUID v4) if you leave it out."""

    merchantTxRef: str
    senderName: str


class _DataRequired(TypedDict):
    productId: str
    phoneNumber: str
    network: Network


class DataParams(_DataRequired, total=False):
    """``merchantTxRef`` is generated (UUID v4) if you leave it out."""

    amount: float
    merchantTxRef: str
    senderName: str


class DataPlan(TypedDict, total=False):
    plan: str
    amount: int
    productId: str


class ElectricityParams(TypedDict, total=False):
    """``merchantTxRef`` is generated (UUID v4) if you leave it out."""

    disco: str
    merchantTxRef: str
    payerName: str
    amount: int
    customerId: str
    meterType: str
    """``"prepaid"`` or ``"postpaid"``."""


class ElectricityProvider(TypedDict, total=False):
    id: str
    name: str


class ElectricityCustomer(TypedDict):
    name: str
    address: str


class CableTvParams(TypedDict, total=False):
    """``merchantTxRef`` is generated (UUID v4) if you leave it out."""

    cableTvType: str
    merchantTxRef: str
    payerName: str
    amount: int
    customerId: str


class CableTvPlan(TypedDict):
    subScriptionType: str
    amount: float


class BettingParams(TypedDict, total=False):
    """``merchantTxRef`` is generated (UUID v4) if you leave it out."""

    bettingProvider: str
    merchantTxRef: str
    phoneNumber: str
    payerName: str
    amount: int
    customerId: str


class _BettingProviderBase(TypedDict):
    id: str
    name: str


class BettingProvider(_BettingProviderBase, total=False):
    lookup_id: str
    amount: str
    biller_id: str
