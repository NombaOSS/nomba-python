from __future__ import annotations

from typing import TypedDict

__all__ = [
    "CreateVirtualAccountParams",
    "ExpireVirtualAccountResult",
    "UpdateVirtualAccountParams",
    "UpdateVirtualAccountResult",
    "VirtualAccount",
    "VirtualAccountFilters",
    "VirtualAccountPage",
]


class _CreateVirtualAccountRequired(TypedDict):
    accountRef: str
    accountName: str


class CreateVirtualAccountParams(_CreateVirtualAccountRequired, total=False):
    bvn: str
    nin: str
    expiryDate: str
    """``"YYYY-MM-DD HH:MM:SS"``."""
    expectedAmount: float
    restrictInflowToAccountName: bool
    callbackUrl: str


class UpdateVirtualAccountParams(TypedDict, total=False):
    newAccountRef: str
    accountName: str
    expectedAmount: str


class _VirtualAccountBase(TypedDict):
    createdAt: str
    accountHolderId: str
    accountRef: str
    accountName: str
    currency: str


class VirtualAccount(_VirtualAccountBase, total=False):
    bvn: str
    identifierType: str
    bankName: str
    bankAccountNumber: str
    bankAccountName: str
    callbackUrl: str
    expired: bool
    restrictInflowToAccountName: bool


class UpdateVirtualAccountResult(TypedDict):
    updated: bool


class ExpireVirtualAccountResult(TypedDict):
    expired: bool


class VirtualAccountFilters(TypedDict, total=False):
    accountName: str
    accountRef: str
    bvn: str
    bankAccountNumber: str
    dateCreatedFrom: str
    dateCreatedTo: str
    expired: bool
    resourceAcquired: bool


class VirtualAccountPage(TypedDict, total=False):
    results: list[VirtualAccount]
    cursor: str
