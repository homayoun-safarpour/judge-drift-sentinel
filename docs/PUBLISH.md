# Publish `judge-drift-sentinel` to PyPI

**Status (2026-08-04):** packaging is ready (`python -m build` + `twine check` PASS).
Upload is **blocked until Boss Homayoun** provides a PyPI API token in the shell
environment. Agents must **not** claim `pip install judge-drift-sentinel` works
until PyPI returns success for the upload.

Never commit tokens, `.pypirc`, or CI secrets into this repo.

## One-time setup (Boss)

1. Create a PyPI account at https://pypi.org (Trusted Publisher optional later).
2. Create an API token: Account settings → API tokens → Add API token
   (scope: project `judge-drift-sentinel` after first upload, or entire account for first publish).
3. Do **not** paste the token into git, issues, or chat logs that get committed.

## Publish commands (Boss shell — PowerShell)

From the repo root on a clean `main` after the packaging commit:

```powershell
cd D:\ship\judge-drift-sentinel

python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*

# Token auth (PyPI): username is literally __token__
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-AgEIcHlwaS5vcmc..."   # paste API token; do not commit

python -m twine upload dist/*
```

Equivalent with `UV_PUBLISH_TOKEN` / `PYPI_TOKEN` if you prefer uv:

```powershell
$env:UV_PUBLISH_TOKEN = "pypi-AgEIcHlwaS5vcmc..."
uv publish
```

TestPyPI dry-run (optional, recommended once):

```powershell
python -m twine upload --repository testpypi dist/*
# then: pip install -i https://test.pypi.org/simple/ judge-drift-sentinel
```

## Verify after upload (only then claim pip install)

```powershell
pip index versions judge-drift-sentinel
pip install judge-drift-sentinel==0.1.0
drift-sentinel --help
python -c "import driftsentinel; print(driftsentinel.__version__)"
```

Expected: import package name `driftsentinel`, PyPI project name `judge-drift-sentinel`,
CLI `drift-sentinel`, version `0.1.0`.

## After a successful upload

1. Mark W8 `[x]` in `LOOP_STATE.md` with `(touched: YYYY-MM-DD)`.
2. Update README Install to lead with `pip install judge-drift-sentinel`.
3. Append Build Log + close Week-1 DoD if all W1–W8 are done.

## CI note (dry-run only — no auto-publish)

CI must **not** upload to PyPI without an explicit Boss-approved Trusted Publisher
or a secret that Boss installs in GitHub Actions. Until then:

- Local/CI may run `python -m build` and `twine check dist/*` (metadata only).
- Do **not** add `twine upload` to `.github/workflows/` with a stored token unless
  Boss explicitly requests Trusted Publisher / OIDC publish.

Optional future workflow job (proposal only): `build` → `twine check` on every
tag `v*`, with upload gated on `environment: pypi` + Trusted Publisher.
