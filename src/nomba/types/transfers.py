from __future__ import annotations

from typing import Any, TypedDict

__all__ = ["Bank", "BankAccountLookup", "BankTransferParams", "Transfer", "WalletTransferParams"]


class Bank(TypedDict, total=False):
    code: str
    name: str
    nipCode: str
    logo: str


class BankAccountLookup(TypedDict, total=False):
    accountNumber: str
    accountName: str


class _BankTransferRequired(TypedDict):
    amount: float
    accountNumber: str
    accountName: str
    bankCode: str


class BankTransferParams(_BankTransferRequired, total=False):
    """``merchantTxRef`` is generated (UUID v4) if you leave it out."""

    merchantTxRef: str
    senderName: str
    narration: str


class _WalletTransferRequired(TypedDict):
    amount: float
    receiverAccountId: str


class WalletTransferParams(_WalletTransferRequired, total=False):
    """``merchantTxRef`` is generated (UUID v4) if you leave it out."""

    merchantTxRef: str
    narration: str


class _TransferBase(TypedDict):
    id: str
    status: str
    """See :class:`nomba.TransactionStatus`."""
    type: str
    amount: Any
    """A string for bank transfers, a number for wallet transfers."""
    fee: float
    timeCreated: str
    meta: dict[str, Any]


class Transfer(_TransferBase, total=False):
    source: str
    sourceUserId: str
    customerBillerId: str
    productId: str
    merchantTxRef: str
    """The reference the SDK sent (yours, or a generated one)."""
