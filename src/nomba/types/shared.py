"""Types shared by several resources.

Python 3.10 has no ``typing.NotRequired``, so TypedDicts with both required and
optional keys are split into a private base class (required keys) and a
public ``total=False`` subclass (optional keys).
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

Currency = str
"""ISO currency code, e.g. ``"NGN"``."""

TransactionType = Literal["withdrawal", "purchase", "transfer", "p2p", "online_checkout", "qrt_credit", "qrt_debit"]
TransactionSource = Literal["api", "pos", "web", "android_app", "ios_app"]


class SuccessMessage(TypedDict, total=False):
    """``{"success": true, "message": "..."}``-style results."""

    success: bool
    status: bool
    message: str


class _BillPurchaseBase(TypedDict):
    id: str
    status: str
    type: str
    amount: float
    timeCreated: str


class BillPurchase(_BillPurchaseBase, total=False):
    """Result of an airtime, data, electricity, cable TV or betting purchase.

    ``merchantTxRef`` is the reference the SDK sent (yours, or a generated one).
    """

    source: str
    sourceUserId: str
    customerBillerId: str
    productId: str
    meta: dict[str, Any]
    userId: str
    merchantTxRef: str
