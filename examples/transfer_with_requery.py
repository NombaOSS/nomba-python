"""Send a bank transfer safely and confirm its final status.

Transfers are never retried automatically. If a call fails in a way that
leaves the outcome unknown (timeout, connection reset, 5xx), look the transfer
up by its merchantTxRef before you try again, and reuse the same reference if
you do retry so Nomba can reject the duplicate.
"""

from __future__ import annotations

import time
import uuid

from nomba import APIConnectionError, Nomba, ServerError, TransactionStatus, ValidationError

FINAL = {TransactionStatus.SUCCESS, TransactionStatus.REFUND, TransactionStatus.CANCELLED}


def pay(nomba: Nomba, account_number: str, bank_code: str, amount: float) -> str:
    lookup = nomba.transfers.lookup_account(account_number=account_number, bank_code=bank_code)
    reference = f"payout-{uuid.uuid4()}"  # store this with your payout record first

    try:
        result = nomba.transfers.to_bank(
            {
                "amount": amount,
                "accountNumber": account_number,
                "accountName": lookup.get("accountName", ""),
                "bankCode": bank_code,
                "merchantTxRef": reference,
                "narration": "Invoice 1042",
            }
        )
        status = result["status"]
    except ValidationError:
        raise  # the request was wrong; nothing was sent to the bank
    except (APIConnectionError, ServerError):
        status = TransactionStatus.PENDING_BILLING.value  # unknown: find out below

    # Poll until the status is final. In production, prefer the payout_* webhooks.
    for _ in range(10):
        if status in FINAL:
            break
        time.sleep(3)
        try:
            status = nomba.transactions.get(merchant_tx_ref=reference)["status"]
        except APIConnectionError:
            continue
    return status


if __name__ == "__main__":
    with Nomba() as client:
        print(pay(client, "0123456789", "058", 100.0))
