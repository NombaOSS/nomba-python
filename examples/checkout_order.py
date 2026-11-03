"""Create a hosted checkout order, then charge the saved card later."""

from __future__ import annotations

import uuid

from nomba import Nomba


def main() -> None:
    with Nomba() as nomba:
        order = nomba.checkout.create_order(
            {
                "order": {
                    "orderReference": f"order-{uuid.uuid4()}",
                    "callbackUrl": "https://merchant.example.com/checkout/done",
                    "customerEmail": "ada@example.com",
                    "amount": "5000.00",
                    "currency": "NGN",
                },
                "tokenizeCard": True,
            }
        )
        print("Send the customer to:", order["checkoutLink"])

        # Later, with the tokenKey from the payment_success webhook:
        charge = nomba.checkout.charge_saved_card(
            {
                "tokenKey": "token-from-webhook",
                "order": {"customerEmail": "ada@example.com", "amount": "5000.00", "currency": "NGN"},
            }
        )
        # orderReference was generated for you; keep it to submit an OTP or verify.
        print(charge["orderReference"], charge.get("status"), charge.get("otpRequired"))


if __name__ == "__main__":
    main()
