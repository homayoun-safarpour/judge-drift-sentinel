# Publish `judge-drift-sentinel` to PyPI

**Status (2026-08-05):** **DONE.** `judge-drift-sentinel==0.1.0` is on
[PyPI](https://pypi.org/project/judge-drift-sentinel/). Verified with
`pip install judge-drift-sentinel==0.1.0`.

Never commit tokens, `.pypirc`, or CI secrets into this repo.

## Install (users)

```bash
pip install judge-drift-sentinel
```

## Re-publish a new version (maintainer)

1. Bump version in `pyproject.toml`.
2. Build and check:

```powershell
cd D:\ship\judge-drift-sentinel
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

3. Upload (token stays in your shell only):

```powershell
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-..."   # paste API token; do not commit
python -m twine upload dist/*
```

4. Tag / GitHub Release to match the version.
5. Confirm: `pip index versions judge-drift-sentinel`

## Notes

- Import name: `driftsentinel`
- CLI: `drift-sentinel`
- CI must not upload to PyPI without an explicit Trusted Publisher or secret approved by Homayoun.
