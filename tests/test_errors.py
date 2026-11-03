from __future__ import annotations

import httpx
import pytest

from nomba import (
    ApiError,
    AuthenticationError,
    NombaError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from nomba._core import parse_response

from .conftest import CLIENT_SECRET, MockAPI, envelope, make_client


@pytest.mark.parametrize("code", ["00", "200", "201", None])
def test_success_codes_return_data(code: str | None) -> None:
    response = envelope({"ok": True}, code=code)
    assert parse_response(response, "GET", "/x") == {"ok": True}


def test_numeric_code_is_normalised() -> None:
    response = httpx.Response(200, json={"code": 200, "data": [1]})
    assert parse_response(response, "GET", "/x") == [1]


def test_empty_2xx_body_returns_none() -> None:
    assert parse_response(httpx.Response(204), "DELETE", "/x") is None


def test_2xx_with_failure_code_raises_api_error() -> None:
    response = envelope({"status": False}, code="400", description="Email address doesn't match token key")
    with pytest.raises(ApiError) as info:
        parse_response(response, "POST", "/v1/checkout/tokenized-card-payment")
    err = info.value
    assert type(err) is ApiError
    assert err.http_status == 200
    assert err.code == "400"
    assert err.description == "Email address doesn't match token key"
    assert err.body == {
        "code": "400",
        "description": "Email address doesn't match token key",
        "data": {"status": False},
    }
    assert str(err) == (
        'Nomba API error 200 (code "400"): Email address doesn\'t match token key '
        "[POST /v1/checkout/tokenized-card-payment]"
    )


def test_2xx_non_json_raises() -> None:
    with pytest.raises(ApiError, match="not a JSON envelope"):
        parse_response(httpx.Response(200, text="<html>"), "GET", "/x")


@pytest.mark.parametrize(
    ("status", "cls"),
    [
        (400, ValidationError),
        (401, AuthenticationError),
        (403, PermissionDeniedError),
        (404, NotFoundError),
        (409, ApiError),
        (422, ValidationError),
        (429, RateLimitError),
        (500, ServerError),
        (502, ServerError),
        (503, ServerError),
    ],
)
def test_http_status_maps_to_class(status: int, cls: type[ApiError]) -> None:
    response = httpx.Response(status, json={"code": str(status), "description": "Bad thing"})
    with pytest.raises(cls) as info:
        parse_response(response, "POST", "/v2/transfers/bank")
    err = info.value
    assert type(err) is cls
    assert isinstance(err, ApiError)
    assert isinstance(err, NombaError)
    assert err.http_status == status
    assert err.method == "POST"
    assert err.path == "/v2/transfers/bank"
    assert str(err) == f'Nomba API error {status} (code "{status}"): Bad thing [POST /v2/transfers/bank]'


def test_non_json_error_uses_reason_phrase() -> None:
    with pytest.raises(ServerError) as info:
        parse_response(httpx.Response(502, text="bad gateway"), "GET", "/x")
    assert info.value.description == "Bad Gateway"
    assert info.value.code is None
    assert str(info.value) == "Nomba API error 502: Bad Gateway [GET /x]"


def test_message_field_used_when_description_missing() -> None:
    with pytest.raises(ValidationError, match="amount is required"):
        parse_response(httpx.Response(400, json={"message": "amount is required"}), "POST", "/x")


def test_long_description_is_truncated() -> None:
    with pytest.raises(ValidationError) as info:
        parse_response(httpx.Response(400, json={"description": "x" * 5000}), "POST", "/x")
    assert info.value.description is not None
    assert len(info.value.description) == 500


def test_rate_limit_details() -> None:
    response = httpx.Response(
        429,
        json={"code": "429", "description": "Too many requests. Please slow down.", "data": None},
        headers={
            "Retry-After": "3",
            "X-Rate-Limit-Limit": "40",
            "X-Rate-Limit-Remaining": "0",
            "X-Rate-Limit-Window": "1s",
        },
    )
    with pytest.raises(RateLimitError) as info:
        parse_response(response, "POST", "/v2/transfers/bank")
    err = info.value
    assert err.retry_after == 3.0
    assert err.rate_limit_limit == "40"
    assert err.rate_limit_remaining == "0"
    assert err.rate_limit_window == "1s"


def test_rate_limit_without_headers() -> None:
    with pytest.raises(RateLimitError) as info:
        parse_response(httpx.Response(429, json={}), "GET", "/x")
    assert info.value.retry_after is None


def test_error_path_excludes_query_and_secrets(api: MockAPI) -> None:
    api.add("GET", "/v1/transactions/accounts/single", httpx.Response(404, json={"code": "404", "description": "nf"}))
    with make_client(api) as client, pytest.raises(NotFoundError) as info:
        client.transactions.get(merchant_tx_ref="secret-ish-ref")
    text = str(info.value)
    assert text == 'Nomba API error 404 (code "404"): nf [GET /v1/transactions/accounts/single]'
    assert "secret-ish-ref" not in text
    assert CLIENT_SECRET not in repr(info.value.__dict__)
    assert "access-1" not in repr(info.value.__dict__)
