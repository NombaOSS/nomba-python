from __future__ import annotations

from typing import Any, Literal

from .._core import Request, add_reference, new_reference, path, require
from ..errors import ValidationError
from ..types.checkout import (
    CancelOrderParams,
    CancelTransactionParams,
    CardDetailsResult,
    CardOtpResult,
    ChargeSavedCardParams,
    ChargeSavedCardResult,
    CheckoutTransaction,
    ConfirmTransactionReceiptResult,
    CreateOrderParams,
    CreateOrderResult,
    DeleteSavedCardParams,
    OrderDetails,
    OrderReferenceParams,
    RefundParams,
    RequestSaveCardOtpParams,
    SavedCardList,
    SubmitCardDetailsParams,
    SubmitCardOtpParams,
    SubmitUserOtpParams,
    SuccessMessage,
    TransferAccount,
    UpdateSavedCardEmailParams,
    UpdateSavedCardEmailResult,
    UserSavedCards,
)
from ._base import AsyncResource, SyncResource

IdType = Literal["ORDER_ID", "ORDER_REFERENCE"]


def _create_order(params: CreateOrderParams) -> Request[CreateOrderResult]:
    return Request("POST", "/v1/checkout/order", body=dict(params))


def _cancel_order(params: CancelOrderParams) -> Request[SuccessMessage]:
    return Request("POST", "/v1/checkout/order/cancel", body=dict(params))


def _refund(params: RefundParams) -> Request[SuccessMessage]:
    return Request("POST", "/v1/checkout/refund", body=dict(params))


def _update_saved_card_email(params: UpdateSavedCardEmailParams) -> Request[UpdateSavedCardEmailResult]:
    return Request("POST", "/v1/checkout/tokenized-card-data", body=dict(params))


def _submit_card_details(params: SubmitCardDetailsParams) -> Request[CardDetailsResult]:
    return Request("POST", "/v1/checkout/checkout-card-detail", body=dict(params))


def _submit_card_otp(params: SubmitCardOtpParams) -> Request[CardOtpResult]:
    return Request("POST", "/v1/checkout/checkout-card-otp", body=dict(params))


def _resend_otp(params: OrderReferenceParams) -> Request[SuccessMessage]:
    return Request("POST", "/v1/checkout/resend-otp", body=dict(params))


def _confirm_transaction_receipt(params: OrderReferenceParams) -> Request[ConfirmTransactionReceiptResult]:
    return Request("POST", "/v1/checkout/confirm-transaction-receipt", body=dict(params))


def _cancel_transaction(params: CancelTransactionParams) -> Request[SuccessMessage]:
    return Request("POST", "/v1/checkout/transaction/cancel", body=dict(params))


def _request_save_card_otp(params: RequestSaveCardOtpParams) -> Request[SuccessMessage]:
    return Request("POST", "/v1/checkout/user-card/auth", body=dict(params))


def _request_saved_cards_otp(params: OrderReferenceParams) -> Request[SuccessMessage]:
    return Request("POST", "/v1/checkout/user-card/saved-card/auth", body=dict(params))


def _submit_user_otp(params: SubmitUserOtpParams) -> Request[SuccessMessage]:
    return Request("POST", "/v1/checkout/user-card", body=dict(params))


def _get_order(order_reference: str) -> Request[OrderDetails]:
    return Request("GET", path("/v1/checkout/order/{}", order_reference))


def _get_transaction(id_type: IdType, id: str) -> Request[CheckoutTransaction]:  # noqa: A002
    require(id_type, "id_type")
    require(id, "id")
    return Request("GET", "/v1/checkout/transaction", query={"idType": id_type, "id": id})


def _charge_saved_card(params: ChargeSavedCardParams) -> Request[ChargeSavedCardResult]:
    # This endpoint has no merchantTxRef; order.orderReference is its idempotency
    # key (Nomba never charges the same orderReference twice), so generate that.
    body: dict[str, Any] = dict(params)
    order = body.get("order")
    if order is None:
        return Request("POST", "/v1/checkout/tokenized-card-payment", body=body)
    if not isinstance(order, dict):
        raise ValidationError("order must be a dict")
    order = dict(order)
    ref = order.get("orderReference")
    if not isinstance(ref, str) or not ref:
        ref = new_reference()
        order["orderReference"] = ref
    body["order"] = order
    return Request(
        "POST",
        "/v1/checkout/tokenized-card-payment",
        body=body,
        postprocess=add_reference("orderReference", ref),
    )


def _list_saved_cards(
    customer_email: str | None, date_from: str | None, date_to: str | None, page: int | None, limit: int | None
) -> Request[SavedCardList]:
    query = {"customerEmail": customer_email, "dateFrom": date_from, "dateTo": date_to, "page": page, "limit": limit}
    return Request("GET", "/v1/checkout/tokenized-card-data", query=query)


def _delete_saved_card(params: DeleteSavedCardParams) -> Request[SuccessMessage]:
    # DELETE with a JSON body: the core always sends Request.body.
    return Request("DELETE", "/v1/checkout/tokenized-card-data", body=dict(params))


def _get_transfer_account(order_reference: str) -> Request[TransferAccount]:
    return Request("GET", path("/v1/checkout/get-checkout-kta/{}", order_reference))


def _get_saved_cards(order_reference: str, otp: str) -> Request[UserSavedCards]:
    require(otp, "otp")
    return Request("GET", path("/v1/checkout/user-card/{}", order_reference), query={"otp": otp})


class Checkout(SyncResource):
    """Online checkout: hosted orders, saved cards and the card/OTP flow."""

    def create_order(self, params: CreateOrderParams) -> CreateOrderResult:
        """Create a checkout order and get the hosted ``checkoutLink``."""
        return self._client._request(_create_order(params))

    def get_order(self, order_reference: str) -> OrderDetails:
        return self._client._request(_get_order(order_reference))

    def cancel_order(self, params: CancelOrderParams) -> SuccessMessage:
        return self._client._request(_cancel_order(params))

    def get_transaction(self, *, id_type: IdType, id: str) -> CheckoutTransaction:  # noqa: A002
        """Look up a checkout transaction by order ID or order reference."""
        return self._client._request(_get_transaction(id_type, id))

    def refund(self, params: RefundParams) -> SuccessMessage:
        """Refund a checkout transaction. Never retried automatically."""
        return self._client._request(_refund(params))

    def charge_saved_card(self, params: ChargeSavedCardParams) -> ChargeSavedCardResult:
        """Charge a saved card by ``tokenKey``. Never retried automatically.

        ``order.orderReference`` is the idempotency key: if you leave it out, a
        UUID v4 is generated and returned as ``result["orderReference"]``.
        Check ``status`` and ``otpRequired`` to see what happened.
        """
        return self._client._request(_charge_saved_card(params))

    def list_saved_cards(
        self,
        *,
        customer_email: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> SavedCardList:
        return self._client._request(_list_saved_cards(customer_email, date_from, date_to, page, limit))

    def update_saved_card_email(self, params: UpdateSavedCardEmailParams) -> UpdateSavedCardEmailResult:
        return self._client._request(_update_saved_card_email(params))

    def delete_saved_card(self, params: DeleteSavedCardParams) -> SuccessMessage:
        return self._client._request(_delete_saved_card(params))

    def get_transfer_account(self, order_reference: str) -> TransferAccount:
        """The bank account a customer can pay an order into by transfer."""
        return self._client._request(_get_transfer_account(order_reference))

    def submit_card_details(self, params: SubmitCardDetailsParams) -> CardDetailsResult:
        return self._client._request(_submit_card_details(params))

    def submit_card_otp(self, params: SubmitCardOtpParams) -> CardOtpResult:
        return self._client._request(_submit_card_otp(params))

    def resend_otp(self, params: OrderReferenceParams) -> SuccessMessage:
        return self._client._request(_resend_otp(params))

    def confirm_transaction_receipt(self, params: OrderReferenceParams) -> ConfirmTransactionReceiptResult:
        return self._client._request(_confirm_transaction_receipt(params))

    def cancel_transaction(self, params: CancelTransactionParams) -> SuccessMessage:
        return self._client._request(_cancel_transaction(params))

    def request_save_card_otp(self, params: RequestSaveCardOtpParams) -> SuccessMessage:
        return self._client._request(_request_save_card_otp(params))

    def request_saved_cards_otp(self, params: OrderReferenceParams) -> SuccessMessage:
        return self._client._request(_request_saved_cards_otp(params))

    def submit_user_otp(self, params: SubmitUserOtpParams) -> SuccessMessage:
        return self._client._request(_submit_user_otp(params))

    def get_saved_cards(self, order_reference: str, *, otp: str) -> UserSavedCards:
        return self._client._request(_get_saved_cards(order_reference, otp))


class AsyncCheckout(AsyncResource):
    """Online checkout (async)."""

    async def create_order(self, params: CreateOrderParams) -> CreateOrderResult:
        return await self._client._request(_create_order(params))

    async def get_order(self, order_reference: str) -> OrderDetails:
        return await self._client._request(_get_order(order_reference))

    async def cancel_order(self, params: CancelOrderParams) -> SuccessMessage:
        return await self._client._request(_cancel_order(params))

    async def get_transaction(self, *, id_type: IdType, id: str) -> CheckoutTransaction:  # noqa: A002
        return await self._client._request(_get_transaction(id_type, id))

    async def refund(self, params: RefundParams) -> SuccessMessage:
        return await self._client._request(_refund(params))

    async def charge_saved_card(self, params: ChargeSavedCardParams) -> ChargeSavedCardResult:
        return await self._client._request(_charge_saved_card(params))

    async def list_saved_cards(
        self,
        *,
        customer_email: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> SavedCardList:
        return await self._client._request(_list_saved_cards(customer_email, date_from, date_to, page, limit))

    async def update_saved_card_email(self, params: UpdateSavedCardEmailParams) -> UpdateSavedCardEmailResult:
        return await self._client._request(_update_saved_card_email(params))

    async def delete_saved_card(self, params: DeleteSavedCardParams) -> SuccessMessage:
        return await self._client._request(_delete_saved_card(params))

    async def get_transfer_account(self, order_reference: str) -> TransferAccount:
        return await self._client._request(_get_transfer_account(order_reference))

    async def submit_card_details(self, params: SubmitCardDetailsParams) -> CardDetailsResult:
        return await self._client._request(_submit_card_details(params))

    async def submit_card_otp(self, params: SubmitCardOtpParams) -> CardOtpResult:
        return await self._client._request(_submit_card_otp(params))

    async def resend_otp(self, params: OrderReferenceParams) -> SuccessMessage:
        return await self._client._request(_resend_otp(params))

    async def confirm_transaction_receipt(self, params: OrderReferenceParams) -> ConfirmTransactionReceiptResult:
        return await self._client._request(_confirm_transaction_receipt(params))

    async def cancel_transaction(self, params: CancelTransactionParams) -> SuccessMessage:
        return await self._client._request(_cancel_transaction(params))

    async def request_save_card_otp(self, params: RequestSaveCardOtpParams) -> SuccessMessage:
        return await self._client._request(_request_save_card_otp(params))

    async def request_saved_cards_otp(self, params: OrderReferenceParams) -> SuccessMessage:
        return await self._client._request(_request_saved_cards_otp(params))

    async def submit_user_otp(self, params: SubmitUserOtpParams) -> SuccessMessage:
        return await self._client._request(_submit_user_otp(params))

    async def get_saved_cards(self, order_reference: str, *, otp: str) -> UserSavedCards:
        return await self._client._request(_get_saved_cards(order_reference, otp))
