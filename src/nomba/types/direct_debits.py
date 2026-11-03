from __future__ import annotations

from typing import Literal, TypedDict

__all__ = [
    "CreateMandateParams",
    "DebitMandateParams",
    "DebitMandateResult",
    "Mandate",
    "MandateCreated",
    "MandatePage",
    "MandateStatus",
    "UpdateMandateStatusParams",
    "UpdateMandateStatusResult",
]

MandateFrequency = Literal[
    "VARIABLE",
    "WEEKLY",
    "EVERY_TWO_WEEKS",
    "MONTHLY",
    "EVERY_TWO_MONTHS",
    "EVERY_THREE_MONTHS",
    "EVERY_FOUR_MONTHS",
    "EVERY_FIVE_MONTHS",
    "EVERY_SIX_MONTHS",
    "EVERY_SEVEN_MONTHS",
    "EVERY_EIGHT_MONTHS",
    "EVERY_NINE_MONTHS",
    "EVERY_TEN_MONTHS",
    "EVERY_ELEVEN_MONTHS",
    "EVERY_TWELVE_MONTHS",
]


class _CreateMandateRequired(TypedDict):
    customerAccountNumber: str
    bankCode: str
    customerName: str
    customerAccountName: str
    amount: float
    frequency: MandateFrequency
    merchantReference: str
    startDate: str
    endDate: str
    customerEmail: str


class CreateMandateParams(_CreateMandateRequired, total=False):
    customerAddress: str
    narration: str
    customerPhoneNumber: str
    startImmediately: bool


class MandateCreated(TypedDict):
    mandateId: str
    merchantReference: str
    phoneNumber: str
    description: str


class DebitMandateParams(TypedDict):
    mandateId: str
    amount: str


class DebitMandateResult(TypedDict, total=False):
    mandateId: str
    status: str
    amount: str
    message: str


class _MandateStatusBase(TypedDict):
    customerAccountName: str
    mandateId: str
    customerAccountNumber: str
    mandateStatus: str


class MandateStatus(_MandateStatusBase, total=False):
    rejectionComment: str
    mandateAdviceStatus: str


class Mandate(TypedDict, total=False):
    status: str
    customerAccountNumber: str
    customerAccountName: str
    bankCode: str
    amount: float
    customerName: str
    customerAddress: str
    customerEmail: str
    customerPhoneNumber: str
    merchantReference: str
    frequency: str
    startDate: str
    endDate: str
    mandateAdviceStatus: str
    mandateId: str


class MandatePage(TypedDict, total=False):
    items: list[Mandate]
    page: int
    pageSize: int
    totalItems: int
    totalPages: int
    hasMore: bool


class UpdateMandateStatusParams(TypedDict):
    mandateId: str
    status: Literal["SUSPEND", "ACTIVE", "DELETE"]


class UpdateMandateStatusResult(TypedDict, total=False):
    mandateId: str
    mandateStatus: str
