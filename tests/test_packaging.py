"""Named claim: README `pip install -e ".[dev]"` has a real extras table."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
README = ROOT / "README.md"


def test_pyproject_declares_dev_optional_dependencies_for_readme_claim() -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    assert "[project.optional-dependencies]" in text
    match = re.search(
        r"\[project\.optional-dependencies\]\s*\ndev\s*=\s*\[([^\]]+)\]",
        text,
    )
    assert match is not None, 'missing [project.optional-dependencies] dev = [...]'
    extras = match.group(1)
    assert "pytest" in extras
    assert "ruff" in extras


def test_readme_documents_editable_dev_install() -> None:
    text = README.read_text(encoding="utf-8")
    assert 'pip install -e ".[dev]"' in text
