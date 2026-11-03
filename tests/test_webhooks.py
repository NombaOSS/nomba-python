from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from nomba import Nomba, WebhookEventType, WebhookVerificationError, webhooks
from nomba.webhooks import compute_signature, verify_signature

FIXTURE = (Path(__file__).parent / "fixtures" / "webhook-fixture.json").read_bytes()
KEY = "SampleSignatureKey123"
TIMESTAMP = "2025-09-29T10:51:44Z"
# Written with explicit code points so the letter case can't be mangled in
# transit: 0x71 is a lower-case "q". This is both the signature in Nomba's
# webhook docs and the value HMAC-SHA256 produces.
_REST = "30yFZDyykoymBf9+mt1wz5UAuLk57raPGPHlGzIv00="
DOCUMENTED = "\x71" + _REST
COMPUTED = DOCUMENTED
CASE_ALTERED = "\x51" + _REST  # upper-case "Q": not a valid signature


def headers(signature: str = DOCUMENTED, **extra: str) -> dict[str, str]:
    return {"nomba-signature": signature, "nomba-timestamp": TIMESTAMP, **extra}


def test_computed_signature_matches_vector() -> None:
    sig = compute_signature(json.loads(FIXTURE), TIMESTAMP, KEY)
    assert sig == COMPUTED
    assert ord(sig[0]) == 0x71


def test_documented_vector_verifies() -> None:
    event = verify_signature(FIXTURE, headers(DOCUMENTED), KEY)
    assert event["event_type"] == WebhookEventType.PAYMENT_SUCCESS
    assert event["data"]["transaction"]["transactionId"].startswith("API-VACT_TRA-")


def test_surrounding_whitespace_is_ignored() -> None:
    verify_signature(FIXTURE, headers(f"  {DOCUMENTED}\n"), KEY)


@pytest.mark.parametrize("signature", [CASE_ALTERED, DOCUMENTED.upper(), DOCUMENTED.lower()])
def test_case_altered_signature_fails(signature: str) -> None:
    assert signature != DOCUMENTED
    with pytest.raises(WebhookVerificationError, match="does not match"):
        verify_signature(FIXTURE, headers(signature), KEY)


def test_accepts_str_body_and_bytearray() -> None:
    verify_signature(FIXTURE.decode(), headers(), KEY)
    verify_signature(bytearray(FIXTURE), headers(), KEY)


def test_headers_are_case_insensitive_and_pairs_work() -> None:
    verify_signature(FIXTURE, {"Nomba-Signature": DOCUMENTED, "NOMBA-TIMESTAMP": TIMESTAMP}, KEY)
    verify_signature(FIXTURE, [(b"nomba-signature", DOCUMENTED.encode()), ("Nomba-Timestamp", TIMESTAMP)], KEY)


def test_sig_value_fallback_header() -> None:
    verify_signature(FIXTURE, {"nomba-sig-value": DOCUMENTED, "nomba-timestamp": TIMESTAMP}, KEY)


def test_wrong_key_fails() -> None:
    with pytest.raises(WebhookVerificationError, match="does not match"):
        verify_signature(FIXTURE, headers(), "WrongKey")


def test_tampered_transaction_id_fails() -> None:
    tampered = FIXTURE.replace(b"API-VACT_TRA-3C8E1", b"API-VACT_TRA-3C8E2")
    assert tampered != FIXTURE
    with pytest.raises(WebhookVerificationError, match="does not match"):
        verify_signature(tampered, headers(), KEY)


def test_tampered_timestamp_header_fails() -> None:
    with pytest.raises(WebhookVerificationError, match="does not match"):
        verify_signature(FIXTURE, {"nomba-signature": DOCUMENTED, "nomba-timestamp": "2025-09-29T10:51:45Z"}, KEY)


@pytest.mark.parametrize(
    ("hdrs", "message"),
    [
        ({"nomba-timestamp": TIMESTAMP}, "nomba-signature"),
        ({"nomba-signature": DOCUMENTED}, "nomba-timestamp"),
        ({}, "nomba-signature"),
        ({"nomba-signature": "", "nomba-timestamp": TIMESTAMP}, "nomba-signature"),
    ],
)
def test_missing_headers_fail(hdrs: dict[str, str], message: str) -> None:
    with pytest.raises(WebhookVerificationError, match=message):
        verify_signature(FIXTURE, hdrs, KEY)


def test_wrong_algorithm_fails() -> None:
    with pytest.raises(WebhookVerificationError, match="algorithm"):
        verify_signature(FIXTURE, headers(**{"nomba-signature-algorithm": "HmacSHA1"}), KEY)


def test_declared_algorithm_accepted() -> None:
    verify_signature(FIXTURE, headers(**{"Nomba-Signature-Algorithm": "HmacSHA256"}), KEY)


def test_tolerance() -> None:
    with pytest.raises(WebhookVerificationError, match="tolerance"):
        verify_signature(FIXTURE, headers(), KEY, tolerance_seconds=300)

    event = json.loads(FIXTURE)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sig = compute_signature(event, now, KEY)
    verify_signature(FIXTURE, {"nomba-signature": sig, "nomba-timestamp": now}, KEY, tolerance_seconds=300)

    future = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    sig = compute_signature(event, future, KEY)
    with pytest.raises(WebhookVerificationError, match="tolerance"):
        verify_signature(FIXTURE, {"nomba-signature": sig, "nomba-timestamp": future}, KEY, tolerance_seconds=300)


@pytest.mark.parametrize(
    "timestamp",
    [
        "yesterday",
        "51:44Z",
        "2025-09-29 10:51:44Z",
        "2025-09-29T10:51:44",
        "2025-09-29T10:51Z",
        "2025-09-29T10:51:44+0100",
        "2025-09-29T10:51:44Zjunk",
        "1759143104",
    ],
)
@pytest.mark.parametrize("tolerance", [None, 300.0])
def test_malformed_timestamp_rejected(timestamp: str, tolerance: float | None) -> None:
    event = json.loads(FIXTURE)
    sig = compute_signature(event, timestamp, KEY)  # a genuinely valid signature for it
    with pytest.raises(WebhookVerificationError, match="RFC 3339"):
        verify_signature(
            FIXTURE, {"nomba-signature": sig, "nomba-timestamp": timestamp}, KEY, tolerance_seconds=tolerance
        )


@pytest.mark.parametrize(
    "timestamp", ["2025-09-29T10:51:44.123Z", "2025-09-29T11:51:44+01:00", "2025-09-29T10:51:44-00:00"]
)
def test_rfc3339_variants_accepted(timestamp: str) -> None:
    event = json.loads(FIXTURE)
    sig = compute_signature(event, timestamp, KEY)
    verify_signature(FIXTURE, {"nomba-signature": sig, "nomba-timestamp": timestamp}, KEY)


def _old_join(event: dict[str, Any], timestamp: str) -> str:
    """The signed message as built before the hardening (no responseCode check)."""
    d = event["data"]
    m, t = d["merchant"], d["transaction"]
    fields = [event["event_type"], event["requestId"], m["userId"], m["walletId"], t["transactionId"], t["type"]]
    return ":".join([*fields, t["time"], t["responseCode"], timestamp])


def _hmac(message: str) -> str:
    return base64.b64encode(hmac.new(KEY.encode(), message.encode(), hashlib.sha256).digest()).decode()


@pytest.mark.parametrize("tolerance", [None, 300.0, 10.0**12])
def test_split_timestamp_forgery_rejected(tolerance: float | None) -> None:
    genuine = json.loads(FIXTURE)
    forged = json.loads(FIXTURE)
    forged["data"]["transaction"]["responseCode"] = ":2025-09-29T10"
    forged_ts = "51:44Z"
    # Moving the front of the timestamp into responseCode leaves the signed
    # message, and so the genuine signature, unchanged.
    assert _old_join(forged, forged_ts) == _old_join(genuine, TIMESTAMP)
    assert _hmac(_old_join(forged, forged_ts)) == DOCUMENTED
    hdrs = {"nomba-signature": DOCUMENTED, "nomba-timestamp": forged_ts}
    with pytest.raises(WebhookVerificationError, match="RFC 3339"):
        verify_signature(json.dumps(forged).encode(), hdrs, KEY, tolerance_seconds=tolerance)


def test_split_forgery_rejected_even_with_a_well_formed_timestamp() -> None:
    # Same trick, but leaving a timestamp-shaped header: caught by the responseCode check.
    forged = json.loads(FIXTURE)
    forged["data"]["transaction"]["responseCode"] = ":2025-09-29T10:51:44Z:2025"
    hdrs = {"nomba-signature": DOCUMENTED, "nomba-timestamp": "2025-09-29T10:51:44Z"}
    with pytest.raises(WebhookVerificationError, match="responseCode"):
        verify_signature(json.dumps(forged).encode(), hdrs, KEY)


def test_response_code_with_colon_rejected_even_with_valid_timestamp() -> None:
    forged = json.loads(FIXTURE)
    forged["data"]["transaction"]["responseCode"] = "00:01"
    with pytest.raises(WebhookVerificationError, match="responseCode"):
        verify_signature(json.dumps(forged).encode(), headers(), KEY)


def test_fixture_still_verifies_with_tolerance_off() -> None:
    assert verify_signature(FIXTURE, headers(), KEY)["event_type"] == "payment_success"


def test_tolerance_off_by_default() -> None:
    # The fixture's timestamp is from 2025; without a tolerance it still verifies.
    verify_signature(FIXTURE, headers(), KEY)


@pytest.mark.parametrize("body", [b"not json", b"\xff\xfe", b"[1,2]", b'"str"'])
def test_bad_body_fails(body: bytes) -> None:
    with pytest.raises(WebhookVerificationError):
        verify_signature(body, headers(), KEY)


def _signed(event: dict[str, Any]) -> tuple[bytes, dict[str, str]]:
    raw = json.dumps(event).encode()
    return raw, {"nomba-signature": "AAAA", "nomba-timestamp": TIMESTAMP}


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda e: e.pop("event_type"), "event_type"),
        (lambda e: e.pop("requestId"), "requestId"),
        (lambda e: e.pop("data"), "data object"),
        (lambda e: e["data"].pop("merchant"), "data.merchant"),
        (lambda e: e["data"].pop("transaction"), "data.transaction"),
        (lambda e: e["data"].__setitem__("transaction", "x"), "data.transaction"),
    ],
)
def test_missing_signed_fields_fail(mutate: Any, message: str) -> None:
    event = json.loads(FIXTURE)
    mutate(event)
    raw, hdrs = _signed(event)
    with pytest.raises(WebhookVerificationError, match=message):
        verify_signature(raw, hdrs, KEY)


@pytest.mark.parametrize("code", [None, "null"])
def test_null_response_code_signs_as_empty(code: str | None) -> None:
    event = json.loads(FIXTURE)
    event["data"]["transaction"]["responseCode"] = code
    assert compute_signature(event, TIMESTAMP, KEY) == COMPUTED
    del event["data"]["transaction"]["responseCode"]
    assert compute_signature(event, TIMESTAMP, KEY) == COMPUTED


def test_non_string_fields_are_stringified() -> None:
    event = json.loads(FIXTURE)
    event["data"]["transaction"]["responseCode"] = True
    a = compute_signature(event, TIMESTAMP, KEY)
    event["data"]["transaction"]["responseCode"] = "true"
    assert compute_signature(event, TIMESTAMP, KEY) == a


def test_empty_signing_key_rejected() -> None:
    with pytest.raises(WebhookVerificationError, match="signing_key"):
        verify_signature(FIXTURE, headers(), "")


def test_client_webhooks_verify() -> None:
    with Nomba(client_id="i", client_secret="s", account_id="a") as client:
        assert client.webhooks.verify(FIXTURE, headers(), KEY)["requestId"]
        assert client.webhooks.verify_signature(FIXTURE, headers(), KEY)["requestId"]


def test_event_type_constants() -> None:
    assert [e.value for e in WebhookEventType] == [
        "payment_success",
        "payment_failed",
        "payment_reversal",
        "payout_success",
        "payout_failed",
        "payout_refund",
    ]
    assert webhooks.PAYOUT_REFUND == "payout_refund"
    assert str(WebhookEventType.PAYMENT_FAILED) == "payment_failed"


def test_impossible_date_rejected_with_tolerance() -> None:
    event = json.loads(FIXTURE)
    timestamp = "2025-13-45T10:51:44Z"  # right shape, not a real date
    sig = compute_signature(event, timestamp, KEY)
    with pytest.raises(WebhookVerificationError, match="valid timestamp"):
        verify_signature(FIXTURE, {"nomba-signature": sig, "nomba-timestamp": timestamp}, KEY, tolerance_seconds=300)
