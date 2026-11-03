"""Exceptions raised by the Nomba SDK.

Hierarchy::

    NombaError
    ├── ConfigurationError
    ├── WebhookVerificationError
    ├── APIConnectionError
    │   └── APITimeoutError
    └── ApiError
        ├── AuthenticationError     401 after a token refresh, or token issue failed
        ├── PermissionDeniedError   403
        ├── NotFoundError           404
        ├── ValidationError         400, 422, and client-side validation
        ├── RateLimitError          429
        └── ServerError             5xx
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "APIConnectionError",
    "APITimeoutError",
    "ApiError",
    "AuthenticationError",
    "ConfigurationError",
    "NombaError",
    "NotFoundError",
    "PermissionDeniedError",
    "RateLimitError",
    "ServerError",
    "ValidationError",
    "WebhookVerificationError",
]


class NombaError(Exception):
    """Base class for every error raised by this SDK."""


class ConfigurationError(NombaError):
    """The client was constructed with missing or invalid options."""


class WebhookVerificationError(NombaError):
    """A webhook's signature, headers or body failed verification."""


class APIConnectionError(NombaError):
    """The request could not reach Nomba (DNS, TLS, connection reset, ...)."""

    def __init__(self, message: str, *, method: str | None = None, path: str | None = None) -> None:
        super().__init__(message)
        self.method = method
        self.path = path


class APITimeoutError(APIConnectionError):
    """The request timed out."""


class ApiError(NombaError):
    """Nomba answered with an error.

    Raised directly when Nomba returns HTTP 2xx with a non-success ``code``;
    HTTP error statuses raise one of the subclasses.
    """

    def __init__(
        self,
        message: str,
        *,
        http_status: int | None = None,
        code: str | None = None,
        description: str | None = None,
        body: Any = None,
        method: str | None = None,
        path: str | None = None,
    ) -> None:
        super().__init__(message)
        self.http_status = http_status
        self.code = code
        self.description = description
        self.body = body
        self.method = method
        self.path = path


class AuthenticationError(ApiError):
    """401 after the token refresh retry, or the access token could not be issued."""


class PermissionDeniedError(ApiError):
    """403."""


class NotFoundError(ApiError):
    """404."""


class ValidationError(ApiError):
    """400 or 422 from Nomba, or a client-side check failed before sending.

    Client-side validation errors have ``http_status`` set to ``None``.
    """


class RateLimitError(ApiError):
    """429. ``retry_after`` is in seconds when Nomba sent ``Retry-After``."""

    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
        rate_limit_limit: str | None = None,
        rate_limit_remaining: str | None = None,
        rate_limit_window: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after
        self.rate_limit_limit = rate_limit_limit
        self.rate_limit_remaining = rate_limit_remaining
        self.rate_limit_window = rate_limit_window


class ServerError(ApiError):
    """5xx."""
