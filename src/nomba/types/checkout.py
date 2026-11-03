from __future__ import annotations

from typing import Any, Literal, TypedDict

from .shared import SuccessMessage

__all__ = [
    "CancelOrderParams",
    "CancelTransactionParams",
    "CardDetailsResult",
    "CardOtpResult",
    "ChargeSavedCardParams",
    "ChargeSavedCardResult",
    "CheckoutOrder",
    "CheckoutOrderParams",
    "CheckoutTransaction",
    "ConfirmTransactionReceiptResult",
    "CreateOrderParams",
    "CreateOrderResult",
    "DeleteSavedCardParams",
    "DeviceInformation",
    "OrderDetails",
    "OrderReferenceParams",
    "RefundParams",
    "RequestSaveCardOtpParams",
    "SavedCard",
    "SavedCardList",
    "SavedCardOrder",
    "SplitRequest",
    "SubmitCardDetailsParams",
    "SubmitCardOtpParams",
    "SubmitUserOtpParams",
    "SuccessMessage",
    "TransferAccount",
    "UpdateSavedCardEmailParams",
    "UpdateSavedCardEmailResult",
    "UserSavedCards",
]


class SplitEntry(TypedDict, total=False):
    accountId: str
    value: float


class SplitRequest(TypedDict, total=False):
    splitType: Literal["PERCENTAGE", "AMOUNT"]
    splitList: list[SplitEntry]


class _CheckoutOrderRequired(TypedDict):
    callbackUrl: str
    customerEmail: str
    amount: float | str
    currency: str


class CheckoutOrderParams(_CheckoutOrderRequired, total=False):
    orderReference: str
    customerId: str
    accountId: str
    allowedPaymentMethods: list[str]
    splitRequest: SplitRequest
    orderMetaData: dict[str, Any]


class _CreateOrderRequired(TypedDict):
    order: CheckoutOrderParams


class CreateOrderParams(_CreateOrderRequired, total=False):
    tokenizeCard: bool


class CreateOrderResult(TypedDict):
    checkoutLink: str
    orderReference: str


class CheckoutOrder(TypedDict, total=False):
    orderId: str
    orderReference: str
    customerId: str
    accountId: str
    callbackUrl: str
    customerEmail: str
    amount: float
    currency: str
    businessName: str
    businessEmail: str
    businessLogo: str


class OrderDetails(TypedDict, total=False):
    order: CheckoutOrder
    hasSavedCards: bool
    base64EncodedRsaPublicKey: str


class OrderReferenceParams(TypedDict):
    orderReference: str


CancelOrderParams = OrderReferenceParams


class CheckoutTransaction(TypedDict, total=False):
    success: bool
    message: str
    order: CheckoutOrder
    transactionDetails: dict[str, Any]
    transferDetails: dict[str, Any]
    cardDetails: dict[str, Any]


class _RefundRequired(TypedDict):
    transactionId: str


class RefundParams(_RefundRequired, total=False):
    amount: float
    accountNumber: str
    bankCode: str


class _SavedCardOrderRequired(TypedDict):
    customerEmail: str
    amount: float | str
    currency: str


class SavedCardOrder(_SavedCardOrderRequired, total=False):
    """``orderReference`` is generated (UUID v4) if you leave it out."""

    orderReference: str
    customerId: str
    callbackUrl: str
    accountId: str
    splitRequest: SplitRequest
    orderMetaData: dict[str, Any]


class ChargeSavedCardParams(TypedDict):
    tokenKey: str
    order: SavedCardOrder


class ChargeSavedCardResult(TypedDict, total=False):
    """Check ``status`` and ``otpRequired``; ``description`` doesn't say whether the bank approved."""

    status: bool
    message: str
    orderId: str
    orderReference: str
    otpRequired: bool
    transactionId: str


class SavedCard(TypedDict, total=False):
    tokenKey: str
    customerEmail: str
    cardType: str
    cardPan: str
    tokenExpiryDate: str


class SavedCardList(TypedDict, total=False):
    hasNextPage: bool
    nextPage: int
    tokenizedCardDataList: list[SavedCard]


class UpdateSavedCardEmailParams(TypedDict):
    tokenKey: str
    currentEmailAddress: str
    newEmailAddress: str


class UpdateSavedCardEmailResult(TypedDict, total=False):
    status: bool
    message: str
    tokenizedCardData: SavedCard


class DeleteSavedCardParams(TypedDict):
    tokenKey: str


class TransferAccount(TypedDict):
    accountNumber: str
    accountName: str
    bankName: str


class DeviceInformation(TypedDict, total=False):
    httpBrowserLanguage: str
    httpBrowserJavaEnabled: bool
    httpBrowserJavaScriptEnabled: bool
    httpBrowserColorDepth: str
    httpBrowserScreenHeight: str
    httpBrowserScreenWidth: str
    httpBrowserTimeDifference: str
    userAgentBrowserValue: str
    deviceChannel: str


class SubmitCardDetailsParams(TypedDict, total=False):
    cardDetails: str
    """Card details encrypted with the order's ``base64EncodedRsaPublicKey``."""
    key: str
    orderReference: str
    saveCard: bool
    deviceInformation: DeviceInformation


class CardDetailsResult(TypedDict, total=False):
    status: bool
    message: str
    responseCode: str
    transactionId: str
    secureAuthenticationData: dict[str, Any]


class SubmitCardOtpParams(TypedDict):
    otp: str
    orderReference: str
    transactionId: str


class CardOtpResult(TypedDict):
    status: bool
    message: str


class ConfirmTransactionReceiptResult(TypedDict, total=False):
    status: bool
    message: str
    order: CheckoutOrder


class CancelTransactionParams(TypedDict):
    transactionId: str
    forceCancel: bool


class RequestSaveCardOtpParams(TypedDict):
    orderReference: str
    phoneNumber: str


class SubmitUserOtpParams(TypedDict):
    orderReference: str
    phoneNumber: str
    otp: str


class UserSavedCards(TypedDict, total=False):
    tokenizedCardData: Any
