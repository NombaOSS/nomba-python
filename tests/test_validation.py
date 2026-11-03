from __future__ import annotations

from typing import Any

import pytest

from nomba import ValidationError
from nomba._core import clean_query

from .conftest import MockAPI, envelope, make_client

BAD_SEGMENTS: list[Any] = ["", "   ", ".", "..", "a/b", "../accounts/parent", "a\\b", 123, None]


PATH_CALLS: list[tuple[str, Any]] = [
    ("virtual_accounts.get", lambda c, v: c.virtual_accounts.get(v)),
    ("virtual_accounts.expire", lambda c, v: c.virtual_accounts.expire(v)),
    ("accounts.get_balance(sub)", lambda c, v: c.accounts.get_balance(sub_account_id=v)),
    (
        "transfers.to_bank(sub)",
        lambda c, v: c.transfers.to_bank(
            {"amount": 1, "accountNumber": "1", "accountName": "a", "bankCode": "1"}, sub_account_id=v
        ),
    ),
    ("transactions.requery", lambda c, v: c.transactions.requery(v)),
    ("checkout.get_order", lambda c, v: c.checkout.get_order(v)),
    (
        "terminals.send_payment_request",
        lambda c, v: c.terminals.send_payment_request(v, {"merchantTxRef": "m", "amount": 1, "currency": "NGN"}),
    ),
    ("global_payout.get_account", lambda c, v: c.global_payout.get_account(v)),
    ("bills.list_data_plans", lambda c, v: c.bills.list_data_plans(v)),
]


@pytest.mark.parametrize("value", BAD_SEGMENTS)
@pytest.mark.parametrize(("name", "call"), PATH_CALLS, ids=[n for n, _ in PATH_CALLS])
def test_bad_path_params_rejected_before_sending(api: MockAPI, name: str, call: Any, value: Any) -> None:
    if value is None and "(sub)" in name:
        pytest.skip("None means 'parent account' for sub_account_id")
    with make_client(api) as client, pytest.raises(ValidationError) as info:
        call(client, value)
    assert info.value.http_status is None
    assert api.requests == []


def test_path_params_are_url_encoded(api: MockAPI) -> None:
    api.add("GET", "/v1/accounts/virtual/a b?c#d%e", envelope({}))
    with make_client(api) as client:
        client.virtual_accounts.get("a b?c#d%e")
    raw = api.last().url.raw_path.decode()
    assert raw == "/v1/accounts/virtual/a%20b%3Fc%23d%25e"


def test_dotted_segment_inside_value_allowed(api: MockAPI) -> None:
    api.add("GET", "/v1/accounts/virtual/inv.2026..01", envelope({}))
    with make_client(api) as client:
        client.virtual_accounts.get("inv.2026..01")


@pytest.mark.parametrize("limit", [0, 51, -1, True, 2.5])
def test_limit_validated(api: MockAPI, limit: Any) -> None:
    with make_client(api) as client:
        with pytest.raises(ValidationError, match="limit"):
            client.transactions.list(limit=limit)
        with pytest.raises(ValidationError, match="limit"):
            client.transactions.list_all(limit=limit)
    assert api.requests == []


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.accounts.get_sub_account(),
        lambda c: c.accounts.get_sub_account(account_id="a", account_ref="b"),
        lambda c: c.transactions.get(),
        lambda c: c.transactions.get(transaction_ref="a", merchant_tx_ref="b"),
        lambda c: c.transfers.lookup_account(account_number="", bank_code="058"),
        lambda c: c.bills.lookup_electricity_customer(disco="jed", customer_id=" "),
        lambda c: c.checkout.get_saved_cards("ord", otp=""),
        lambda c: c.direct_debits.get_mandate_status(""),
        lambda c: c.global_payout.get_exchange_rates(from_="", to="NGN"),
        lambda c: c.checkout.get_transaction(id_type="ORDER_ID", id=""),
    ],
)
def test_required_arguments(api: MockAPI, call: Any) -> None:
    with make_client(api) as client, pytest.raises(ValidationError):
        call(client)
    assert api.requests == []


def test_clean_query() -> None:
    assert clean_query({"a": None, "b": True, "c": False, "d": 5, "e": "x"}) == {
        "b": "true",
        "c": "false",
        "d": "5",
        "e": "x",
    }
