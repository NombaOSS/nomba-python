"""Page through every transaction in a date range."""

from __future__ import annotations

from nomba import Nomba


def main() -> None:
    with Nomba() as nomba:
        # One page at a time:
        page = nomba.transactions.list(limit=50, date_from="2026-01-01T00:00:00Z")
        print(len(page.get("results", [])), "on the first page; next cursor:", page.get("cursor"))

        # Or let the SDK follow the cursors:
        total = 0.0
        for txn in nomba.transactions.list_all(limit=50, date_from="2026-01-01T00:00:00Z"):
            if txn["status"] == "SUCCESS":
                total += float(txn["amount"])
        print("Total successful:", total)


if __name__ == "__main__":
    main()
