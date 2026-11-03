"""Webhook signature verification.

Usable without a client, since webhook handlers often don't hold API
credentials::

    from nomba.webhooks import verify_signature

    event = verify_signature(raw_body, request.headers, signing_key)

Always pass the **raw** request body (bytes or str) exactly as received.
Don't parse it and re-encode it before verifying.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from collections.abc import Iterable, Mapping
from typing import Any, cast

from ._enums import WebhookEventType
from .errors import WebhookVerificationError
from .tokens import parse_timestamp
from .types.webhooks import WebhookEvent

__all__ = [
    "PAYMENT_FAILED",
    "PAYMENT_REVERSAL",
    "PAYMENT_SUCCESS",
    "PAYOUT_FAILED",
    "PAYOUT_REFUND",
    "PAYOUT_SUCCESS",
    "SIGNATURE_ALGORITHM",
    "HeadersLike",
    "WebhookEventType",
    "Webhooks",
    "compute_signature",
    "verify_signature",
]

PAYMENT_SUCCESS = WebhookEventType.PAYMENT_SUCCESS.value
PAYMENT_FAILED = WebhookEventType.PAYMENT_FAILED.value
PAYMENT_REVERSAL = WebhookEventType.PAYMENT_REVERSAL.value
PAYOUT_SUCCESS = WebhookEventType.PAYOUT_SUCCESS.value
PAYOUT_FAILED = WebhookEventType.PAYOUT_FAILED.value
PAYOUT_REFUND = WebhookEventType.PAYOUT_REFUND.value

SIGNATURE_ALGORITHM = "HmacSHA256"

HeadersLike = Mapping[str, str] | Iterable[tuple[str | bytes, str | bytes]]


def _lower_headers(headers: Any) -> dict[str, str]:
    items: Iterable[Any] = headers.items() if hasattr(headers, "items") else headers
    out: dict[str, str] = {}
    for raw_key, raw_value in items:
        key = raw_key.decode("latin-1") if isinstance(raw_key, bytes) else str(raw_key)
        value = raw_value.decode("latin-1") if isinstance(raw_value, bytes) else str(raw_value)
        out[key.lower()] = value
    return out


def _field(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _signing_message(event: Mapping[str, Any], timestamp: str) -> str:
    event_type = event.get("event_type")
    request_id = event.get("requestId")
    data = event.get("data")
    if not isinstance(event_type, str) or not event_type:
        raise WebhookVerificationError("Webhook body has no event_type")
    if not isinstance(request_id, str) or not request_id:
        raise WebhookVerificationError("Webhook body has no requestId")
    if not isinstance(data, Mapping):
        raise WebhookVerificationError("Webhook body has no data object")
    merchant = data.get("merchant")
    transaction = data.get("transaction")
    if not isinstance(merchant, Mapping):
        raise WebhookVerificationError("Webhook body has no data.merchant object")
    if not isinstance(transaction, Mapping):
        raise WebhookVerificationError("Webhook body has no data.transaction object")
    response_code = _field(transaction.get("responseCode"))
    if response_code == "null":
        response_code = ""
    parts = [
        event_type,
        request_id,
        _field(merchant.get("userId")),
        _field(merchant.get("walletId")),
        _field(transaction.get("transactionId")),
        _field(transaction.get("type")),
        _field(transaction.get("time")),
        response_code,
        timestamp,
    ]
    return ":".join(parts)


def compute_signature(event: Mapping[str, Any], timestamp: str, signing_key: str) -> str:
    """The base64 HMAC-SHA256 signature Nomba sends for ``event`` and ``timestamp``.

    Useful for testing your webhook handler.
    """
    message = _signing_message(event, timestamp)
    digest = hmac.new(signing_key.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def verify_signature(
    raw_body: str | bytes | bytearray,
    headers: HeadersLike,
    signing_key: str,
    *,
    tolerance_seconds: float | None = None,
) -> WebhookEvent:
    """Verify a Nomba webhook and return the parsed event.

    Reads ``nomba-signature`` (or ``nomba-sig-value``) and ``nomba-timestamp``
    (header names are case-insensitive). If ``tolerance_seconds`` is set, the
    timestamp must be within that many seconds of now, which limits replays.

    Raises :class:`~nomba.errors.WebhookVerificationError` if anything is wrong.
    """
    if not isinstance(signing_key, str) or not signing_key:
        raise WebhookVerificationError("signing_key is required")
    lowered = _lower_headers(headers)
    signature = lowered.get("nomba-signature") or lowered.get("nomba-sig-value")
    timestamp = lowered.get("nomba-timestamp")
    if not signature:
        raise WebhookVerificationError("Missing nomba-signature header")
    if not timestamp:
        raise WebhookVerificationError("Missing nomba-timestamp header")
    algorithm = lowered.get("nomba-signature-algorithm")
    if algorithm is not None and algorithm.strip().lower() != SIGNATURE_ALGORITHM.lower():
        raise WebhookVerificationError(f"Unsupported signature algorithm {algorithm!r}")

    if tolerance_seconds is not None:
        try:
            sent_at = parse_timestamp(timestamp).timestamp()
        except ValueError:
            raise WebhookVerificationError("nomba-timestamp is not a valid timestamp") from None
        if abs(time.time() - sent_at) > tolerance_seconds:
            raise WebhookVerificationError("Webhook timestamp is outside the allowed tolerance")

    try:
        text = raw_body.decode("utf-8") if isinstance(raw_body, (bytes, bytearray)) else raw_body
        event = json.loads(text)
    except (UnicodeDecodeError, ValueError):
        raise WebhookVerificationError("Webhook body is not valid JSON") from None
    if not isinstance(event, dict):
        raise WebhookVerificationError("Webhook body is not a JSON object")

    expected = compute_signature(event, timestamp, signing_key)
    # Nomba's reference implementation compares case-insensitively, and its
    # documented sample differs from the computed value only in letter case.
    if not hmac.compare_digest(expected.lower().encode(), signature.strip().lower().encode()):
        raise WebhookVerificationError("Webhook signature does not match")
    return cast(WebhookEvent, event)


class Webhooks:
    """``client.webhooks``: the same verification, reachable from a client."""

    def verify(
        self,
        raw_body: str | bytes | bytearray,
        headers: HeadersLike,
        signing_key: str,
        *,
        tolerance_seconds: float | None = None,
    ) -> WebhookEvent:
        """See :func:`verify_signature`."""
        return verify_signature(raw_body, headers, signing_key, tolerance_seconds=tolerance_seconds)

    verify_signature = staticmethod(verify_signature)
