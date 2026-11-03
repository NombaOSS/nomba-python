from __future__ import annotations

from typing import Literal, TypedDict

from .accounts import Terminal

__all__ = ["AssignTerminalParams", "Terminal", "TerminalPaymentRequest", "TerminalPaymentRequestParams"]


class _AssignTerminalRequired(TypedDict):
    serialNumber: str


class AssignTerminalParams(_AssignTerminalRequired, total=False):
    terminalLabel: str


class TerminalPaymentRequestParams(TypedDict):
    merchantTxRef: str
    amount: float
    currency: Literal["NGN", "USD", "CDF"]


class TerminalPaymentRequest(TypedDict):
    paymentId: str
    status: Literal["pending", "completed", "failed"]
    amount: float
    currency: str
    createdAt: str
