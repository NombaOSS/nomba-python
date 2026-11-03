# Security

## Reporting a vulnerability

Email **security@nomba.com** with a description, the affected version and steps to reproduce. Please don't open a public issue for security problems. We aim to acknowledge reports within three working days.

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x (latest) | Yes |
| older | No |

Security fixes are released as a new patch version. Upgrade with `pip install --upgrade nomba`.

## What the SDK does to protect you

- Never auto-retries POST, PUT or DELETE requests, so money is not moved twice.
- Keeps secrets out of logs, `repr()` and exception messages.
- Validates and encodes path parameters.
- Verifies webhook signatures in constant time.
- Defaults to the sandbox; production must be chosen explicitly.
