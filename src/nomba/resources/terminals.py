from __future__ import annotations

from .._core import Request, path, sub_account_path
from ..types.terminals import AssignTerminalParams, Terminal, TerminalPaymentRequest, TerminalPaymentRequestParams
from ._base import AsyncResource, SyncResource


def _assign(action: str, params: AssignTerminalParams, sub_account_id: str | None) -> Request[Terminal]:
    return Request("POST", sub_account_path(f"/v1/terminals/{action}{{sub}}", sub_account_id), body=dict(params))


def _send_payment_request(terminal_id: str, params: TerminalPaymentRequestParams) -> Request[TerminalPaymentRequest]:
    return Request("POST", path("/v1/terminals/payment-request/{}", terminal_id), body=dict(params))


class Terminals(SyncResource):
    def assign(self, params: AssignTerminalParams, *, sub_account_id: str | None = None) -> Terminal:
        """Assign a POS terminal (by serial number) to the parent account or ``sub_account_id``."""
        return self._client._request(_assign("assign", params, sub_account_id))

    def unassign(self, params: AssignTerminalParams, *, sub_account_id: str | None = None) -> Terminal:
        """Remove a POS terminal from the parent account or ``sub_account_id``."""
        return self._client._request(_assign("unassign", params, sub_account_id))

    def send_payment_request(self, terminal_id: str, params: TerminalPaymentRequestParams) -> TerminalPaymentRequest:
        """Push a payment request to a terminal."""
        return self._client._request(_send_payment_request(terminal_id, params))


class AsyncTerminals(AsyncResource):
    async def assign(self, params: AssignTerminalParams, *, sub_account_id: str | None = None) -> Terminal:
        """Assign a POS terminal (by serial number) to the parent account or ``sub_account_id``."""
        return await self._client._request(_assign("assign", params, sub_account_id))

    async def unassign(self, params: AssignTerminalParams, *, sub_account_id: str | None = None) -> Terminal:
        """Remove a POS terminal from the parent account or ``sub_account_id``."""
        return await self._client._request(_assign("unassign", params, sub_account_id))

    async def send_payment_request(
        self, terminal_id: str, params: TerminalPaymentRequestParams
    ) -> TerminalPaymentRequest:
        """Push a payment request to a terminal."""
        return await self._client._request(_send_payment_request(terminal_id, params))
