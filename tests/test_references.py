"""Money-moving calls attach their idempotency reference to every error."""

from __future__ import annotations

import uuid
from typing import Any

import httpx
import pytest

from nomba import APIConnectionError, APITimeoutError, NombaError, NotFoundError, Reference, ServerError

from .conftest import MockAPI, body_of, envelope, make_async_client, make_client

BANK = {"amount": 100, "accountNumber": "0123456789", "accountName": "Ada", "bankCode": "058"}
AIRTIME = {"amount": 200, "phoneNumber": "08055441122", "network": "MTN"}

FAILURES: list[tuple[str, Any, type[NombaError]]] = [
    ("timeout", httpx.ReadTimeout("slow"), APITimeoutError),
    ("connection", httpx.ConnectError("reset"), APIConnectionError),
    ("5xx", httpx.Response(502, json={"code": "502", "description": "bad gateway"}), ServerError),
]

CALLS: list[tuple[str, str, Any]] = [
    ("transfers.to_bank", "/v2/transfers/bank", lambda c, p: c.transfers.to_bank({**BANK, **p})),
    ("bills.buy_airtime", "/v2/bill/topup", lambda c, p: c.bills.buy_airtime({**AIRTIME, **p})),
]


def _is_uuid4(value: str) -> bool:
    return uuid.UUID(value).version == 4


@pytest.mark.parametrize(("name", "path", "call"), CALLS, ids=[c[0] for c in CALLS])
@pytest.mark.parametrize(("kind", "failure", "error"), FAILURES, ids=[f[0] for f in FAILURES])
def test_sync_error_carries_generated_reference(
    api: MockAPI, name: str, path: str, call: Any, kind: str, failure: Any, error: type[NombaError]
) -> None:
    api.add("POST", path, failure)
    with make_client(api) as client, pytest.raises(error) as info:
        call(client, {})
    sent = body_of(api.last())["merchantTxRef"]
    assert _is_uuid4(sent)
    assert info.value.reference == Reference("merchantTxRef", sent)
    assert api.paths().count(f"POST {path}") == 1


@pytest.mark.parametrize(("name", "path", "call"), CALLS, ids=[c[0] for c in CALLS])
@pytest.mark.parametrize(("kind", "failure", "error"), FAILURES, ids=[f[0] for f in FAILURES])
async def test_async_error_carries_generated_reference(
    api: MockAPI, name: str, path: str, call: Any, kind: str, failure: Any, error: type[NombaError]
) -> None:
    api.add("POST", path, failure)
    async with make_async_client(api) as client:
        with pytest.raises(error) as info:
            await call(client, {})
    sent = body_of(api.last())["merchantTxRef"]
    assert info.value.reference is not None
    assert info.value.reference.value == sent
    assert info.value.reference.field == "merchantTxRef"


@pytest.mark.parametrize(("name", "path", "call"), CALLS, ids=[c[0] for c in CALLS])
def test_callers_reference_is_attached(api: MockAPI, name: str, path: str, call: Any) -> None:
    api.add("POST", path, httpx.ReadTimeout("slow"))
    with make_client(api) as client, pytest.raises(APITimeoutError) as info:
        call(client, {"merchantTxRef": "payout-1042"})
    assert info.value.reference == Reference("merchantTxRef", "payout-1042")


def test_reference_survives_requery_then_retry_flow(api: MockAPI) -> None:
    api.add("POST", "/v2/transfers/bank", httpx.ReadTimeout("slow"), envelope({"status": "SUCCESS"}))
    api.add("GET", "/v1/transactions/accounts/single", httpx.Response(404, json={"code": "404", "description": "nf"}))
    with make_client(api) as client:
        with pytest.raises(APITimeoutError) as info:
            client.transfers.to_bank(dict(BANK))  # type: ignore[arg-type]
        ref = info.value.reference
        assert ref is not None
        with pytest.raises(NotFoundError) as lookup:
            client.transactions.get(merchant_tx_ref=ref.value)
        assert lookup.value.reference is None  # not a money-moving call
        result = client.transfers.to_bank({**BANK, ref.field: ref.value})  # type: ignore[typeddict-item]
    assert result["merchantTxRef"] == ref.value
    sent = [body_of(r)["merchantTxRef"] for r in api.requests if r.url.path == "/v2/transfers/bank"]
    assert sent == [ref.value, ref.value]


def test_token_failure_on_money_call_still_carries_reference(api: MockAPI) -> None:
    api.add("POST", "/v1/auth/token/issue", httpx.Response(401, json={"code": "401", "description": "bad creds"}))
    with make_client(api) as client, pytest.raises(NombaError) as info:
        client.transfers.to_wallet({"amount": 1, "receiverAccountId": "r", "merchantTxRef": "w-1"})
    assert info.value.reference == Reference("merchantTxRef", "w-1")


@pytest.mark.parametrize("use_async", [False, True])
async def test_charge_saved_card_error_carries_order_reference(api: MockAPI, use_async: bool) -> None:
    api.add("POST", "/v1/checkout/tokenized-card-payment", httpx.ConnectError("reset"))
    params: Any = {"tokenKey": "tk", "order": {"customerEmail": "a@b.c", "amount": "1.00", "currency": "NGN"}}
    if use_async:
        async with make_async_client(api) as aclient:
            with pytest.raises(APIConnectionError) as info:
                await aclient.checkout.charge_saved_card(params)
    else:
        with make_client(api) as client, pytest.raises(APIConnectionError) as info:
            client.checkout.charge_saved_card(params)
    sent = body_of(api.last())["order"]["orderReference"]
    assert info.value.reference == Reference("orderReference", sent)


def test_non_money_calls_have_no_reference(api: MockAPI) -> None:
    api.add("GET", "/v1/accounts/parent", httpx.Response(500, json={"code": "500"}))
    with make_client(api, max_retries=0) as client, pytest.raises(ServerError) as info:
        client.accounts.get_parent()
    assert info.value.reference is None
