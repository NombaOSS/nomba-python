from __future__ import annotations

from typing import Any, Literal, TypedDict

__all__ = [
    "AuthorizeExchangeParams",
    "AuthorizeTransferParams",
    "Beneficiary",
    "ConversionQuote",
    "ConvertMoneyParams",
    "ExchangeRate",
    "ExchangeRates",
    "GlobalPayoutAccount",
    "GlobalPayoutResult",
    "GlobalPayoutTransaction",
    "InstitutionProvider",
    "PaymentMethod",
]


class GlobalPayoutAccount(TypedDict, total=False):
    accountId: str
    name: str
    currency: str
    balance: float
    availableBalance: float
    status: Literal["ACTIVE", "UNAVAILABLE"]
    operationRegion: str


class InstitutionProvider(TypedDict, total=False):
    code: str
    displayName: str


class ExchangeRate(TypedDict, total=False):
    exchangeRateId: str
    currencyPairName: str
    bidRate: str
    askRate: str
    midRate: str
    createdAt: str


class ExchangeRates(TypedDict, total=False):
    rates: list[ExchangeRate]


class PaymentMethod(TypedDict, total=False):
    code: str
    displayName: str
    purposeOfPaymentRequired: bool
    purposeOfPayments: list[dict[str, Any]]
    requiredFields: list[str]
    optionalFields: list[str]
    accountTypes: list[str]
    bankAccountTypes: list[str]
    supportedCorridors: list[dict[str, Any]]


class GlobalPayoutTransaction(TypedDict, total=False):
    transactionId: str
    status: Literal["PROCESSING", "COMPLETED", "FAILED", "PENDING"]
    coreStatus: str
    type: str
    createdAt: str
    idempotencyKey: str


class _AuthorizeExchangeRequired(TypedDict):
    amount: float
    sourceCurrency: str
    destinationCurrency: str
    senderName: str
    receiverName: str
    sourceCountryIsoCode: str
    destinationCountryIsoCode: str


class AuthorizeExchangeParams(_AuthorizeExchangeRequired, total=False):
    narration: str
    lockedExchangeRateId: str
    idempotencyKey: str


class GlobalPayoutResult(TypedDict, total=False):
    wtTransactionId: str
    coreTransactionId: str
    status: str
    coreStatus: str
    type: str
    idempotencyKey: str
    idempotentReplay: bool
    prettyStatus: str
    meta: dict[str, Any]


class ConvertMoneyParams(TypedDict):
    amount: float
    currency: str
    destinationCurrency: str
    transactionType: str


class ConversionQuote(TypedDict, total=False):
    fromAmount: float
    fromCurrency: str
    fromFormatted: str
    toAmount: float
    toCurrency: str
    toFormatted: str
    spreadAmount: float
    spreadCurrency: str
    exchangeRateId: str
    currencyPairName: str
    feeAmount: float
    feeCurrency: str


class Beneficiary(TypedDict, total=False):
    beneficiaryEmail: str
    securityQuestion: str
    securityQuestionAnswer: str
    transitNumber: str
    beneficiaryAddress: str
    beneficiaryCity: str
    beneficiaryState: str
    beneficiaryPostCode: str


class _AuthorizeTransferRequired(TypedDict):
    amount: float
    sourceCurrency: str
    destinationCurrency: str
    receiverName: str
    sourceCountryIsoCode: str
    destinationCountryIsoCode: str
    paymentMethod: Literal["BANK", "MobileMoney", "INTERAC", "FASTER_PAYMENTS", "SEPA", "ACH", "WIRE"]
    accountType: Literal["INDIVIDUAL", "CORPORATE"]


class AuthorizeTransferParams(_AuthorizeTransferRequired, total=False):
    accountNumber: str
    institutionCode: str
    institutionName: str
    bankAccountType: Literal["CHECKING", "SAVINGS"]
    purposeOfPayment: str
    narration: str
    lockedExchangeRateId: str
    idempotencyKey: str
    bankAddress: str
    bankCity: str
    bankState: str
    bankZipCode: str
    beneficiary: Beneficiary
