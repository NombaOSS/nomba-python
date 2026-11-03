from __future__ import annotations

import httpx

from .conftest import MockAPI, envelope, make_async_client, make_client


def paged(pages: dict[str | None, dict[str, object]]) -> object:
    def handler(request: httpx.Request) -> httpx.Response:
        return envelope(pages[request.url.params.get("cursor")])

    return handler


PAGES: dict[str | None, dict[str, object]] = {
    None: {"results": [{"id": "1"}, {"id": "2"}], "cursor": "c2"},
    "c2": {"results": [{"id": "3"}], "cursor": "c3"},
    "c3": {"results": [{"id": "4"}], "cursor": ""},
}


def test_list_all_follows_cursors(api: MockAPI) -> None:
    api.add("GET", "/v1/transactions/accounts", paged(PAGES))  # type: ignore[arg-type]
    with make_client(api) as client:
        ids = [t["id"] for t in client.transactions.list_all(limit=2, date_from="2026-01-01")]
    assert ids == ["1", "2", "3", "4"]
    calls = api.api_requests()
    assert [r.url.params.get("cursor") for r in calls] == [None, "c2", "c3"]
    assert all(r.url.params["limit"] == "2" and r.url.params["dateFrom"] == "2026-01-01" for r in calls)


def test_list_all_is_lazy(api: MockAPI) -> None:
    api.add("GET", "/v1/transactions/accounts", paged(PAGES))  # type: ignore[arg-type]
    with make_client(api) as client:
        iterator = client.transactions.list_all()
        assert api.requests == []
        assert next(iterator)["id"] == "1"
    assert len(api.api_requests()) == 1


def test_stops_on_absent_or_repeated_cursor(api: MockAPI) -> None:
    api.add(
        "POST",
        "/v1/accounts/virtual/list",
        envelope({"results": [{"accountRef": "a"}], "cursor": "same"}),
        envelope({"results": [{"accountRef": "b"}], "cursor": "same"}),
    )
    api.add("GET", "/v1/accounts/terminals", envelope({"results": [{"terminalId": "t"}]}))
    api.add("GET", "/v1/transactions/bank", envelope(None))
    with make_client(api) as client:
        assert [v["accountRef"] for v in client.virtual_accounts.list_all({"expired": False})] == ["a", "b"]
        assert [t["terminalId"] for t in client.accounts.list_all_terminals()] == ["t"]
        assert list(client.transactions.list_all_bank_transactions()) == []


def test_filter_all_and_sub_account_terminals(api: MockAPI) -> None:
    api.add("POST", "/v1/transactions/accounts/sub-1", paged(PAGES))  # type: ignore[arg-type]
    api.add("GET", "/v1/accounts/sub-1/terminals", envelope({"results": [{"terminalId": "x"}], "cursor": None}))
    with make_client(api) as client:
        assert len(list(client.transactions.filter_all({"status": "SUCCESS"}, sub_account_id="sub-1"))) == 4
        assert len(list(client.accounts.list_all_terminals(sub_account_id="sub-1", serial_number="S"))) == 1


async def test_async_list_all(api: MockAPI) -> None:
    api.add("GET", "/v1/transactions/accounts", paged(PAGES))  # type: ignore[arg-type]
    api.add("POST", "/v1/transactions/accounts", paged(PAGES))  # type: ignore[arg-type]
    api.add("GET", "/v1/transactions/bank", paged(PAGES))  # type: ignore[arg-type]
    api.add("GET", "/v1/accounts/terminals", paged(PAGES))  # type: ignore[arg-type]
    api.add("POST", "/v1/accounts/virtual/list", paged(PAGES))  # type: ignore[arg-type]
    async with make_async_client(api) as client:
        assert [t["id"] async for t in client.transactions.list_all()] == ["1", "2", "3", "4"]
        assert len([t async for t in client.transactions.filter_all({"source": "api"})]) == 4
        assert len([t async for t in client.transactions.list_all_bank_transactions(limit=50)]) == 4
        assert len([t async for t in client.accounts.list_all_terminals()]) == 4
        assert len([v async for v in client.virtual_accounts.list_all()]) == 4
