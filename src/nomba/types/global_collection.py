from __future__ import annotations

from typing import TypedDict

__all__ = ["CollectionTransaction", "DrcProvider", "InflowResult", "InitiateInflowParams"]


class DrcProvider(TypedDict, total=False):
    code: str
    displayName: str


class _InitiateInflowRequired(TypedDict):
    phoneNumber: str
    callbackUrl: str
    amount: float
    currency: str
    topupVendor: str


class InitiateInflowParams(_InitiateInflowRequired, total=False):
    idempotencyKey: str


class InflowResult(TypedDict, total=False):
    transactionReference: str
    status: str
    message: str
    idempotencyKey: str


class CollectionTransaction(TypedDict, total=False):
    transactionId: str
    coreUserId: str
    account: str
    status: str
    amount: float
    currency: str
    vendor: str
    gatewayMessage: str
    gatewayCode: str
