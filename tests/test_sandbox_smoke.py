"""Opt-in smoke test against the real Nomba sandbox. Never runs in CI.

Set NOMBA_SANDBOX_CLIENT_ID, NOMBA_SANDBOX_CLIENT_SECRET and
NOMBA_SANDBOX_ACCOUNT_ID to run it.
"""

from __future__ import annotations

import os

import pytest

from nomba import Nomba

_VARS = ("NOMBA_SANDBOX_CLIENT_ID", "NOMBA_SANDBOX_CLIENT_SECRET", "NOMBA_SANDBOX_ACCOUNT_ID")

pytestmark = pytest.mark.skipif(
    not all(os.environ.get(v) for v in _VARS) or bool(os.environ.get("CI")),
    reason="sandbox credentials not set (opt-in only)",
)


def test_sandbox_get_parent() -> None:  # pragma: no cover - opt-in
    with Nomba(
        client_id=os.environ["NOMBA_SANDBOX_CLIENT_ID"],
        client_secret=os.environ["NOMBA_SANDBOX_CLIENT_SECRET"],
        account_id=os.environ["NOMBA_SANDBOX_ACCOUNT_ID"],
        environment="sandbox",
    ) as nomba:
        parent = nomba.accounts.get_parent()
        assert parent["accountId"]
