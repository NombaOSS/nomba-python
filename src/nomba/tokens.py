"""Access-token storage.

The client caches its OAuth token in a :class:`TokenStore`. The default
:class:`InMemoryTokenStore` keeps it in the process. To share one token across
several processes or hosts (Nomba recommends a single authenticating
instance), implement :class:`TokenStore` (or :class:`AsyncTokenStore` for
:class:`~nomba.AsyncNomba`) on top of Redis, a database, etc.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol, runtime_checkable

__all__ = ["AsyncTokenStore", "InMemoryTokenStore", "Token", "TokenStore"]


@dataclass(frozen=True)
class Token:
    """An access token and the refresh token that came with it."""

    access_token: str = field(repr=False)
    refresh_token: str = field(repr=False)
    expires_at: datetime

    def __repr__(self) -> str:
        return f"Token(access_token='***', refresh_token='***', expires_at={self.expires_at.isoformat()!r})"


@runtime_checkable
class TokenStore(Protocol):
    """Synchronous token storage."""

    def get(self) -> Token | None: ...

    def set(self, token: Token | None) -> None: ...


@runtime_checkable
class AsyncTokenStore(Protocol):
    """Asynchronous token storage, for :class:`~nomba.AsyncNomba`."""

    async def get(self) -> Token | None: ...

    async def set(self, token: Token | None) -> None: ...


class InMemoryTokenStore:
    """Keeps the token in this process. The default."""

    def __init__(self) -> None:
        self._token: Token | None = None

    def get(self) -> Token | None:
        return self._token

    def set(self, token: Token | None) -> None:
        self._token = token

    def __repr__(self) -> str:
        return f"InMemoryTokenStore(has_token={self._token is not None})"


_FRACTION = re.compile(r"\.(\d+)")

# If Nomba ever sends an expiry we can't parse, treat the token as short-lived
# so it is refreshed early rather than used after it has expired.
_FALLBACK_LIFETIME = timedelta(minutes=10)


def parse_timestamp(value: str) -> datetime:
    """Parse an RFC 3339 timestamp on every supported Python version.

    Raises ``ValueError`` if ``value`` isn't a timestamp.
    """
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    # Python < 3.11 accepts only 3 or 6 fractional digits.
    text = _FRACTION.sub(lambda m: "." + (m.group(1) + "000000")[:6], text, count=1)
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def token_from_response(data: Any, now: datetime) -> Token:
    """Build a :class:`Token` from the ``data`` of an issue/refresh response."""
    if not isinstance(data, dict):
        raise ValueError("token response has no data object")
    access = data.get("access_token")
    if not isinstance(access, str) or not access:
        raise ValueError("token response has no access_token")
    refresh = data.get("refresh_token")
    expires = data.get("expiresAt")
    try:
        expires_at = parse_timestamp(expires) if isinstance(expires, str) else now + _FALLBACK_LIFETIME
    except ValueError:
        expires_at = now + _FALLBACK_LIFETIME
    return Token(
        access_token=access,
        refresh_token=refresh if isinstance(refresh, str) else "",
        expires_at=expires_at,
    )
