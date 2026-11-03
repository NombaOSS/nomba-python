from __future__ import annotations

from .._core import Request, require, sub_account_path, with_reference
from ..types.transfers import Bank, BankAccountLookup, BankTransferParams, Transfer, WalletTransferParams
from ._base import AsyncResource, SyncResource


def _list_banks() -> Request[list[Bank]]:
    return Request("GET", "/v1/transfers/banks")


def _lookup_account(account_number: str, bank_code: str) -> Request[BankAccountLookup]:
    require(account_number, "account_number")
    require(bank_code, "bank_code")
    return Request("POST", "/v1/transfers/bank/lookup", body={"accountNumber": account_number, "bankCode": bank_code})


def _to_bank(params: BankTransferParams, sub_account_id: str | None) -> Request[Transfer]:
    body, ref = with_reference(params)
    return Request("POST", sub_account_path("/v2/transfers/bank{sub}", sub_account_id), body=body, reference=ref)


def _to_wallet(params: WalletTransferParams, sub_account_id: str | None) -> Request[Transfer]:
    body, ref = with_reference(params)
    return Request("POST", sub_account_path("/v2/transfers/wallet{sub}", sub_account_id), body=body, reference=ref)


class Transfers(SyncResource):
    def list_banks(self) -> list[Bank]:
        """Bank codes and names for transfers."""
        return self._client._request(_list_banks())

    def lookup_account(self, *, account_number: str, bank_code: str) -> BankAccountLookup:
        """Resolve the account name for a bank account number."""
        return self._client._request(_lookup_account(account_number, bank_code))

    def to_bank(self, params: BankTransferParams, *, sub_account_id: str | None = None) -> Transfer:
        """Send money to a bank account. Never retried automatically.

        Pass your own ``merchantTxRef`` and reuse it if you retry; if you leave
        it out a UUID v4 is generated and returned as ``result["merchantTxRef"]``.
        """
        return self._client._request(_to_bank(params, sub_account_id))

    def to_wallet(self, params: WalletTransferParams, *, sub_account_id: str | None = None) -> Transfer:
        """Send money to another Nomba account. Never retried automatically."""
        return self._client._request(_to_wallet(params, sub_account_id))


class AsyncTransfers(AsyncResource):
    async def list_banks(self) -> list[Bank]:
        """Bank codes and names for transfers."""
        return await self._client._request(_list_banks())

    async def lookup_account(self, *, account_number: str, bank_code: str) -> BankAccountLookup:
        """Resolve the account name for a bank account number."""
        return await self._client._request(_lookup_account(account_number, bank_code))

    async def to_bank(self, params: BankTransferParams, *, sub_account_id: str | None = None) -> Transfer:
        """Send money to a bank account. Never retried automatically."""
        return await self._client._request(_to_bank(params, sub_account_id))

    async def to_wallet(self, params: WalletTransferParams, *, sub_account_id: str | None = None) -> Transfer:
        """Send money to another Nomba account. Never retried automatically."""
        return await self._client._request(_to_wallet(params, sub_account_id))
