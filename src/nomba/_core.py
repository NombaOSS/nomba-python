"""I/O-free request core shared by the sync and async clients.

Request handling is written once, as generators that *yield* the I/O they need
(:class:`Send`, :class:`Sleep`, :class:`AccessToken`) and receive the result.
``Nomba`` drives them with blocking calls and ``AsyncNomba`` with ``await``,
so building requests, retries, the 401 refresh, token issue/refresh and error
mapping exist in one place.
"""

from __future__ import annotations

import json
import platform
import random
import uuid
from collections.abc import Callable, Generator, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Generic, TypeVar
from urllib.parse import quote

import httpx

from ._config import Config
from ._version import __version__
from .errors import (
    APIConnectionError,
    ApiError,
    APITimeoutError,
    AuthenticationError,
    NombaError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    Reference,
    ServerError,
    ValidationError,
)
from .tokens import Token, token_from_response

T = TypeVar("T")

SUCCESS_CODES = frozenset({"00", "200", "201"})
REFRESH_WINDOW_SECONDS = 5 * 60
MAX_BACKOFF_SECONDS = 8.0
MAX_RETRY_AFTER_SECONDS = 60.0
MAX_PAGE_LIMIT = 50
_DESCRIPTION_LIMIT = 500

USER_AGENT = f"nomba-python/{__version__} python/{platform.python_version()} httpx/{httpx.__version__}"


# --------------------------------------------------------------------------- requests


@dataclass(frozen=True)
class Request(Generic[T]):
    """One API operation and its policy. ``T`` is the type of the unwrapped ``data``."""

    method: str
    path: str
    query: Mapping[str, Any] | None = None
    body: Any = None
    reference: Reference | None = None
    """Idempotency reference of a money-moving call: added to the returned
    data if missing, and attached to any error the call raises."""
    retryable: bool | None = None
    """Retry connection errors, timeouts, 429 and 5xx. ``None`` means "only for
    GET": a retried POST/PUT/DELETE could move money twice."""
    retry_on_401: bool = True
    """Get a fresh token and resend once after a 401 (safe: a 401 means the
    request was not processed)."""
    authenticated: bool = True
    """Send ``Authorization: Bearer <token>``."""
    auth_endpoint: bool = False
    """A token issue/refresh/revoke call: error bodies are stored without ``data``."""

    def __post_init__(self) -> None:
        if self.retryable is None:
            object.__setattr__(self, "retryable", self.method == "GET")


def path(template: str, *values: object) -> str:
    """Fill ``{}`` placeholders with validated, URL-encoded path segments."""
    encoded = [quote(validate_segment(v), safe="") for v in values]
    return template.format(*encoded)


def sub_account_path(template: str, sub_account_id: str | None) -> str:
    """Fill ``{sub}`` with ``/<sub_account_id>`` (validated, encoded), or nothing for the parent account.

    ``sub_account_path("/v1/accounts{sub}/balance", None)`` is ``/v1/accounts/balance``.
    """
    sub = "" if sub_account_id is None else "/" + quote(validate_segment(sub_account_id), safe="")
    return template.replace("{sub}", sub)


def validate_segment(value: object, name: str = "path parameter") -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be a string, got {type(value).__name__}")
    if value == "" or value.strip() == "":
        raise ValidationError(f"{name} must not be empty")
    if value in (".", "..") or "/" in value or "\\" in value:
        raise ValidationError(f"{name} {value!r} is not allowed (contains '/' or is '.' or '..')")
    return value


def clean_query(params: Mapping[str, Any]) -> dict[str, str]:
    """Drop ``None`` values and render booleans as ``true``/``false``."""
    out: dict[str, str] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            out[key] = "true" if value else "false"
        else:
            out[key] = str(value)
    return out


def check_limit(limit: int | None) -> int | None:
    if limit is None:
        return None
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_PAGE_LIMIT:
        raise ValidationError(f"limit must be an integer between 1 and {MAX_PAGE_LIMIT}")
    return limit


def require(value: Any, name: str) -> None:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        raise ValidationError(f"{name} is required")


def exactly_one(**candidates: Any) -> tuple[str, Any]:
    given = [(k, v) for k, v in candidates.items() if v is not None]
    if len(given) != 1:
        names = ", ".join(candidates)
        raise ValidationError(f"pass exactly one of: {names}")
    return given[0]


def new_reference() -> str:
    """A UUID v4 (cryptographically random) for idempotency references."""
    return str(uuid.uuid4())


def with_reference(params: Mapping[str, Any], key: str = "merchantTxRef") -> tuple[dict[str, Any], Reference]:
    """Copy ``params`` and make sure ``key`` holds a reference, generating one if needed."""
    body = dict(params)
    ref = body.get(key)
    if not isinstance(ref, str) or not ref:
        ref = new_reference()
        body[key] = ref
    return body, Reference(key, ref)


def _add_reference(data: Any, reference: Reference) -> Any:
    if isinstance(data, dict) and not data.get(reference.field):
        data[reference.field] = reference.value
    return data


# --------------------------------------------------------------------------- actions


@dataclass(frozen=True)
class Send:
    """Send ``request`` and read the whole body within ``total_timeout`` seconds.

    The driver answers with a :class:`Received`.
    """

    request: httpx.Request
    total_timeout: float


@dataclass(frozen=True)
class Received:
    """A response (headers only) and its fully read, decoded body."""

    response: httpx.Response
    content: bytes


@dataclass(frozen=True)
class Sleep:
    seconds: float


@dataclass(frozen=True)
class AccessToken:
    """Ask the driver for a valid access token.

    ``stale`` is a token that just got a 401: the driver drops it (unless
    another caller already replaced it) and obtains a new one.
    """

    stale: str | None = None


Action = Send | Sleep | AccessToken
Flow = Generator[Action, Any, T]


# --------------------------------------------------------------------------- HTTP


def build_http_request(req: Request[Any], config: Config, access_token: str | None) -> httpx.Request:
    headers = {
        "accountId": config.account_id,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    if access_token is not None:
        headers["Authorization"] = f"Bearer {access_token}"
    content = None
    if req.body is not None:
        content = json.dumps(req.body, separators=(",", ":")).encode()
    return httpx.Request(
        req.method,
        config.base_url + req.path,
        params=clean_query(req.query) if req.query else None,
        headers=headers,
        content=content,
        extensions={"timeout": httpx.Timeout(config.timeout).as_dict()},
    )


class TotalTimeout(httpx.ReadTimeout):
    """The whole attempt (connect, headers and body) took longer than ``timeout``."""


class BodyReader:
    """Collects a streamed body while enforcing a total deadline for the attempt.

    httpx timeouts apply per phase (connect, each read, ...), so a server
    trickling bytes could keep a request alive far beyond ``timeout``. Create
    the reader before sending (the clock starts then), call :meth:`check`
    once the headers arrive and :meth:`add` for each decoded chunk.
    """

    def __init__(self, action: Send, clock: Callable[[], float]) -> None:
        self._request = action.request
        self._clock = clock
        self._deadline = clock() + action.total_timeout
        self._chunks: list[bytes] = []

    def check(self) -> None:
        if self._clock() > self._deadline:
            raise TotalTimeout("total request timeout exceeded", request=self._request)

    def add(self, chunk: bytes) -> None:
        self._chunks.append(chunk)
        self.check()

    def received(self, response: httpx.Response) -> Received:
        return Received(response, b"".join(self._chunks))


def _is_retryable_status(status: int) -> bool:
    return status == 429 or status >= 500


def retry_after_seconds(response: httpx.Response | None) -> float | None:
    if response is None:
        return None
    raw = response.headers.get("retry-after")
    if raw is None:
        return None
    raw = raw.strip()
    try:
        seconds = float(raw)
    except ValueError:
        try:
            when = parsedate_to_datetime(raw)
        except (TypeError, ValueError):
            return None
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        seconds = (when - datetime.now(timezone.utc)).total_seconds()
    return max(0.0, seconds)


def backoff_seconds(attempt: int, response: httpx.Response | None = None) -> float:
    """Delay before retry number ``attempt`` (0-based)."""
    if response is not None and response.status_code == 429:
        after = retry_after_seconds(response)
        if after is not None:
            return min(after, MAX_RETRY_AFTER_SECONDS)
    base: float = min(0.5 * (2.0**attempt), MAX_BACKOFF_SECONDS)
    jitter = 0.8 + random.random() * 0.4  # noqa: S311 - not security sensitive
    return min(base * jitter, MAX_BACKOFF_SECONDS)


def transport_flow(req: Request[Any], config: Config, access_token: str | None) -> Flow[Received]:
    """Send ``req``, retrying network errors, 429 and 5xx when ``req.retryable``."""
    request = build_http_request(req, config, access_token)
    method, api_path = req.method, req.path
    attempt = 0
    while True:
        received: Received | None = None
        error: APIConnectionError | None = None
        try:
            received = yield Send(request, config.timeout)
        except httpx.TimeoutException as exc:
            error = APITimeoutError(f"Request to Nomba timed out [{method} {api_path}]", method=method, path=api_path)
            error.__cause__ = exc
        except httpx.TransportError as exc:
            error = APIConnectionError(
                f"Could not connect to Nomba ({type(exc).__name__}) [{method} {api_path}]",
                method=method,
                path=api_path,
            )
            error.__cause__ = exc
        response = received.response if received is not None else None
        if received is not None and not _is_retryable_status(received.response.status_code):
            return received
        if not req.retryable or attempt >= config.max_retries:
            if error is not None:
                raise error
            if received is not None:
                return received
        yield Sleep(backoff_seconds(attempt, response))
        attempt += 1


def _description(body: Any, response: httpx.Response) -> str:
    text: object = None
    if isinstance(body, dict):
        text = body.get("description") or body.get("message")
    if not isinstance(text, str) or not text:
        text = response.reason_phrase or "Unknown error"
    return text[:_DESCRIPTION_LIMIT]


def _format_message(status: int, code: str | None, description: str, method: str, api_path: str) -> str:
    code_part = f' (code "{code}")' if code is not None else ""
    return f"Nomba API error {status}{code_part}: {description} [{method} {api_path}]"


def _error_body(body: Any, req: Request[Any]) -> Any:
    # Token endpoints' data can hold tokens; keep it out of exceptions.
    if req.auth_endpoint and isinstance(body, dict):
        return {k: v for k, v in body.items() if k != "data"}
    return body


def _error_class(status: int) -> type[ApiError]:
    if status == 401:
        return AuthenticationError
    if status == 403:
        return PermissionDeniedError
    if status == 404:
        return NotFoundError
    if status in (400, 422):
        return ValidationError
    if status == 429:
        return RateLimitError
    if status >= 500:
        return ServerError
    return ApiError


def parse_response(received: Received, req: Request[Any]) -> Any:
    """Unwrap the envelope and return ``data``, or raise the matching error."""
    response, content = received.response, received.content
    method, api_path = req.method, req.path
    body: Any
    try:
        body = json.loads(content) if content else None
    except ValueError:
        body = None
    status = response.status_code
    code_raw = body.get("code") if isinstance(body, dict) else None
    code = None if code_raw is None else str(code_raw)

    if 200 <= status < 300:
        if isinstance(body, dict):
            if code is None or code in SUCCESS_CODES:
                return body.get("data")
        elif not content:
            return None
        description = _description(body, response) if isinstance(body, dict) else "Response was not a JSON envelope"
        body = _error_body(body, req)
        raise ApiError(
            _format_message(status, code, description, method, api_path),
            http_status=status,
            code=code,
            description=description,
            body=body,
            method=method,
            path=api_path,
        )

    description = _description(body, response)
    body = _error_body(body, req)
    cls = _error_class(status)
    kwargs: dict[str, Any] = {
        "http_status": status,
        "code": code,
        "description": description,
        "body": body,
        "method": method,
        "path": api_path,
    }
    message = _format_message(status, code, description, method, api_path)
    if cls is RateLimitError:
        raise RateLimitError(
            message,
            retry_after=retry_after_seconds(response),
            rate_limit_limit=response.headers.get("x-rate-limit-limit"),
            rate_limit_remaining=response.headers.get("x-rate-limit-remaining"),
            rate_limit_window=response.headers.get("x-rate-limit-window"),
            **kwargs,
        )
    raise cls(message, **kwargs)


# --------------------------------------------------------------------------- flows


def api_flow(req: Request[T], config: Config) -> Flow[T]:
    """An authenticated API call: token, send (with retries), 401 refresh-once, unwrap."""
    try:
        data = yield from _api_call(req, config)
    except NombaError as exc:
        # The caller needs the reference to requery before retrying, above all
        # when the outcome is unknown (timeout, connection error, 5xx).
        if req.reference is not None:
            exc.reference = req.reference
        raise
    if req.reference is not None:
        data = _add_reference(data, req.reference)
    return data  # type: ignore[no-any-return]


def _api_call(req: Request[Any], config: Config) -> Flow[Any]:
    token: str | None = (yield AccessToken(None)) if req.authenticated else None
    received = yield from transport_flow(req, config, token)
    if received.response.status_code == 401 and req.retry_on_401 and req.authenticated:
        # A 401 means the request was not processed, so retrying once with a
        # fresh token is safe even for POST.
        token = yield AccessToken(token)
        received = yield from transport_flow(req, config, token)
    return parse_response(received, req)


def usable_token(token: Token | None, stale: str | None, now: datetime) -> str | None:
    """The cached access token if it can be used as is, else ``None``.

    Lets the drivers skip the token lock on the hot path.
    """
    if token is None or token.access_token == stale or token_decision(token, now) != "valid":
        return None
    return token.access_token


def token_decision(token: Token | None, now: datetime) -> str:
    """``"valid"``, ``"refresh"`` or ``"issue"``."""
    if token is None or not token.access_token:
        return "issue"
    remaining = (token.expires_at - now).total_seconds()
    if remaining > REFRESH_WINDOW_SECONDS:
        return "valid"
    return "refresh" if token.refresh_token else "issue"


def _token_request(api_path: str, body: dict[str, str]) -> Request[Any]:
    # Token issue/refresh moves no money, so it is retried like a GET.
    return Request(
        "POST", api_path, body=body, retryable=True, retry_on_401=False, authenticated=False, auth_endpoint=True
    )


def revoke_request(config: Config, token: Token) -> Request[Any]:
    return Request(
        "POST",
        "/v1/auth/token/revoke",
        body={"clientId": config.client_id, "access_token": token.access_token},
        retry_on_401=False,
        auth_endpoint=True,
    )


def _is_client_rejection(error: ApiError) -> bool:
    status = error.http_status or 0
    return (400 <= status < 500 and status != 429) or 200 <= status < 300


def obtain_token_flow(config: Config, current: Token | None, now: Callable[[], datetime]) -> Flow[Token]:
    """Refresh ``current`` if given, falling back to a fresh issue on a 4xx."""
    if current is not None and current.refresh_token:
        try:
            data = yield from _api_call(
                _token_request(
                    "/v1/auth/token/refresh",
                    {"grant_type": "refresh_token", "refresh_token": current.refresh_token},
                ),
                config,
            )
            return token_from_response(data, now())
        except ApiError as exc:
            # A 4xx means the refresh token is no good: fall through to a new issue.
            # Anything else (5xx, 429) is an outage: keep the current token while it lasts.
            if not _is_client_rejection(exc):
                if current.expires_at > now():
                    return current
                raise
        except (APIConnectionError, ValueError):
            if current.expires_at > now():
                return current
            # fall through to a fresh issue
    try:
        data = yield from _api_call(
            _token_request(
                "/v1/auth/token/issue",
                {
                    "grant_type": "client_credentials",
                    "client_id": config.client_id,
                    "client_secret": config.client_secret,
                },
            ),
            config,
        )
    except ApiError as exc:
        if isinstance(exc, AuthenticationError) or not _is_client_rejection(exc):
            raise
        raise AuthenticationError(
            f"Could not obtain a Nomba access token: {exc}",
            http_status=exc.http_status,
            code=exc.code,
            description=exc.description,
            body=exc.body,
            method=exc.method,
            path=exc.path,
        ) from exc
    try:
        return token_from_response(data, now())
    except ValueError as exc:
        raise AuthenticationError(
            f"Could not obtain a Nomba access token: {exc} [POST /v1/auth/token/issue]",
            method="POST",
            path="/v1/auth/token/issue",
        ) from None


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
