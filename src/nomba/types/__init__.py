"""TypedDicts for request params and response data.

Response dicts may carry extra keys that Nomba adds over time.
"""

from __future__ import annotations

from .accounts import (
    AccountBalance as AccountBalance,
)
from .accounts import (
    AccountBank as AccountBank,
)
from .accounts import (
    AccountDetails as AccountDetails,
)
from .accounts import (
    Terminal as Terminal,
)
from .accounts import (
    TerminalPage as TerminalPage,
)
from .auth import (
    RevokeResult as RevokeResult,
)
from .bills import (
    AirtimeParams as AirtimeParams,
)
from .bills import (
    BettingParams as BettingParams,
)
from .bills import (
    BettingProvider as BettingProvider,
)
from .bills import (
    CableTvParams as CableTvParams,
)
from .bills import (
    CableTvPlan as CableTvPlan,
)
from .bills import (
    CableTvType as CableTvType,
)
from .bills import (
    DataParams as DataParams,
)
from .bills import (
    DataPlan as DataPlan,
)
from .bills import (
    ElectricityCustomer as ElectricityCustomer,
)
from .bills import (
    ElectricityParams as ElectricityParams,
)
from .bills import (
    ElectricityProvider as ElectricityProvider,
)
from .bills import (
    Network as Network,
)
from .checkout import (
    CancelOrderParams as CancelOrderParams,
)
from .checkout import (
    CancelTransactionParams as CancelTransactionParams,
)
from .checkout import (
    CardDetailsResult as CardDetailsResult,
)
from .checkout import (
    CardOtpResult as CardOtpResult,
)
from .checkout import (
    ChargeSavedCardParams as ChargeSavedCardParams,
)
from .checkout import (
    ChargeSavedCardResult as ChargeSavedCardResult,
)
from .checkout import (
    CheckoutOrder as CheckoutOrder,
)
from .checkout import (
    CheckoutOrderParams as CheckoutOrderParams,
)
from .checkout import (
    CheckoutTransaction as CheckoutTransaction,
)
from .checkout import (
    ConfirmTransactionReceiptResult as ConfirmTransactionReceiptResult,
)
from .checkout import (
    CreateOrderParams as CreateOrderParams,
)
from .checkout import (
    CreateOrderResult as CreateOrderResult,
)
from .checkout import (
    DeleteSavedCardParams as DeleteSavedCardParams,
)
from .checkout import (
    DeviceInformation as DeviceInformation,
)
from .checkout import (
    OrderDetails as OrderDetails,
)
from .checkout import (
    OrderReferenceParams as OrderReferenceParams,
)
from .checkout import (
    RefundParams as RefundParams,
)
from .checkout import (
    RequestSaveCardOtpParams as RequestSaveCardOtpParams,
)
from .checkout import (
    SavedCard as SavedCard,
)
from .checkout import (
    SavedCardList as SavedCardList,
)
from .checkout import (
    SavedCardOrder as SavedCardOrder,
)
from .checkout import (
    SplitEntry as SplitEntry,
)
from .checkout import (
    SplitRequest as SplitRequest,
)
from .checkout import (
    SubmitCardDetailsParams as SubmitCardDetailsParams,
)
from .checkout import (
    SubmitCardOtpParams as SubmitCardOtpParams,
)
from .checkout import (
    SubmitUserOtpParams as SubmitUserOtpParams,
)
from .checkout import (
    TransferAccount as TransferAccount,
)
from .checkout import (
    UpdateSavedCardEmailParams as UpdateSavedCardEmailParams,
)
from .checkout import (
    UpdateSavedCardEmailResult as UpdateSavedCardEmailResult,
)
from .checkout import (
    UserSavedCards as UserSavedCards,
)
from .direct_debits import (
    CreateMandateParams as CreateMandateParams,
)
from .direct_debits import (
    DebitMandateParams as DebitMandateParams,
)
from .direct_debits import (
    DebitMandateResult as DebitMandateResult,
)
from .direct_debits import (
    Mandate as Mandate,
)
from .direct_debits import (
    MandateCreated as MandateCreated,
)
from .direct_debits import (
    MandateFrequency as MandateFrequency,
)
from .direct_debits import (
    MandatePage as MandatePage,
)
from .direct_debits import (
    MandateStatus as MandateStatus,
)
from .direct_debits import (
    UpdateMandateStatusParams as UpdateMandateStatusParams,
)
from .direct_debits import (
    UpdateMandateStatusResult as UpdateMandateStatusResult,
)
from .global_collection import (
    CollectionTransaction as CollectionTransaction,
)
from .global_collection import (
    DrcProvider as DrcProvider,
)
from .global_collection import (
    InflowResult as InflowResult,
)
from .global_collection import (
    InitiateInflowParams as InitiateInflowParams,
)
from .global_payout import (
    AuthorizeExchangeParams as AuthorizeExchangeParams,
)
from .global_payout import (
    AuthorizeTransferParams as AuthorizeTransferParams,
)
from .global_payout import (
    Beneficiary as Beneficiary,
)
from .global_payout import (
    ConversionQuote as ConversionQuote,
)
from .global_payout import (
    ConvertMoneyParams as ConvertMoneyParams,
)
from .global_payout import (
    ExchangeRate as ExchangeRate,
)
from .global_payout import (
    ExchangeRates as ExchangeRates,
)
from .global_payout import (
    GlobalPayoutAccount as GlobalPayoutAccount,
)
from .global_payout import (
    GlobalPayoutResult as GlobalPayoutResult,
)
from .global_payout import (
    GlobalPayoutTransaction as GlobalPayoutTransaction,
)
from .global_payout import (
    InstitutionProvider as InstitutionProvider,
)
from .global_payout import (
    PaymentMethod as PaymentMethod,
)
from .shared import (
    BillPurchase as BillPurchase,
)
from .shared import (
    Currency as Currency,
)
from .shared import (
    SuccessMessage as SuccessMessage,
)
from .shared import (
    TransactionSource as TransactionSource,
)
from .shared import (
    TransactionType as TransactionType,
)
from .terminals import (
    AssignTerminalParams as AssignTerminalParams,
)
from .terminals import (
    TerminalPaymentRequest as TerminalPaymentRequest,
)
from .terminals import (
    TerminalPaymentRequestParams as TerminalPaymentRequestParams,
)
from .transactions import (
    BankTransaction as BankTransaction,
)
from .transactions import (
    BankTransactionPage as BankTransactionPage,
)
from .transactions import (
    Transaction as Transaction,
)
from .transactions import (
    TransactionFilters as TransactionFilters,
)
from .transactions import (
    TransactionPage as TransactionPage,
)
from .transfers import (
    Bank as Bank,
)
from .transfers import (
    BankAccountLookup as BankAccountLookup,
)
from .transfers import (
    BankTransferParams as BankTransferParams,
)
from .transfers import (
    Transfer as Transfer,
)
from .transfers import (
    WalletTransferParams as WalletTransferParams,
)
from .virtual_accounts import (
    CreateVirtualAccountParams as CreateVirtualAccountParams,
)
from .virtual_accounts import (
    ExpireVirtualAccountResult as ExpireVirtualAccountResult,
)
from .virtual_accounts import (
    UpdateVirtualAccountParams as UpdateVirtualAccountParams,
)
from .virtual_accounts import (
    UpdateVirtualAccountResult as UpdateVirtualAccountResult,
)
from .virtual_accounts import (
    VirtualAccount as VirtualAccount,
)
from .virtual_accounts import (
    VirtualAccountFilters as VirtualAccountFilters,
)
from .virtual_accounts import (
    VirtualAccountPage as VirtualAccountPage,
)
from .webhooks import (
    WebhookEvent as WebhookEvent,
)

__all__ = [
    "AccountBalance",
    "AccountBank",
    "AccountDetails",
    "AirtimeParams",
    "AssignTerminalParams",
    "AuthorizeExchangeParams",
    "AuthorizeTransferParams",
    "Bank",
    "BankAccountLookup",
    "BankTransaction",
    "BankTransactionPage",
    "BankTransferParams",
    "Beneficiary",
    "BettingParams",
    "BettingProvider",
    "BillPurchase",
    "CableTvParams",
    "CableTvPlan",
    "CableTvType",
    "CancelOrderParams",
    "CancelTransactionParams",
    "CardDetailsResult",
    "CardOtpResult",
    "ChargeSavedCardParams",
    "ChargeSavedCardResult",
    "CheckoutOrder",
    "CheckoutOrderParams",
    "CheckoutTransaction",
    "CollectionTransaction",
    "ConfirmTransactionReceiptResult",
    "ConversionQuote",
    "ConvertMoneyParams",
    "CreateMandateParams",
    "CreateOrderParams",
    "CreateOrderResult",
    "CreateVirtualAccountParams",
    "Currency",
    "DataParams",
    "DataPlan",
    "DebitMandateParams",
    "DebitMandateResult",
    "DeleteSavedCardParams",
    "DeviceInformation",
    "DrcProvider",
    "ElectricityCustomer",
    "ElectricityParams",
    "ElectricityProvider",
    "ExchangeRate",
    "ExchangeRates",
    "ExpireVirtualAccountResult",
    "GlobalPayoutAccount",
    "GlobalPayoutResult",
    "GlobalPayoutTransaction",
    "InflowResult",
    "InitiateInflowParams",
    "InstitutionProvider",
    "Mandate",
    "MandateCreated",
    "MandateFrequency",
    "MandatePage",
    "MandateStatus",
    "Network",
    "OrderDetails",
    "OrderReferenceParams",
    "PaymentMethod",
    "RefundParams",
    "RequestSaveCardOtpParams",
    "RevokeResult",
    "SavedCard",
    "SavedCardList",
    "SavedCardOrder",
    "SplitEntry",
    "SplitRequest",
    "SubmitCardDetailsParams",
    "SubmitCardOtpParams",
    "SubmitUserOtpParams",
    "SuccessMessage",
    "Terminal",
    "TerminalPage",
    "TerminalPaymentRequest",
    "TerminalPaymentRequestParams",
    "Transaction",
    "TransactionFilters",
    "TransactionPage",
    "TransactionSource",
    "TransactionType",
    "Transfer",
    "TransferAccount",
    "UpdateMandateStatusParams",
    "UpdateMandateStatusResult",
    "UpdateSavedCardEmailParams",
    "UpdateSavedCardEmailResult",
    "UpdateVirtualAccountParams",
    "UpdateVirtualAccountResult",
    "UserSavedCards",
    "VirtualAccount",
    "VirtualAccountFilters",
    "VirtualAccountPage",
    "WalletTransferParams",
    "WebhookEvent",
]
