from __future__ import annotations

from typing import cast

from ..types.auth import RevokeResult
from ._base import AsyncResource, SyncResource


class Auth(SyncResource):
    def revoke(self) -> RevokeResult | None:
        """Revoke the cached access token and clear the token store.

        Does nothing (and returns ``None``) if no token is cached.
        """
        return cast("RevokeResult | None", self._client._revoke())


class AsyncAuth(AsyncResource):
    async def revoke(self) -> RevokeResult | None:
        """Revoke the cached access token and clear the token store."""
        return cast("RevokeResult | None", await self._client._revoke())
