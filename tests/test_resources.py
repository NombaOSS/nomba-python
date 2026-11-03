"""One request test per method, run against both the sync and the async client.

The sync and async surfaces are identical, so each case's ``call`` works with
either; the async run awaits the result.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest

from nomba import AsyncNomba, Nomba

from .conftest import ACCOUNT_ID, MockAPI, body_of, envelope, make_async_client, make_client

ORDER = {
    "callbackUrl": "https://merchant.example/cb",
    "customerEmail": "ada@example.com",
    "amount": "5000.00",
    "currency": "NGN",
}


@dataclass
class Case:
    id: str
    call: Callable[[Any], Any]
    method: str
    path: str
    query: dict[str, str] | None = None
    body: Any = None
    data: Any = None


CASES = [
    # accounts
    Case("accounts.get_parent", lambda c: c.accounts.get_parent(), "GET", "/v1/accounts/parent"),
    Case("accounts.get_balance", lambda c: c.accounts.get_balance(), "GET", "/v1/accounts/balance"),
    Case(
        "accounts.get_balance(sub)",
        lambda c: c.accounts.get_balance(sub_account_id="sub-1"),
        "GET",
        "/v1/accounts/sub-1/balance",
    ),
    Case(
        "accounts.get_sub_account(id)",
        lambda c: c.accounts.get_sub_account(account_id="acc-1"),
        "GET",
        "/v1/accounts/sub-account-details",
        {"accountId": "acc-1"},
    ),
    Case(
        "accounts.get_sub_account(ref)",
        lambda c: c.accounts.get_sub_account(account_ref="ref-1"),
        "GET",
        "/v1/accounts/sub-account-details",
        {"accountRef": "ref-1"},
    ),
    Case(
        "accounts.list_terminals",
        lambda c: c.accounts.list_terminals(limit=10, cursor="cur", serial_number="SN1", merchant_name="M"),
        "GET",
        "/v1/accounts/terminals",
        {"limit": "10", "cursor": "cur", "serialNumber": "SN1", "merchantName": "M"},
    ),
    Case(
        "accounts.list_terminals(sub)",
        lambda c: c.accounts.list_terminals(sub_account_id="sub-1", terminal_id="T1", terminal_label="L"),
        "GET",
        "/v1/accounts/sub-1/terminals",
        {"terminalId": "T1", "terminalLabel": "L"},
    ),
    # virtual accounts
    Case(
        "virtual_accounts.create",
        lambda c: c.virtual_accounts.create({"accountRef": "r1", "accountName": "Ada", "expectedAmount": 200}),
        "POST",
        "/v1/accounts/virtual",
        body={"accountRef": "r1", "accountName": "Ada", "expectedAmount": 200},
    ),
    Case(
        "virtual_accounts.create(sub)",
        lambda c: c.virtual_accounts.create({"accountRef": "r1", "accountName": "Ada"}, sub_account_id="sub-1"),
        "POST",
        "/v1/accounts/virtual/sub-1",
        body={"accountRef": "r1", "accountName": "Ada"},
    ),
    Case("virtual_accounts.get", lambda c: c.virtual_accounts.get("r1"), "GET", "/v1/accounts/virtual/r1"),
    Case(
        "virtual_accounts.update",
        lambda c: c.virtual_accounts.update("r1", {"accountName": "New"}),
        "PUT",
        "/v1/accounts/virtual/r1",
        body={"accountName": "New"},
    ),
    Case("virtual_accounts.expire", lambda c: c.virtual_accounts.expire("r1"), "DELETE", "/v1/accounts/virtual/r1"),
    Case(
        "virtual_accounts.list",
        lambda c: c.virtual_accounts.list({"expired": False}, limit=5, cursor="x"),
        "POST",
        "/v1/accounts/virtual/list",
        {"limit": "5", "cursor": "x"},
        {"expired": False},
    ),
    Case(
        "virtual_accounts.list(no filters)",
        lambda c: c.virtual_accounts.list(),
        "POST",
        "/v1/accounts/virtual/list",
        body={},
    ),
    # checkout
    Case(
        "checkout.create_order",
        lambda c: c.checkout.create_order({"order": ORDER, "tokenizeCard": True}),
        "POST",
        "/v1/checkout/order",
        body={"order": ORDER, "tokenizeCard": True},
    ),
    Case("checkout.get_order", lambda c: c.checkout.get_order("ord-1"), "GET", "/v1/checkout/order/ord-1"),
    Case(
        "checkout.cancel_order",
        lambda c: c.checkout.cancel_order({"orderReference": "ord-1"}),
        "POST",
        "/v1/checkout/order/cancel",
        body={"orderReference": "ord-1"},
    ),
    Case(
        "checkout.get_transaction",
        lambda c: c.checkout.get_transaction(id_type="ORDER_REFERENCE", id="ord-1"),
        "GET",
        "/v1/checkout/transaction",
        {"idType": "ORDER_REFERENCE", "id": "ord-1"},
    ),
    Case(
        "checkout.refund",
        lambda c: c.checkout.refund({"transactionId": "t1", "amount": 50}),
        "POST",
        "/v1/checkout/refund",
        body={"transactionId": "t1", "amount": 50},
    ),
    Case(
        "checkout.charge_saved_card",
        lambda c: c.checkout.charge_saved_card({"tokenKey": "tk", "order": {**ORDER, "orderReference": "sub-1"}}),
        "POST",
        "/v1/checkout/tokenized-card-payment",
        body={"tokenKey": "tk", "order": {**ORDER, "orderReference": "sub-1"}},
        data={"status": True, "orderReference": "sub-1"},
    ),
    Case(
        "checkout.list_saved_cards",
        lambda c: c.checkout.list_saved_cards(customer_email="a@b.c", page=2, limit=20, date_from="2026-01-01"),
        "GET",
        "/v1/checkout/tokenized-card-data",
        {"customerEmail": "a@b.c", "page": "2", "limit": "20", "dateFrom": "2026-01-01"},
    ),
    Case(
        "checkout.update_saved_card_email",
        lambda c: c.checkout.update_saved_card_email(
            {"tokenKey": "tk", "currentEmailAddress": "a@b.c", "newEmailAddress": "d@e.f"}
        ),
        "POST",
        "/v1/checkout/tokenized-card-data",
        body={"tokenKey": "tk", "currentEmailAddress": "a@b.c", "newEmailAddress": "d@e.f"},
    ),
    Case(
        "checkout.delete_saved_card",
        lambda c: c.checkout.delete_saved_card({"tokenKey": "tk"}),
        "DELETE",
        "/v1/checkout/tokenized-card-data",
        body={"tokenKey": "tk"},
    ),
    Case(
        "checkout.get_transfer_account",
        lambda c: c.checkout.get_transfer_account("ord-1"),
        "GET",
        "/v1/checkout/get-checkout-kta/ord-1",
    ),
    Case(
        "checkout.submit_card_details",
        lambda c: c.checkout.submit_card_details({"orderReference": "ord-1", "cardDetails": "enc", "saveCard": False}),
        "POST",
        "/v1/checkout/checkout-card-detail",
        body={"orderReference": "ord-1", "cardDetails": "enc", "saveCard": False},
    ),
    Case(
        "checkout.submit_card_otp",
        lambda c: c.checkout.submit_card_otp({"otp": "1234", "orderReference": "ord-1", "transactionId": "t1"}),
        "POST",
        "/v1/checkout/checkout-card-otp",
        body={"otp": "1234", "orderReference": "ord-1", "transactionId": "t1"},
    ),
    Case(
        "checkout.resend_otp",
        lambda c: c.checkout.resend_otp({"orderReference": "ord-1"}),
        "POST",
        "/v1/checkout/resend-otp",
        body={"orderReference": "ord-1"},
    ),
    Case(
        "checkout.confirm_transaction_receipt",
        lambda c: c.checkout.confirm_transaction_receipt({"orderReference": "ord-1"}),
        "POST",
        "/v1/checkout/confirm-transaction-receipt",
        body={"orderReference": "ord-1"},
    ),
    Case(
        "checkout.cancel_transaction",
        lambda c: c.checkout.cancel_transaction({"transactionId": "t1", "forceCancel": False}),
        "POST",
        "/v1/checkout/transaction/cancel",
        body={"transactionId": "t1", "forceCancel": False},
    ),
    Case(
        "checkout.request_save_card_otp",
        lambda c: c.checkout.request_save_card_otp({"orderReference": "ord-1", "phoneNumber": "080"}),
        "POST",
        "/v1/checkout/user-card/auth",
        body={"orderReference": "ord-1", "phoneNumber": "080"},
    ),
    Case(
        "checkout.request_saved_cards_otp",
        lambda c: c.checkout.request_saved_cards_otp({"orderReference": "ord-1"}),
        "POST",
        "/v1/checkout/user-card/saved-card/auth",
        body={"orderReference": "ord-1"},
    ),
    Case(
        "checkout.submit_user_otp",
        lambda c: c.checkout.submit_user_otp({"orderReference": "ord-1", "phoneNumber": "080", "otp": "1"}),
        "POST",
        "/v1/checkout/user-card",
        body={"orderReference": "ord-1", "phoneNumber": "080", "otp": "1"},
    ),
    Case(
        "checkout.get_saved_cards",
        lambda c: c.checkout.get_saved_cards("ord-1", otp="9999"),
        "GET",
        "/v1/checkout/user-card/ord-1",
        {"otp": "9999"},
    ),
    # transfers
    Case("transfers.list_banks", lambda c: c.transfers.list_banks(), "GET", "/v1/transfers/banks", data=[]),
    Case(
        "transfers.lookup_account",
        lambda c: c.transfers.lookup_account(account_number="0554772814", bank_code="053"),
        "POST",
        "/v1/transfers/bank/lookup",
        body={"accountNumber": "0554772814", "bankCode": "053"},
    ),
    Case(
        "transfers.to_bank",
        lambda c: c.transfers.to_bank(
            {
                "amount": 3500,
                "accountNumber": "0554772814",
                "accountName": "M A",
                "bankCode": "058",
                "merchantTxRef": "m1",
            }
        ),
        "POST",
        "/v2/transfers/bank",
        body={
            "amount": 3500,
            "accountNumber": "0554772814",
            "accountName": "M A",
            "bankCode": "058",
            "merchantTxRef": "m1",
        },
        data={"id": "x", "status": "SUCCESS", "merchantTxRef": "m1"},
    ),
    Case(
        "transfers.to_bank(sub)",
        lambda c: c.transfers.to_bank(
            {"amount": 1, "accountNumber": "1", "accountName": "A", "bankCode": "0", "merchantTxRef": "m2"},
            sub_account_id="sub-1",
        ),
        "POST",
        "/v2/transfers/bank/sub-1",
        body={"amount": 1, "accountNumber": "1", "accountName": "A", "bankCode": "0", "merchantTxRef": "m2"},
        data={"merchantTxRef": "m2"},
    ),
    Case(
        "transfers.to_wallet",
        lambda c: c.transfers.to_wallet({"amount": 5, "receiverAccountId": "r", "merchantTxRef": "m3"}),
        "POST",
        "/v2/transfers/wallet",
        body={"amount": 5, "receiverAccountId": "r", "merchantTxRef": "m3"},
        data={"merchantTxRef": "m3"},
    ),
    Case(
        "transfers.to_wallet(sub)",
        lambda c: c.transfers.to_wallet(
            {"amount": 5, "receiverAccountId": "r", "merchantTxRef": "m4"}, sub_account_id="sub-1"
        ),
        "POST",
        "/v2/transfers/wallet/sub-1",
        body={"amount": 5, "receiverAccountId": "r", "merchantTxRef": "m4"},
        data={"merchantTxRef": "m4"},
    ),
    # transactions
    Case(
        "transactions.list",
        lambda c: c.transactions.list(limit=50, date_from="2026-01-01T00:00:00Z", date_to="2026-02-01T00:00:00Z"),
        "GET",
        "/v1/transactions/accounts",
        {"limit": "50", "dateFrom": "2026-01-01T00:00:00Z", "dateTo": "2026-02-01T00:00:00Z"},
    ),
    Case(
        "transactions.list(sub)",
        lambda c: c.transactions.list(sub_account_id="sub-1", cursor="c1"),
        "GET",
        "/v1/transactions/accounts/sub-1",
        {"cursor": "c1"},
    ),
    Case(
        "transactions.filter",
        lambda c: c.transactions.filter({"status": "SUCCESS", "source": "api"}, limit=2),
        "POST",
        "/v1/transactions/accounts",
        {"limit": "2"},
        {"status": "SUCCESS", "source": "api"},
    ),
    Case(
        "transactions.filter(sub)",
        lambda c: c.transactions.filter({"merchantTxRef": "m"}, sub_account_id="sub-1"),
        "POST",
        "/v1/transactions/accounts/sub-1",
        body={"merchantTxRef": "m"},
    ),
    Case(
        "transactions.get",
        lambda c: c.transactions.get(transaction_ref="API-1"),
        "GET",
        "/v1/transactions/accounts/single",
        {"transactionRef": "API-1"},
    ),
    Case(
        "transactions.get(sub, order_id)",
        lambda c: c.transactions.get(order_id="o1", sub_account_id="sub-1"),
        "GET",
        "/v1/transactions/accounts/sub-1/single",
        {"orderId": "o1"},
    ),
    Case(
        "transactions.get(order_reference)",
        lambda c: c.transactions.get(order_reference="or1"),
        "GET",
        "/v1/transactions/accounts/single",
        {"orderReference": "or1"},
    ),
    Case(
        "transactions.list_bank_transactions",
        lambda c: c.transactions.list_bank_transactions(limit=3, cursor="z"),
        "GET",
        "/v1/transactions/bank",
        {"limit": "3", "cursor": "z"},
    ),
    Case(
        "transactions.requery",
        lambda c: c.transactions.requery("100004250929105143781234567890"),
        "GET",
        "/v1/transactions/requery/100004250929105143781234567890",
    ),
    # terminals
    Case(
        "terminals.assign",
        lambda c: c.terminals.assign({"serialNumber": "SN", "terminalLabel": "Till 1"}),
        "POST",
        "/v1/terminals/assign",
        body={"serialNumber": "SN", "terminalLabel": "Till 1"},
    ),
    Case(
        "terminals.assign(sub)",
        lambda c: c.terminals.assign({"serialNumber": "SN"}, sub_account_id="sub-1"),
        "POST",
        "/v1/terminals/assign/sub-1",
        body={"serialNumber": "SN"},
    ),
    Case(
        "terminals.unassign",
        lambda c: c.terminals.unassign({"serialNumber": "SN"}),
        "POST",
        "/v1/terminals/unassign",
        body={"serialNumber": "SN"},
    ),
    Case(
        "terminals.unassign(sub)",
        lambda c: c.terminals.unassign({"serialNumber": "SN"}, sub_account_id="sub-1"),
        "POST",
        "/v1/terminals/unassign/sub-1",
        body={"serialNumber": "SN"},
    ),
    Case(
        "terminals.send_payment_request",
        lambda c: c.terminals.send_payment_request(
            "2KUD4AKB", {"merchantTxRef": "m", "amount": 1000, "currency": "NGN"}
        ),
        "POST",
        "/v1/terminals/payment-request/2KUD4AKB",
        body={"merchantTxRef": "m", "amount": 1000, "currency": "NGN"},
    ),
    # direct debits
    Case(
        "direct_debits.create_mandate",
        lambda c: c.direct_debits.create_mandate({"customerAccountNumber": "0174534423", "amount": 100}),
        "POST",
        "/v1/direct-debits",
        body={"customerAccountNumber": "0174534423", "amount": 100},
    ),
    Case(
        "direct_debits.debit_mandate",
        lambda c: c.direct_debits.debit_mandate({"mandateId": "m1", "amount": "110.00"}),
        "POST",
        "/v1/direct-debits/debit-mandate",
        body={"mandateId": "m1", "amount": "110.00"},
    ),
    Case(
        "direct_debits.get_mandate_status",
        lambda c: c.direct_debits.get_mandate_status("m1"),
        "GET",
        "/v1/direct-debits/status",
        {"mandateId": "m1"},
    ),
    Case(
        "direct_debits.list_mandates",
        lambda c: c.direct_debits.list_mandates(
            page=1, page_size=20, from_="2026-01-01", to="2026-02-01", status="ACTIVE"
        ),
        "GET",
        "/v1/direct-debits/mandates",
        {"page": "1", "pageSize": "20", "from": "2026-01-01", "to": "2026-02-01", "status": "ACTIVE"},
    ),
    Case(
        "direct_debits.update_mandate_status",
        lambda c: c.direct_debits.update_mandate_status({"mandateId": "m1", "status": "SUSPEND"}),
        "PUT",
        "/v1/direct-debits/update-status",
        body={"mandateId": "m1", "status": "SUSPEND"},
    ),
    # bills
    Case(
        "bills.buy_airtime",
        lambda c: c.bills.buy_airtime({"amount": 200, "phoneNumber": "080", "network": "MTN", "merchantTxRef": "b1"}),
        "POST",
        "/v2/bill/topup",
        body={"amount": 200, "phoneNumber": "080", "network": "MTN", "merchantTxRef": "b1"},
        data={"merchantTxRef": "b1"},
    ),
    Case(
        "bills.buy_airtime(sub)",
        lambda c: c.bills.buy_airtime(
            {"amount": 200, "phoneNumber": "080", "network": "MTN", "merchantTxRef": "b2"}, sub_account_id="sub-1"
        ),
        "POST",
        "/v2/bill/topup/sub-1",
        body={"amount": 200, "phoneNumber": "080", "network": "MTN", "merchantTxRef": "b2"},
        data={"merchantTxRef": "b2"},
    ),
    Case(
        "bills.buy_data",
        lambda c: c.bills.buy_data(
            {"productId": "mtn47", "phoneNumber": "080", "network": "MTN", "merchantTxRef": "b3"}
        ),
        "POST",
        "/v2/bill/data",
        body={"productId": "mtn47", "phoneNumber": "080", "network": "MTN", "merchantTxRef": "b3"},
        data={"merchantTxRef": "b3"},
    ),
    Case(
        "bills.buy_data(sub)",
        lambda c: c.bills.buy_data(
            {"productId": "p", "phoneNumber": "080", "network": "GLO", "merchantTxRef": "b4"}, sub_account_id="sub-1"
        ),
        "POST",
        "/v2/bill/data/sub-1",
        body={"productId": "p", "phoneNumber": "080", "network": "GLO", "merchantTxRef": "b4"},
        data={"merchantTxRef": "b4"},
    ),
    Case("bills.list_data_plans", lambda c: c.bills.list_data_plans("MTN"), "GET", "/v1/bill/data-plan/mtn", data=[]),
    Case(
        "bills.buy_electricity",
        lambda c: c.bills.buy_electricity(
            {"disco": "jed", "customerId": "123", "amount": 1000, "meterType": "prepaid", "merchantTxRef": "b5"}
        ),
        "POST",
        "/v2/bill/electricity",
        body={"disco": "jed", "customerId": "123", "amount": 1000, "meterType": "prepaid", "merchantTxRef": "b5"},
        data={"merchantTxRef": "b5"},
    ),
    Case(
        "bills.buy_electricity(sub)",
        lambda c: c.bills.buy_electricity({"disco": "jed", "merchantTxRef": "b6"}, sub_account_id="sub-1"),
        "POST",
        "/v2/bill/electricity/sub-1",
        body={"disco": "jed", "merchantTxRef": "b6"},
        data={"merchantTxRef": "b6"},
    ),
    Case(
        "bills.list_electricity_providers",
        lambda c: c.bills.list_electricity_providers(),
        "GET",
        "/v1/bill/electricity/discos",
        data=[],
    ),
    Case(
        "bills.lookup_electricity_customer",
        lambda c: c.bills.lookup_electricity_customer(disco="jed", customer_id="123"),
        "GET",
        "/v2/bill/electricity/lookup",
        {"disco": "jed", "customerId": "123"},
    ),
    Case(
        "bills.pay_cable_tv",
        lambda c: c.bills.pay_cable_tv(
            {"cableTvType": "dstv", "customerId": "9", "amount": 19000, "merchantTxRef": "b7"}
        ),
        "POST",
        "/v2/bill/cabletv",
        body={"cableTvType": "dstv", "customerId": "9", "amount": 19000, "merchantTxRef": "b7"},
        data={"merchantTxRef": "b7"},
    ),
    Case(
        "bills.pay_cable_tv(sub)",
        lambda c: c.bills.pay_cable_tv({"cableTvType": "gotv", "merchantTxRef": "b8"}, sub_account_id="sub-1"),
        "POST",
        "/v2/bill/cabletv/sub-1",
        body={"cableTvType": "gotv", "merchantTxRef": "b8"},
        data={"merchantTxRef": "b8"},
    ),
    Case(
        "bills.list_cable_tv_plans",
        lambda c: c.bills.list_cable_tv_plans("dstv"),
        "GET",
        "/v1/bill/cableTvProduct",
        {"cableTvType": "dstv"},
        data=[],
    ),
    Case(
        "bills.lookup_cable_tv_customer",
        lambda c: c.bills.lookup_cable_tv_customer(customer_id="9", cable_tv_type="dstv"),
        "GET",
        "/v1/bill/cabletv/lookup",
        {"customerId": "9", "cableTvType": "dstv"},
        data="John Doe",
    ),
    Case(
        "bills.fund_betting",
        lambda c: c.bills.fund_betting(
            {"bettingProvider": "bet9ja", "customerId": "c", "amount": 1000, "merchantTxRef": "b9"}
        ),
        "POST",
        "/v2/bill/betting",
        body={"bettingProvider": "bet9ja", "customerId": "c", "amount": 1000, "merchantTxRef": "b9"},
        data={"merchantTxRef": "b9"},
    ),
    Case(
        "bills.fund_betting(sub)",
        lambda c: c.bills.fund_betting({"bettingProvider": "bet9ja", "merchantTxRef": "b10"}, sub_account_id="sub-1"),
        "POST",
        "/v2/bill/betting/sub-1",
        body={"bettingProvider": "bet9ja", "merchantTxRef": "b10"},
        data={"merchantTxRef": "b10"},
    ),
    Case(
        "bills.list_betting_providers",
        lambda c: c.bills.list_betting_providers(),
        "GET",
        "/v1/bill/betting/providers",
        data=[],
    ),
    Case(
        "bills.lookup_betting_customer",
        lambda c: c.bills.lookup_betting_customer(provider_id="bet9ja", customer_id="c"),
        "GET",
        "/v1/bill/betting/lookup",
        {"providerId": "bet9ja", "customerId": "c"},
        data="John Doe",
    ),
    # global payout (sandbox paths for accounts)
    Case(
        "global_payout.list_accounts",
        lambda c: c.global_payout.list_accounts(),
        "GET",
        "/v1/sandbox/global-payout/accounts",
        data=[],
    ),
    Case(
        "global_payout.get_account",
        lambda c: c.global_payout.get_account("acc-cad"),
        "GET",
        "/v1/sandbox/global-payout/accounts/acc-cad",
    ),
    Case(
        "global_payout.list_bank_providers",
        lambda c: c.global_payout.list_bank_providers(is_mobile_money=True, country_iso_code="CD"),
        "GET",
        "/v1/global-payout/bank/providers",
        {"isMobileMoney": "true", "countryIsoCode": "CD"},
        data=[],
    ),
    Case(
        "global_payout.list_bank_providers(false)",
        lambda c: c.global_payout.list_bank_providers(is_mobile_money=False),
        "GET",
        "/v1/global-payout/bank/providers",
        {"isMobileMoney": "false"},
        data=[],
    ),
    Case(
        "global_payout.get_exchange_rates",
        lambda c: c.global_payout.get_exchange_rates(from_="USD", to="CDF", region="CD"),
        "GET",
        "/v1/global-payout/exchange-rates",
        {"from": "USD", "to": "CDF", "region": "CD"},
    ),
    Case(
        "global_payout.list_payment_methods",
        lambda c: c.global_payout.list_payment_methods(destination_country_iso_code="CA", code="EFT"),
        "GET",
        "/v1/global-payout/payment-methods",
        {"destinationCountryIsoCode": "CA", "code": "EFT"},
        data=[],
    ),
    Case(
        "global_payout.get_transaction",
        lambda c: c.global_payout.get_transaction("01kj9"),
        "GET",
        "/v1/global-payout/transactions/01kj9",
    ),
    Case(
        "global_payout.authorize_exchange",
        lambda c: c.global_payout.authorize_exchange(
            {"amount": 1, "sourceCurrency": "USD", "destinationCurrency": "CDF"}
        ),
        "POST",
        "/v1/global-payout/exchange/authorize",
        body={"amount": 1, "sourceCurrency": "USD", "destinationCurrency": "CDF"},
    ),
    Case(
        "global_payout.convert_money",
        lambda c: c.global_payout.convert_money(
            {"amount": 15, "currency": "USD", "destinationCurrency": "EUR", "transactionType": "EXCHANGE"}
        ),
        "POST",
        "/v1/global-payout/money/convert",
        body={"amount": 15, "currency": "USD", "destinationCurrency": "EUR", "transactionType": "EXCHANGE"},
    ),
    Case(
        "global_payout.authorize_transfer",
        lambda c: c.global_payout.authorize_transfer({"amount": 500, "paymentMethod": "MobileMoney"}),
        "POST",
        "/v1/global-payout/transfer/authorize",
        body={"amount": 500, "paymentMethod": "MobileMoney"},
    ),
    # global collection
    Case(
        "global_collection.list_drc_providers",
        lambda c: c.global_collection.list_drc_providers(),
        "GET",
        "/v1/global-collection/drc/inflow/providers",
        data=[],
    ),
    Case(
        "global_collection.initiate_inflow",
        lambda c: c.global_collection.initiate_inflow(
            {
                "phoneNumber": "098",
                "callbackUrl": "https://x.example",
                "amount": 10,
                "currency": "CDF",
                "topupVendor": "AIRTEL",
            }
        ),
        "POST",
        "/v1/global-collection/inflow/initiate",
        body={
            "phoneNumber": "098",
            "callbackUrl": "https://x.example",
            "amount": 10,
            "currency": "CDF",
            "topupVendor": "AIRTEL",
        },
    ),
    Case(
        "global_collection.get_transaction",
        lambda c: c.global_collection.get_transaction("a822"),
        "GET",
        "/v1/global-collection/transactions/a822",
    ),
]


def _check(api: MockAPI, case: Case, result: Any) -> None:
    request = api.last()
    assert request.method == case.method
    assert request.url.path == case.path
    assert dict(request.url.params) == (case.query or {})
    assert body_of(request) == case.body
    assert request.headers["authorization"] == "Bearer access-1"
    assert request.headers["accountid"] == ACCOUNT_ID
    assert request.headers["content-type"] == "application/json"
    assert request.headers["accept"] == "application/json"
    expected = case.data if case.data is not None else {"echo": case.id}
    assert result == expected


def _data(case: Case) -> Any:
    return case.data if case.data is not None else {"echo": case.id}


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_sync_request(api: MockAPI, case: Case) -> None:
    api.add(case.method, case.path, envelope(_data(case)))
    with make_client(api) as client:
        result = case.call(client)
    _check(api, case, result)


@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
async def test_async_request(api: MockAPI, case: Case) -> None:
    api.add(case.method, case.path, envelope(_data(case)))
    async with make_async_client(api) as client:
        pending = case.call(client)
        assert inspect.isawaitable(pending)
        result = await pending
    _check(api, case, result)


def _public_methods(obj: object) -> set[str]:
    return {name for name in dir(obj) if not name.startswith("_") and callable(getattr(obj, name))}


RESOURCES = [
    "auth",
    "accounts",
    "virtual_accounts",
    "checkout",
    "transfers",
    "transactions",
    "terminals",
    "direct_debits",
    "bills",
    "global_payout",
    "global_collection",
    "webhooks",
]


def test_sync_and_async_surfaces_match() -> None:
    sync = Nomba(client_id="i", client_secret="s", account_id="a")
    asyn = AsyncNomba(client_id="i", client_secret="s", account_id="a")
    for name in RESOURCES:
        assert _public_methods(getattr(sync, name)) == _public_methods(getattr(asyn, name)), name
    sync.close()


def test_every_operation_has_a_case() -> None:
    sync = Nomba(client_id="i", client_secret="s", account_id="a")
    covered = {c.id.split("(")[0] for c in CASES}
    skip = {"auth.revoke", "webhooks.verify", "webhooks.verify_signature"}
    for name in RESOURCES:
        for method in _public_methods(getattr(sync, name)):
            full = f"{name}.{method}"
            if full in skip or "_all" in method:
                continue
            assert full in covered, full
    sync.close()


def test_production_global_payout_paths(api: MockAPI) -> None:
    api.add("GET", "/v1/global-payout/accounts", envelope([]))
    api.add("GET", "/v1/global-payout/accounts/acc", envelope({}))
    with make_client(api, environment="production", base_url="https://api.nomba.com") as client:
        client.global_payout.list_accounts()
        client.global_payout.get_account("acc")
    assert api.paths()[-2:] == ["GET /v1/global-payout/accounts", "GET /v1/global-payout/accounts/acc"]
