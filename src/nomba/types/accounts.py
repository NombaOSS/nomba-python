from __future__ import annotations

from typing import Literal, TypedDict

__all__ = ["AccountBalance", "AccountBank", "AccountDetails", "Terminal", "TerminalPage"]


class AccountBalance(TypedDict):
    amount: str
    currency: str
    timeCreated: str


class AccountBank(TypedDict):
    bankAccountNumber: str
    bankName: str
    bankAccountName: str


class AccountDetails(TypedDict):
    """The parent account, or a sub-account."""

    createdAt: str
    accountId: str
    accountHolderId: str
    accountRef: str
    bvn: str
    status: Literal["ACTIVE", "INACTIVE", "SUSPENDED", "PND", "BLACKLISTED"]
    type: str
    accountName: str
    currency: str
    banks: list[AccountBank]


class Terminal(TypedDict):
    terminalId: str
    serialNumber: str
    accountId: str
    parentAccountId: str
    merchantName: str
    terminalLabel: str
    createdAt: str
    updatedAt: str


class TerminalPage(TypedDict, total=False):
    results: list[Terminal]
    cursor: str
