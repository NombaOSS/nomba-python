from __future__ import annotations

from typing import Any, TypedDict

__all__ = ["WebhookEvent"]


class _WebhookEventBase(TypedDict):
    event_type: str
    """One of :class:`nomba.WebhookEventType`."""
    requestId: str
    data: dict[str, Any]


class WebhookEvent(_WebhookEventBase, total=False):
    """A verified webhook payload. Extra keys Nomba adds are kept."""
