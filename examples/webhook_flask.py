"""Flask webhook handler.

pip install flask
NOMBA_WEBHOOK_SIGNING_KEY=... flask --app examples/webhook_flask run
"""

from __future__ import annotations

import os

from flask import Flask, abort, request

from nomba import WebhookEventType, WebhookVerificationError
from nomba.webhooks import verify_signature

app = Flask(__name__)
SIGNING_KEY = os.environ["NOMBA_WEBHOOK_SIGNING_KEY"]


@app.post("/webhooks/nomba")
def nomba_webhook() -> tuple[str, int]:
    try:
        # get_data() is the raw body. Don't use request.json and re-encode it.
        event = verify_signature(request.get_data(), request.headers, SIGNING_KEY, tolerance_seconds=300)
    except WebhookVerificationError:
        abort(401)

    if event["event_type"] == WebhookEventType.PAYMENT_SUCCESS:
        transaction = event["data"]["transaction"]
        print("Paid:", transaction.get("transactionId"), transaction.get("transactionAmount"))
    # Nomba retries webhooks that don't get a 2xx, so make handling idempotent
    # on event["requestId"].
    return "", 200
