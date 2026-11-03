from __future__ import annotations

import os
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from .errors import ConfigurationError

ENVIRONMENTS = {
    "sandbox": "https://sandbox.nomba.com",
    "production": "https://api.nomba.com",
}
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


@dataclass(frozen=True)
class Config:
    client_id: str
    client_secret: str = field(repr=False)
    account_id: str
    environment: str
    base_url: str
    timeout: float
    max_retries: int

    @property
    def is_sandbox(self) -> bool:
        return self.environment == "sandbox"

    def __repr__(self) -> str:
        return (
            f"Config(client_id={self.client_id!r}, client_secret='***', account_id={self.account_id!r}, "
            f"environment={self.environment!r}, base_url={self.base_url!r}, timeout={self.timeout!r}, "
            f"max_retries={self.max_retries!r})"
        )


def _pick(value: str | None, env: str) -> str | None:
    if value is not None:
        return value
    from_env = os.environ.get(env)
    return from_env if from_env else None


def _validate_base_url(url: str) -> str:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if not host:
        raise ConfigurationError(f"base_url {url!r} is not an absolute URL")
    if not (parts.scheme == "https" or (parts.scheme == "http" and host in _LOCAL_HOSTS)):
        raise ConfigurationError("base_url must use https:// (http:// is allowed only for localhost or 127.0.0.1)")
    if parts.query or parts.fragment:
        raise ConfigurationError("base_url must not contain a query string or fragment")
    if parts.username or parts.password:
        raise ConfigurationError("base_url must not contain credentials")
    return url.rstrip("/")


def resolve_config(
    *,
    client_id: str | None,
    client_secret: str | None,
    account_id: str | None,
    environment: str | None,
    base_url: str | None,
    timeout: float | None,
    max_retries: int | None,
) -> Config:
    cid = _pick(client_id, "NOMBA_CLIENT_ID")
    secret = _pick(client_secret, "NOMBA_CLIENT_SECRET")
    acct = _pick(account_id, "NOMBA_ACCOUNT_ID")
    missing = [
        f"{opt} (or env {env})"
        for opt, env, val in (
            ("client_id", "NOMBA_CLIENT_ID", cid),
            ("client_secret", "NOMBA_CLIENT_SECRET", secret),
            ("account_id", "NOMBA_ACCOUNT_ID", acct),
        )
        if not val
    ]
    if missing or cid is None or secret is None or acct is None:
        raise ConfigurationError("Missing Nomba credentials: " + ", ".join(missing))

    env_name = _pick(environment, "NOMBA_ENVIRONMENT") or "sandbox"
    if env_name not in ENVIRONMENTS:
        raise ConfigurationError(f"environment must be 'sandbox' or 'production', got {env_name!r}")

    url = _validate_base_url(base_url) if base_url is not None else ENVIRONMENTS[env_name]

    t = DEFAULT_TIMEOUT if timeout is None else timeout
    if isinstance(t, bool) or not isinstance(t, (int, float)) or t <= 0:
        raise ConfigurationError("timeout must be a positive number of seconds")
    r = DEFAULT_MAX_RETRIES if max_retries is None else max_retries
    if isinstance(r, bool) or not isinstance(r, int) or r < 0:
        raise ConfigurationError("max_retries must be a non-negative integer")

    return Config(
        client_id=cid,
        client_secret=secret,
        account_id=acct,
        environment=env_name,
        base_url=url,
        timeout=float(t),
        max_retries=r,
    )
