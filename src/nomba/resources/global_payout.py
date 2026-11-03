from __future__ import annotations

from .._core import Request, path, require
from ..types.global_payout import (
    AuthorizeExchangeParams,
    AuthorizeTransferParams,
    ConversionQuote,
    ConvertMoneyParams,
    ExchangeRates,
    GlobalPayoutAccount,
    GlobalPayoutResult,
    GlobalPayoutTransaction,
    InstitutionProvider,
    PaymentMethod,
)
from ._base import AsyncResource, SyncResource


def _accounts_base(sandbox: bool) -> str:
    # Nomba serves the account endpoints under a separate path in sandbox.
    return "/v1/sandbox/global-payout/accounts" if sandbox else "/v1/global-payout/accounts"


def _list_accounts(sandbox: bool) -> Request[list[GlobalPayoutAccount]]:
    return Request("GET", _accounts_base(sandbox))


def _get_account(sandbox: bool, account_id: str) -> Request[GlobalPayoutAccount]:
    return Request("GET", path(_accounts_base(sandbox) + "/{}", account_id))


def _list_bank_providers(
    is_mobile_money: bool | None, country_iso_code: str | None
) -> Request[list[InstitutionProvider]]:
    query = {"isMobileMoney": is_mobile_money, "countryIsoCode": country_iso_code}
    return Request("GET", "/v1/global-payout/bank/providers", query=query)


def _get_exchange_rates(from_: str, to: str, region: str | None) -> Request[ExchangeRates]:
    require(from_, "from_")
    require(to, "to")
    return Request("GET", "/v1/global-payout/exchange-rates", query={"from": from_, "to": to, "region": region})


def _list_payment_methods(
    destination_country_iso_code: str | None,
    destination_currency: str | None,
    code: str | None,
    name: str | None,
) -> Request[list[PaymentMethod]]:
    query = {
        "destinationCountryIsoCode": destination_country_iso_code,
        "destinationCurrency": destination_currency,
        "code": code,
        "name": name,
    }
    return Request("GET", "/v1/global-payout/payment-methods", query=query)


def _get_transaction(transaction_id: str) -> Request[GlobalPayoutTransaction]:
    return Request("GET", path("/v1/global-payout/transactions/{}", transaction_id))


def _authorize_exchange(params: AuthorizeExchangeParams) -> Request[GlobalPayoutResult]:
    return Request("POST", "/v1/global-payout/exchange/authorize", body=dict(params))


def _convert_money(params: ConvertMoneyParams) -> Request[ConversionQuote]:
    return Request("POST", "/v1/global-payout/money/convert", body=dict(params))


def _authorize_transfer(params: AuthorizeTransferParams) -> Request[GlobalPayoutResult]:
    return Request("POST", "/v1/global-payout/transfer/authorize", body=dict(params))


class GlobalPayout(SyncResource):
    def list_accounts(self) -> list[GlobalPayoutAccount]:
        """Your currency wallets and balances (sandbox uses Nomba's sandbox path)."""
        return self._client._request(_list_accounts(self._client._config.is_sandbox))

    def get_account(self, account_id: str) -> GlobalPayoutAccount:
        """One currency wallet."""
        return self._client._request(_get_account(self._client._config.is_sandbox, account_id))

    def list_bank_providers(
        self, *, is_mobile_money: bool | None = None, country_iso_code: str | None = None
    ) -> list[InstitutionProvider]:
        """Banks or mobile money providers for a destination country."""
        return self._client._request(_list_bank_providers(is_mobile_money, country_iso_code))

    def get_exchange_rates(self, *, from_: str, to: str, region: str | None = None) -> ExchangeRates:
        """Latest rates for a currency pair. ``from_`` is sent as ``from``."""
        return self._client._request(_get_exchange_rates(from_, to, region))

    def list_payment_methods(
        self,
        *,
        destination_country_iso_code: str | None = None,
        destination_currency: str | None = None,
        code: str | None = None,
        name: str | None = None,
    ) -> list[PaymentMethod]:
        """Supported payout methods and their required fields."""
        return self._client._request(
            _list_payment_methods(destination_country_iso_code, destination_currency, code, name)
        )

    def get_transaction(self, transaction_id: str) -> GlobalPayoutTransaction:
        """Status of a Global Payout transaction."""
        return self._client._request(_get_transaction(transaction_id))

    def authorize_exchange(self, params: AuthorizeExchangeParams) -> GlobalPayoutResult:
        """Move funds between your own wallets in different currencies. Never retried automatically."""
        return self._client._request(_authorize_exchange(params))

    def convert_money(self, params: ConvertMoneyParams) -> ConversionQuote:
        """Quote a conversion and lock a rate."""
        return self._client._request(_convert_money(params))

    def authorize_transfer(self, params: AuthorizeTransferParams) -> GlobalPayoutResult:
        """Send a cross-border transfer. Never retried automatically."""
        return self._client._request(_authorize_transfer(params))


class AsyncGlobalPayout(AsyncResource):
    async def list_accounts(self) -> list[GlobalPayoutAccount]:
        """Your currency wallets and balances (sandbox uses Nomba's sandbox path)."""
        return await self._client._request(_list_accounts(self._client._config.is_sandbox))

    async def get_account(self, account_id: str) -> GlobalPayoutAccount:
        """One currency wallet."""
        return await self._client._request(_get_account(self._client._config.is_sandbox, account_id))

    async def list_bank_providers(
        self, *, is_mobile_money: bool | None = None, country_iso_code: str | None = None
    ) -> list[InstitutionProvider]:
        """Banks or mobile money providers for a destination country."""
        return await self._client._request(_list_bank_providers(is_mobile_money, country_iso_code))

    async def get_exchange_rates(self, *, from_: str, to: str, region: str | None = None) -> ExchangeRates:
        """Latest rates for a currency pair. ``from_`` is sent as ``from``."""
        return await self._client._request(_get_exchange_rates(from_, to, region))

    async def list_payment_methods(
        self,
        *,
        destination_country_iso_code: str | None = None,
        destination_currency: str | None = None,
        code: str | None = None,
        name: str | None = None,
    ) -> list[PaymentMethod]:
        """Supported payout methods and their required fields."""
        return await self._client._request(
            _list_payment_methods(destination_country_iso_code, destination_currency, code, name)
        )

    async def get_transaction(self, transaction_id: str) -> GlobalPayoutTransaction:
        """Status of a Global Payout transaction."""
        return await self._client._request(_get_transaction(transaction_id))

    async def authorize_exchange(self, params: AuthorizeExchangeParams) -> GlobalPayoutResult:
        """Move funds between your own wallets in different currencies. Never retried automatically."""
        return await self._client._request(_authorize_exchange(params))

    async def convert_money(self, params: ConvertMoneyParams) -> ConversionQuote:
        """Quote a conversion and lock a rate."""
        return await self._client._request(_convert_money(params))

    async def authorize_transfer(self, params: AuthorizeTransferParams) -> GlobalPayoutResult:
        """Send a cross-border transfer. Never retried automatically."""
        return await self._client._request(_authorize_transfer(params))
