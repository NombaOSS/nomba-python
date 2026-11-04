# Changelog

## [Unreleased]

### Documentation

- Webhook docs and examples no longer recommend a timestamp tolerance (previously 300 s): Nomba doesn't document whether retries get a fresh `nomba-timestamp`, so a tolerance could reject legitimate retries. Deduplicate on `requestId` instead. The docs also note that the amount, `orderReference`, `merchantTxRef` and `tokenKey` aren't signed, so money decisions should be confirmed with `transactions.get`.

## [0.1.1] - 2026-11-03

First release on PyPI. Version 0.1.0 was never published: PyPI had already used that filename for an earlier, deleted `nomba` project, and filenames can't be reused.

### Added

- `Nomba` (sync) and `AsyncNomba` (async) clients with the same resources: `auth`, `accounts`, `virtual_accounts`, `checkout`, `transfers`, `transactions`, `terminals`, `direct_debits`, `bills`, `global_payout`, `global_collection`, `webhooks`.
- Configuration from arguments or `NOMBA_*` environment variables, sandbox by default.
- Automatic access tokens: issued on first use, refreshed before expiry, shared between concurrent calls, retried once on a 401. Pluggable token store.
- Error classes for each HTTP status, plus connection and timeout errors.
- Automatic retries for GET requests and token calls only.
- `timeout` bounds the whole attempt, including reading the response body, not just each connection phase.
- Generated `merchantTxRef` (and `orderReference` for saved-card charges) when you don't pass one, returned in the result and attached to any error the call raises as `err.reference`.
- Path parameter validation and encoding.
- Cursor pagination helpers (`*_all`).
- Webhook signature verification with an exact constant-time compare, usable without a client (`nomba.webhooks.verify_signature`), with optional timestamp tolerance. Rejects non-RFC 3339 timestamps and `responseCode` values containing `:`, which would make the signed fields ambiguous.
- `TypedDict` types for params and responses; `TransactionStatus` and `WebhookEventType` enums.
