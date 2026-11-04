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
        event = verify_signature(raw, request.headers, SIGNING_KEY)
    except WebhookVerificationError:
        raise HTTPException(status_code=401) from None

    ref = event["data"]["transaction"].get("merchantTxRef")
    if event["event_type"] == WebhookEventType.PAYOUT_FAILED:
        # Not final: Nomba may still retry the payout. Don't refund yet.
        print("Payout failing, waiting:", ref)
    elif event["event_type"] == WebhookEventType.PAYOUT_REFUND:
        # Final: the money is back in your wallet. Refund your user once, after
        # confirming with nomba.transactions.get(merchant_tx_ref=ref).
        print("Payout refunded:", ref)
    return {"ok": True}
