from __future__ import annotations

from typing import Any

import httpx
import pytest

from nomba import AsyncNomba, ConfigurationError, Nomba
from nomba._config import resolve_config

from .conftest import CLIENT_SECRET


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("NOMBA_CLIENT_ID", "NOMBA_CLIENT_SECRET", "NOMBA_ACCOUNT_ID", "NOMBA_ENVIRONMENT"):
        monkeypatch.delenv(name, raising=False)


def creds(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"client_id": "id", "client_secret": CLIENT_SECRET, "account_id": "acct"}
    base.update(overrides)
    return base


def test_reads_credentials_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOMBA_CLIENT_ID", "env-id")
    monkeypatch.setenv("NOMBA_CLIENT_SECRET", "env-secret")
    monkeypatch.setenv("NOMBA_ACCOUNT_ID", "env-acct")
    with Nomba() as client:
        assert client._config.client_id == "env-id"
        assert client._config.account_id == "env-acct"
        assert client.environment == "sandbox"
        assert client.base_url == "https://sandbox.nomba.com"


def test_explicit_options_override_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOMBA_CLIENT_ID", "env-id")
    with Nomba(client_id="arg-id", client_secret="s", account_id="a") as client:
        assert client._config.client_id == "arg-id"


def test_missing_credentials_name_option_and_env_var() -> None:
    with pytest.raises(ConfigurationError) as info:
        Nomba(client_id="id")
    message = str(info.value)
    assert "client_secret (or env NOMBA_CLIENT_SECRET)" in message
    assert "account_id (or env NOMBA_ACCOUNT_ID)" in message
    assert "client_id" not in message.split(":", 1)[1].replace("client_secret", "")


def test_production_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOMBA_ENVIRONMENT", "production")
    with Nomba(**creds()) as client:
        assert client.base_url == "https://api.nomba.com"
        assert client.environment == "production"


@pytest.mark.parametrize("env", ["live", "Production", "staging", ""])
def test_rejects_unknown_environment(env: str) -> None:
    if env == "":
        # empty string falls back to the default
        with Nomba(**creds(environment=None)) as client:
            assert client.environment == "sandbox"
        return
    with pytest.raises(ConfigurationError, match="environment"):
        Nomba(**creds(environment=env))


@pytest.mark.parametrize(
    "url",
    [
        "https://proxy.example.com/",
        "https://proxy.example.com/nomba",
        "http://localhost:8080",
        "http://127.0.0.1:9000",
        "http://[::1]:9000",
    ],
)
def test_accepts_base_url(url: str) -> None:
    with Nomba(**creds(base_url=url)) as client:
        assert client.base_url == url.rstrip("/")


@pytest.mark.parametrize(
    "url",
    [
        "http://proxy.example.com",
        "ftp://localhost",
        "proxy.example.com",
        "https://proxy.example.com?x=1",
        "https://user:pass@proxy.example.com",
        "http://localhost.evil.com",
    ],
)
def test_rejects_base_url(url: str) -> None:
    with pytest.raises(ConfigurationError):
        Nomba(**creds(base_url=url))


@pytest.mark.parametrize(("timeout", "retries"), [(0, None), (-1, None), (True, None), (None, -1), (None, 1.5)])
def test_rejects_bad_timeout_and_retries(timeout: object, retries: object) -> None:
    with pytest.raises(ConfigurationError):
        resolve_config(
            client_id="i",
            client_secret="s",
            account_id="a",
            environment=None,
            base_url=None,
            timeout=timeout,  # type: ignore[arg-type]
            max_retries=retries,  # type: ignore[arg-type]
        )


def test_repr_redacts_secret() -> None:
    with Nomba(**creds()) as client:
        assert CLIENT_SECRET not in repr(client)
        assert CLIENT_SECRET not in repr(client._config)
        assert "***" in repr(client)


async def test_async_repr_and_env() -> None:
    async with AsyncNomba(**creds(environment="production")) as client:
        assert client.environment == "production"
        assert client.base_url == "https://api.nomba.com"
        assert CLIENT_SECRET not in repr(client)


def test_constructor_makes_no_network_call() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(500)

    http = httpx.Client(transport=httpx.MockTransport(handler))
    Nomba(**creds(http_client=http))
    assert calls == []


def test_close_leaves_injected_client_open() -> None:
    http = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    with Nomba(**creds(http_client=http)):
        pass
    assert not http.is_closed
    http.close()


def test_close_closes_owned_client() -> None:
    client = Nomba(**creds())
    client.close()
    assert client._http.is_closed


async def test_async_close_variants() -> None:
    http = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    async with AsyncNomba(**creds(http_client=http)):
        pass
    assert not http.is_closed
    await http.aclose()
    owned = AsyncNomba(**creds())
    await owned.close()
    assert owned._http.is_closed
