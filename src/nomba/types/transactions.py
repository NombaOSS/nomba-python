from __future__ import annotations

from typing import Any, Literal, TypedDict

__all__ = ["BankTransaction", "BankTransactionPage", "Transaction", "TransactionFilters", "TransactionPage"]


class _TransactionBase(TypedDict):
    id: str
    status: str
    """See :class:`nomba.TransactionStatus`."""
    amount: float
    source: str
    type: str
    gatewayMessage: str
    timeCreated: str


class Transaction(_TransactionBase, total=False):
    fixedCharge: float
    customerBillerId: str
    posTid: str
    terminalId: str
    providerTerminalId: str
    rrn: str
    posSerialNumber: str
    posTerminalLabel: str
    stan: str
    paymentVendorReference: str
    userId: str
    posRrn: str
    merchantTxRef: str


class TransactionPage(TypedDict, total=False):
    results: list[Transaction]
    cursor: str


class TransactionFilters(TypedDict, total=False):
    transactionRef: str
    status: Literal[
        "NEW", "PENDING_PAYMENT", "PAYMENT_SUCCESSFUL", "PAYMENT_FAILED", "PENDING_BILLING", "SUCCESS", "REFUND"
    ]
    source: Literal["api", "pos", "web", "android_app", "ios_app"]
    type: Literal["withdrawal", "purchase", "transfer", "p2p", "online_checkout", "qrt_credit", "qrt_debit"]
    terminalId: str
    rrn: str
    merchantTxRef: str
    orderReference: str
    orderId: str


class BankTransaction(TypedDict, total=False):
    amount: float
    currency: str
    meta: dict[str, Any]
    status: str
    timeUpdated: str
    walletBalance: float
    transactionType: Literal["CREDIT", "DEBIT"]


class BankTransactionPage(TypedDict, total=False):
    results: list[BankTransaction]
    cursor: str
