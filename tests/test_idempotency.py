from __future__ import annotations

import uuid
from typing import Any

import pytest

from nomba import TransactionStatus, ValidationError

from .conftest import MockAPI, body_of, envelope, make_async_client, make_client

BANK = {"amount": 100, "accountNumber": "0123456789", "accountName": "Ada", "bankCode": "058"}


def _is_uuid4(value: Any) -> bool:
    return isinstance(value, str) and uuid.UUID(value).version == 4


@pytest.mark.parametrize(
    ("call", "path"),
    [
        (lambda c: c.transfers.to_bank(dict(BANK)), "/v2/transfers/bank"),
        (lambda c: c.transfers.to_wallet({"amount": 1, "receiverAccountId": "r"}), "/v2/transfers/wallet"),
        (lambda c: c.bills.buy_airtime({"amount": 1, "phoneNumber": "080", "network": "MTN"}), "/v2/bill/topup"),
        (lambda c: c.bills.buy_data({"productId": "p", "phoneNumber": "080", "network": "MTN"}), "/v2/bill/data"),
        (lambda c: c.bills.buy_electricity({"disco": "jed"}), "/v2/bill/electricity"),
        (lambda c: c.bills.pay_cable_tv({"cableTvType": "dstv"}), "/v2/bill/cabletv"),
        (lambda c: c.bills.fund_betting({"bettingProvider": "bet9ja"}), "/v2/bill/betting"),
    ],
)
def test_generates_merchant_tx_ref_and_returns_it(api: MockAPI, call: Any, path: str) -> None:
    api.add("POST", path, envelope({"id": "x", "status": "SUCCESS"}))
    with make_client(api) as client:
        result = call(client)
    sent = body_of(api.last())["merchantTxRef"]
    assert _is_uuid4(sent)
    assert result["merchantTxRef"] == sent
    assert result["status"] == TransactionStatus.SUCCESS


def test_each_call_gets_a_new_reference(api: MockAPI) -> None:
    api.add("POST", "/v2/transfers/bank", envelope({}))
    with make_client(api) as client:
        a = client.transfers.to_bank(dict(BANK))  # type: ignore[arg-type]
        b = client.transfers.to_bank(dict(BANK))  # type: ignore[arg-type]
    assert a["merchantTxRef"] != b["merchantTxRef"]


def test_keeps_callers_reference_and_does_not_mutate_params(api: MockAPI) -> None:
    api.add("POST", "/v2/transfers/bank", envelope({"merchantTxRef": "mine"}))
    params = {**BANK, "merchantTxRef": "mine"}
    with make_client(api) as client:
        result = client.transfers.to_bank(params)  # type: ignore[arg-type]
    assert body_of(api.last())["merchantTxRef"] == "mine"
    assert result["merchantTxRef"] == "mine"

    params_without = dict(BANK)
    with make_client(api) as client:
        client.transfers.to_bank(params_without)  # type: ignore[arg-type]
    assert "merchantTxRef" not in params_without


def test_empty_reference_is_replaced(api: MockAPI) -> None:
    api.add("POST", "/v2/transfers/bank", envelope({}))
    with make_client(api) as client:
        client.transfers.to_bank({**BANK, "merchantTxRef": ""})  # type: ignore[typeddict-item]
    assert _is_uuid4(body_of(api.last())["merchantTxRef"])


def test_response_reference_wins_when_present(api: MockAPI) -> None:
    api.add("POST", "/v2/transfers/bank", envelope({"merchantTxRef": "from-nomba"}))
    with make_client(api) as client:
        result = client.transfers.to_bank(dict(BANK))  # type: ignore[arg-type]
    assert result["merchantTxRef"] == "from-nomba"


def test_non_dict_data_left_alone(api: MockAPI) -> None:
    api.add("POST", "/v2/bill/topup", envelope(None))
    with make_client(api) as client:
        assert client.bills.buy_airtime({"amount": 1, "phoneNumber": "080", "network": "MTN"}) is None


ORDER = {"customerEmail": "ada@example.com", "amount": "5000.00", "currency": "NGN"}


def test_charge_saved_card_generates_order_reference(api: MockAPI) -> None:
    api.add("POST", "/v1/checkout/tokenized-card-payment", envelope({"status": True, "otpRequired": False}))
    params = {"tokenKey": "tk", "order": dict(ORDER)}
    with make_client(api) as client:
        result = client.checkout.charge_saved_card(params)  # type: ignore[arg-type]
    sent = body_of(api.last())
    ref = sent["order"]["orderReference"]
    assert _is_uuid4(ref)
    assert "merchantTxRef" not in sent
    assert result["orderReference"] == ref
    assert "merchantTxRef" not in result
    assert "orderReference" not in params["order"]


def test_charge_saved_card_keeps_callers_order_reference(api: MockAPI) -> None:
    api.add("POST", "/v1/checkout/tokenized-card-payment", envelope({"status": True}))
    with make_client(api) as client:
        result = client.checkout.charge_saved_card({"tokenKey": "tk", "order": {**ORDER, "orderReference": "sub-1"}})  # type: ignore[typeddict-item]
    assert body_of(api.last())["order"]["orderReference"] == "sub-1"
    assert result["orderReference"] == "sub-1"


def test_charge_saved_card_without_order_is_sent_as_is(api: MockAPI) -> None:
    api.add("POST", "/v1/checkout/tokenized-card-payment", envelope({"status": False}))
    with make_client(api) as client:
        client.checkout.charge_saved_card({"tokenKey": "tk"})  # type: ignore[typeddict-item]
    assert body_of(api.last()) == {"tokenKey": "tk"}


def test_charge_saved_card_rejects_non_dict_order(api: MockAPI) -> None:
    with make_client(api) as client, pytest.raises(ValidationError):
        client.checkout.charge_saved_card({"tokenKey": "tk", "order": "nope"})  # type: ignore[typeddict-item]
    assert api.requests == []


async def test_async_generation(api: MockAPI) -> None:
    api.add("POST", "/v2/transfers/bank", envelope({}))
    async with make_async_client(api) as client:
        result = await client.transfers.to_bank(dict(BANK))  # type: ignore[arg-type]
    assert _is_uuid4(result["merchantTxRef"])


def test_transaction_status_values() -> None:
    assert {s.value for s in TransactionStatus} == {
        "SUCCESS",
        "REFUND",
        "CANCELLED",
        "PAYMENT_FAILED",
        "REVERSED_BY_VENDOR",
        "PENDING_BILLING",
        "PROCESSING",
    }
    assert str(TransactionStatus.REFUND) == "REFUND"
    assert TransactionStatus("PENDING_BILLING") is TransactionStatus.PENDING_BILLING
