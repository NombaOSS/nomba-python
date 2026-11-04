from __future__ import annotations

import re
from pathlib import Path

import nomba
from nomba._core import USER_AGENT


def test_version_matches_pyproject() -> None:
    text = (Path(__file__).parent.parent / "pyproject.toml").read_text()
    match = re.search(r'^version = "([^"]+)"', text, re.MULTILINE)
    assert match is not None
    assert nomba.__version__ == match.group(1)


def test_user_agent() -> None:
    assert USER_AGENT.startswith(f"nomba-python/{nomba.__version__} python/")
    assert "httpx/" in USER_AGENT


def test_public_exports() -> None:
    for name in nomba.__all__:
        assert hasattr(nomba, name), name
