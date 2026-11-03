from __future__ import annotations

from typing import TypedDict

__all__ = ["RevokeResult"]


class RevokeResult(TypedDict, total=False):
    code: str
    description: str
