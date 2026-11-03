"""FastAPI webhook handler.

pip install fastapi uvicorn
NOMBA_WEBHOOK_SIGNING_KEY=... uvicorn examples.webhook_fastapi:app
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Request

from nomba import WebhookEventType, WebhookVerificationError
from nomba.webhooks import verify_signature

app = FastAPI()
SIGNING_KEY = os.environ["NOMBA_WEBHOOK_SIGNING_KEY"]


@app.post("/webhooks/nomba")
async def nomba_webhook(request: Request) -> dict[str, bool]:
    raw = await request.body()  # the raw bytes, exactly as Nomba sent them
    try:
        event = verify_signature(raw, request.headers, SIGNING_KEY, tolerance_seconds=300)
    except WebhookVerificationError:
        raise HTTPException(status_code=401) from None

    if event["event_type"] in (WebhookEventType.PAYOUT_FAILED, WebhookEventType.PAYOUT_REFUND):
        print("Payout needs attention:", event["data"]["transaction"].get("transactionId"))
    return {"ok": True}
