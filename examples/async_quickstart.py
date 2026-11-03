"""The same calls with AsyncNomba."""

from __future__ import annotations

import asyncio

from nomba import AsyncNomba


async def main() -> None:
    async with AsyncNomba() as nomba:
        balance, parent = await asyncio.gather(nomba.accounts.get_balance(), nomba.accounts.get_parent())
        print(parent["accountName"], balance["amount"], balance["currency"])


if __name__ == "__main__":
    asyncio.run(main())
