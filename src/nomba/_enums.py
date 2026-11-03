from __future__ import annotations

from enum import Enum

__all__ = ["TransactionStatus", "WebhookEventType"]


class TransactionStatus(str, Enum):
    """Values of ``data.status`` on outflow responses (transfers, bills, ...).

    The SDK never raises because of these; check them yourself.
    See https://developer.nomba.com/docs/api-basics/response-codes.
    """

    SUCCESS = "SUCCESS"
    """Delivered to the destination. Don't refund."""
    REFUND = "REFUND"
    """Funds returned to your Nomba wallet. Refund your customer."""
    CANCELLED = "CANCELLED"
    """Won't proceed. Contact Nomba support."""
    PAYMENT_FAILED = "PAYMENT_FAILED"
    """Debit failed and Nomba may retry. Wait for the webhook."""
    REVERSED_BY_VENDOR = "REVERSED_BY_VENDOR"
    """Nomba may retry through another vendor. Wait for the webhook."""
    PENDING_BILLING = "PENDING_BILLING"
    """Still processing. Wait for the webhook or requery."""
    PROCESSING = "PROCESSING"
    """Still processing (v1 endpoints). Wait for the webhook."""

    def __str__(self) -> str:
        return self.value


class WebhookEventType(str, Enum):
    """``event_type`` values Nomba sends to your webhook URL."""

    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_REVERSAL = "payment_reversal"
    PAYOUT_SUCCESS = "payout_success"
    PAYOUT_FAILED = "payout_failed"
    PAYOUT_REFUND = "payout_refund"

    def __str__(self) -> str:
        return self.value
