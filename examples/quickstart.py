"""Quickstart: check your balance and list banks in the sandbox.

export NOMBA_CLIENT_ID=... NOMBA_CLIENT_SECRET=... NOMBA_ACCOUNT_ID=...
python examples/quickstart.py
"""

from __future__ import annotations

from nomba import Nomba


def main() -> None:
    with Nomba() as nomba:  # sandbox unless NOMBA_ENVIRONMENT=production
        balance = nomba.accounts.get_balance()
        print(f"Balance: {balance['amount']} {balance['currency']}")

        banks = nomba.transfers.list_banks()
        print(f"{len(banks)} banks, e.g. {banks[0].get('name') if banks else 'none'}")


if __name__ == "__main__":
    main()
