# Releasing

Publishing is automated; you never run `twine upload` or create tags by hand.

## Steps

1. Merge your PRs to `main`. Main squash-merges, so each PR title must be a valid Conventional Commit.
2. Open a `chore: release X.Y.Z` PR that bumps `version` in `pyproject.toml` and `__version__` in `src/nomba/_version.py` (a test checks they match), and renames `## [Unreleased]` in `CHANGELOG.md` to `## [X.Y.Z] - YYYY-MM-DD` (Breaking, Security, Added, Fixed, Changed, in plain language).
3. Merge it. `publish.yml` builds it (lint, type-check, test, build, `twine check`, install-and-import smoke), then waits. Open the run in **Actions** and approve the **pypi** deployment. Only then does it publish to PyPI with Trusted Publishing and create the `vX.Y.Z` tag and GitHub Release.

Ordinary merges are no-ops: the workflow skips versions already on PyPI.

## Choosing the version

| Change since the last release | Bump |
|-------------------------------|------|
| `feat!:` or a `BREAKING CHANGE:` footer | major |
| `feat:` | minor |
| `fix:` / `perf:` | patch |
| only `chore:` `docs:` `refactor:` `test:` `ci:` | no release |

Before 1.0.0, breaking changes bump the minor version.

## After publishing

Check the registry directly:

```bash
curl -s https://pypi.org/pypi/nomba/json | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["info"]["version"], d["info"]["requires_dist"])'
```

Then confirm the tag and GitHub Release exist, and in a fresh virtualenv run `pip install nomba && python -c "import nomba; print(nomba.__version__)"`.

## One-time setup (repo owner)

- GitHub: create an environment named `pypi` with yourself as required reviewer, limited to protected branches, so a stolen login can't publish on its own.
- PyPI: add a Trusted Publisher for the `nomba` project pointing at repo `NombaOSS/nomba-python`, workflow `publish.yml`, environment `pypi`. No PyPI token is stored anywhere. For the very first release, add it as a "pending publisher" (PyPI allows this before the project exists), so the first upload also goes through the workflow.
