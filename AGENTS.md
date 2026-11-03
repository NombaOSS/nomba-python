# nomba-python

Official Python SDK for the Nomba API (`pip install nomba`, `from nomba import Nomba, AsyncNomba`). Hand-written, src layout, only runtime dependency is httpx. Request logic lives once in `src/nomba/_core.py` as I/O-free generators; `_client.py` drives them sync and async. Resources in `src/nomba/resources/` hold shared request builders plus a sync and an async class with identical surfaces.

## Rules
- Conventional commits; main squash-merges, so the PR title becomes the commit. Stage files by name.
- Never push to main. Branch and open a PR. Merge only when Sam says so.
- No AI attribution in commits, PRs or code comments.
- Public repo: don't name private Nomba repos.
- Method names match the Node and PHP SDKs (snake_case here). Don't rename without changing all three.

## Safety invariants
- Only GET and token issue/refresh are retried automatically (`Request.retryable`). Never auto-retry POST/PUT/DELETE: money could move twice. The single 401 refresh-and-retry is the only exception.
- Never log, `repr()` or put in an exception message the client secret, access/refresh tokens or the Authorization header. Error messages carry method and path only (no query, no headers).
- Path parameters go through `_core.path()` or `_core.sub_account_path()` (`{sub}` templates): validated (no empty, `.`, `..`, `/`) and URL-encoded.
- Retry, 401 and auth behaviour are fields on `_core.Request` (`retryable` defaults to GET-only); token calls are ordinary `Request`s with `auth_endpoint=True`, whose error bodies drop `data`.
- Money-moving calls (`transfers.to_bank/to_wallet`, `bills.*` purchases) generate a UUID v4 `merchantTxRef` if missing and return it; `checkout.charge_saved_card` does the same for `order.orderReference`.
- Money-moving calls set `Request.reference`; `api_flow` adds it to the result and to every `NombaError` the call raises (`err.reference`). Don't bypass `api_flow`.
- `timeout` is a total per-attempt deadline: the drivers stream the body through `_core.BodyReader`, which checks the deadline after the headers and after each chunk, on top of httpx's per-phase timeouts.
- Webhook verification uses an exact `hmac.compare_digest` (no case folding) on the raw body; never verify a re-serialised object.
- The signed webhook message joins fields with `:`: keep the strict RFC 3339 check on `nomba-timestamp` and the no-`:` check on `responseCode`, or field boundaries become ambiguous.
- Tests mock HTTP with `httpx.MockTransport`; never call Nomba from tests.
- Every new sync method needs its async twin and a case in `tests/test_resources.py`.

## Releasing
Never create tags, Releases or PyPI uploads by hand; see `RELEASING.md`.

## Before pushing
`.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy && .venv/bin/pytest --cov --cov-fail-under=90`
